from __future__ import annotations

import logging
import logging.config
import traceback
from pathlib import Path
from typing import Any, Awaitable, Callable, TypeAlias

from jinja2 import ChoiceLoader, Environment, FileSystemLoader, Template, select_autoescape
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.staticfiles import StaticFiles

logger: logging.Logger = logging.getLogger("uvicorn.error")


METHOD_NOT_ALLOWED_MESSAGE: str = "Method Not Allowed"

HandlerType: TypeAlias = Callable[[Request], Awaitable[PlainTextResponse]]


class BaseView:
    """Base view class that dispatches requests based on HTTP methods."""

    def __init__(self, *, debug: bool = False, app: Sunbreeze) -> None:
        """Initializes the BaseView class.

        In debug mode, detailed error messages are returned in responses.

        Args:
            debug (bool, optional): Enable debug mode. Defaults to False.
            app (Sunbreeze): The Sunbreeze application instance.
        """
        self.debug: bool = debug
        self.templates: Environment = app.templates

    async def dispatch(self, request: Request) -> PlainTextResponse:
        """Dispatches the request to the appropriate HTTP method handler."""
        method: str = request.method.lower()

        if hasattr(self, method):
            handler: HandlerType = getattr(self, method)
            return await handler(request)

        return PlainTextResponse(content=METHOD_NOT_ALLOWED_MESSAGE, status_code=405)

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        """Handles ASGI calls and dispatches requests."""
        request = Request(scope=scope, receive=receive)
        try:
            response: PlainTextResponse = await self.dispatch(request=request)
        except (KeyboardInterrupt, SystemExit):
            logger.exception("Application stopped by user.")
            raise
        except Exception:  # noqa: BLE001
            if self.debug:
                traceback_info: str = traceback.format_exc()
                template: Template = self.templates.get_template(name="error.html")
                content: str = template.render(traceback=traceback_info, request=request)
                response = PlainTextResponse(content=content, status_code=500, media_type="text/html")
            else:
                response = PlainTextResponse(content="Something ducky happened.", status_code=500)

        await response(scope, receive, send)


class Sunbreeze:
    """Sunbreeze application class.

    Attributes:
        routes (list[Route]): The routes to register with the application.
        templates (Environment): The Jinja2 environment for template rendering.
    """

    def __init__(  # noqa: PLR0913
        self,
        *,
        debug: bool = False,
        log_level: str = "INFO",
        name: str | None = "Sunbreeze",
        static_dir: Path = Path("static"),
        template_dir: Path = Path("templates"),
        version: str | None = "0.1.0",
    ) -> None:
        """Initializes the Sunbreeze application.

        Args:
            debug (bool, optional): Enable debug mode. Enables tracebacks on errors, hot-reloading, and more verbose logging.
            log_level (str, optional): The log level to use. Defaults to "INFO".
            name (str | None, optional): The application name.
            static_dir (Path, optional): The directory where static files are stored. Defaults to "static".
            template_dir (Path, optional): The directory where Jinja2 templates are stored. Defaults to "templates".
            version (str | None, optional): The application version.
        """  # noqa: E501
        self.debug: bool = debug
        self.log_level: str = log_level
        self.name: str | None = name
        self.version: str | None = version

        # Set up logging
        logging.basicConfig(level=self.log_level)

        # Create the Starlette application instance.
        self.app = Starlette(debug=self.debug)
        self.routes: list[Route] = []  # Store routes to register them later

        # Initialize the template environment and set up static files
        self._initialize_template_environment(template_dir=template_dir)
        self._setup_static(static_dir=static_dir)

        logger.info("Sunbreeze application initialized: %s v%s", self.name, self.version)

    def _setup_static(self, static_dir: Path) -> None:
        """Set up the static files directory.

        Directory is created if it does not exist.

        Args:
            static_dir (Path): The directory where static files are stored.
        """
        static_dir.mkdir(parents=True, exist_ok=True)
        self.app.mount("/static", StaticFiles(directory=static_dir), name="static")

    def _initialize_template_environment(self, template_dir: Path) -> None:
        """Initialize the Jinja2 template environment.

        Directory is created if it does not exist.

        Args:
            template_dir (Path): The directory where Jinja2 templates are stored.
        """
        internal_template_dir: Path = Path(__file__).parent / "templates"
        template_dir.mkdir(parents=True, exist_ok=True)

        loader = ChoiceLoader(
            loaders=[
                FileSystemLoader(searchpath=template_dir),  # User templates
                FileSystemLoader(searchpath=internal_template_dir),  # Internal templates
            ]
        )

        self.templates = Environment(
            loader=loader,
            autoescape=select_autoescape(enabled_extensions=["html"]),
        )

    def __call__(self) -> Starlette:
        """Returns the Starlette application instance."""
        return self.app

    def view(
        self,
        path: str,
        name: str | None = None,
        methods: list[str] | None = None,
    ) -> Callable[[Callable], Callable]:
        """Decorator to register a view with a given route."""
        # Default to GET and HEAD methods
        if methods is None:
            logger.debug("No methods provided, defaulting to GET and HEAD.")
            methods = ["GET", "HEAD"]

        def decorator(cls: Callable) -> Callable:
            """Attach route metadata to the class and register it.

            Args:
                cls (Callable): The view class to register

            Returns:
                Callable: The view class
            """
            instance: BaseView = cls(debug=self.debug, app=self)
            route = Route(path=path, endpoint=instance, methods=methods, name=name)
            self.app.router.routes.append(route)  # Register the route immediately

            logger.info("View registered: %s at %s", cls.__name__, path)

            return cls

        return decorator

    def add_route(self, path: str, route: BaseView) -> None:
        """Add a route to the application.

        This is used when testing. You should probably use @app.view instead.

        Args:
            path (str): The route path.
            route (BaseView): The route handler.
        """
        self.app.router.routes.append(Route(path=path, endpoint=route))

        logger.info("Route added: %s at %s", route.__class__.__name__, path)
