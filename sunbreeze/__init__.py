from __future__ import annotations

import logging
import logging.config
import traceback
from typing import Awaitable, Callable, TypeAlias

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route

logger: logging.Logger = logging.getLogger("uvicorn.error")


METHOD_NOT_ALLOWED_MESSAGE: str = "Method Not Allowed"

HandlerType: TypeAlias = Callable[[Request], Awaitable[PlainTextResponse]]


class BaseView:
    """Base view class that dispatches requests based on HTTP methods."""

    def __init__(self, *, debug: bool = False) -> None:
        """Initializes the BaseView class.

        In debug mode, detailed error messages are returned in responses.

        Args:
            debug (bool, optional): Enable debug mode. Defaults to False.
        """
        self.debug: bool = debug

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
        except Exception as e:
            if self.debug:
                # Return detailed error message in debug mode
                error_message: str = f"An error occurred: {e!s}\nTraceback:\n{traceback.format_exc()}"
                response = PlainTextResponse(content=error_message, status_code=500)
                logger.exception("An error occurred.")
            else:
                # Return a generic error message in production
                response = PlainTextResponse(content="Something ducky happened.", status_code=500)
                logger.exception("An error occurred.")

        await response(scope, receive, send)


class Sunbreeze:
    """Sunbreeze application class.

    Attributes:
        routes (list[Route]): The routes to register with the application.
    """

    def __init__(
        self,
        *,
        debug: bool = False,
        log_level: str = "INFO",
        name: str | None = "Sunbreeze",
        version: str | None = "0.1.0",
    ) -> None:
        """Initializes the Sunbreeze application.

        Args:
            debug (bool, optional): Enable debug mode. Enables tracebacks on errors, hot-reloading, and more verbose logging.
            log_level (str, optional): The log level to use. Defaults to "INFO".
                If LOGURU_LEVEL is set, it will override this value.
            name (str | None, optional): The application name.
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

        logger.info("Sunbreeze application initialized: %s v%s", self.name, self.version)

    def __call__(self) -> Starlette:
        """Returns the Starlette application instance.

        Returns:
            Starlette: The Starlette application instance.
        """
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
            # Instantiate the view class so it can handle requests
            instance: BaseView = cls(debug=self.debug)
            route = Route(path=path, endpoint=instance, methods=methods, name=name)
            self.app.router.routes.append(route)  # Register the route immediately

            logger.info("View registered: %s at %s", cls.__name__, path)

            return cls

        return decorator

    def add_route(self, path: str, route: BaseView) -> None:
        """Add a route to the application.

        Args:
            path (str): The route path.
            route (BaseView): The route handler.
        """
        self.app.router.routes.append(Route(path=path, endpoint=route))

        logger.info("Route added: %s at %s", route.__class__.__name__, path)
