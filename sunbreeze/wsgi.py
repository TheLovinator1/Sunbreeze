"""API module for the Sunbreeze API."""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Iterable

import httpx
from jinja2 import Environment, FileSystemLoader, Template, select_autoescape
from loguru import logger
from parse import Result, parse  # type: ignore  # noqa: PGH003
from webob import Request, Response

if TYPE_CHECKING:
    from re import Match
from pathlib import Path


@dataclass
class Sunbreeze:
    """WSGI application for the Sunbreeze API."""

    routes: dict[str, Callable[..., Any]] = field(default_factory=dict)

    templates_dir: Path = Path(__file__).parent.parent / "templates"
    templates_env = Environment(
        autoescape=select_autoescape(),
        loader=FileSystemLoader(searchpath=Path(templates_dir).resolve()),
    )

    def __call__(
        self,
        environ: dict[str, str],
        start_response: Callable[..., Any],
    ) -> Iterable[bytes]:
        """WSGI application interface.

        Args:
            environ: The WSGI environment.
            start_response: The start_response callable.

        Returns:
            An iterable of bytes for the response.
        """
        request = Request(environ)
        logger.info(f"Request: {request.method} {request.path}")
        response: Response = self.handle_request(request)
        return response(environ, start_response)

    def add_route(self, path: str, handler: Callable[..., Any]) -> None:
        """Add a route to the API.

        Args:
            path: The path to match for the route.
            handler: The handler for the route.
        """
        if path in self.routes:
            msg: str = f"Route '{path}' already exists."
            logger.error(msg)
            raise AssertionError(msg)

        self.routes[path] = handler

    def route(self, path: str) -> Callable[..., Any]:
        """Decorator to add a route to the API.

        Args:
            path: The path to match for the route.

        Returns:
            The decorator function.
        """

        def wrapper(handler: Callable[..., Any]) -> Callable[..., Any]:
            self.add_route(path, handler)
            return handler

        return wrapper

    def find_handler(
        self: Sunbreeze,
        request_path: str,
    ) -> tuple[Callable[..., Any], dict[str, str]] | tuple[None, None]:
        """Find a handler for a request path.

        Args:
            self: The API instance.
            request_path: The path of the request.

        Returns:
            A tuple of the handler and named parameters if found, otherwise None.
        """
        for path, handler in self.routes.items():
            parse_result: None | Result | Match = parse(path, request_path)  # type: ignore  # noqa: PGH003
            if isinstance(parse_result, Result):
                return handler, parse_result.named

        return None, None

    def handle_request(self: Sunbreeze, request: Request) -> Response:
        """Handle a request and return a response.

        Args:
            request: The request to handle.

        Returns:
            The response to the request.
        """
        logger.info(f"Request: {request.method} {request.path}")

        response = Response()

        handler: Callable[..., Any] | None
        kwargs: dict[str, str] | None
        handler, kwargs = self.find_handler(request_path=request.path)

        if not kwargs:
            kwargs = {}

        if handler is not None:
            if inspect.isclass(handler):
                handler = getattr(handler(), request.method.lower(), None)
                if handler is None:
                    msg = "Method now allowed"
                    raise AttributeError(msg, request.method)
            handler(request, response, **kwargs)

        else:
            self.default_response(response)

        return response

    def default_response(self: Sunbreeze, response: Response) -> None:
        """Set a default response for a missing route.

        Args:
            response: The response to set.
        """
        response.status_code = 404
        response.text = "Not Found"

    def test_session(
        self: Sunbreeze, base_url: str = "http://testserver"
    ) -> httpx.Client:
        """Create a test session for the API.

        Args:
            self: The API instance.
            base_url: The base URL for the test session. Defaults to "http://testserver".

        Returns:
            An httpx.Client instance.
        """
        return httpx.Client(
            base_url=base_url, app=self, transport=httpx.WSGITransport(app=self)
        )

    def template(
        self: Sunbreeze,
        template_name: str,
        context: dict[str, Any] | None = None,
    ) -> bytes:
        """Render a template with the given context.

        Args:
            self: The API instance.
            template_name: The name of the template to render.
            context: The context to render the template with. Defaults to {}.

        Returns:
            The rendered template as bytes.
        """
        if context is None:
            context = {}
        template: Template = self.templates_env.get_template(template_name)

        return template.render(context).encode("utf-8")
