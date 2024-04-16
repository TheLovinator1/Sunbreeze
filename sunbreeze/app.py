"""Sunbreeze application module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from sunbreeze.wsgi import Sunbreeze

if TYPE_CHECKING:
    from webob import Request, Response

app = Sunbreeze()


@app.route("/home")
def home(request: Request, response: Response) -> None:
    """/home route handler.

    Args:
        request: The request object.
        response: The response object.
    """
    response.text = "Hello, World!"


@app.route("/about")
def about(request: Request, response: Response) -> None:
    """About Sunbreeze route handler.

    Args:
        request: The request object.
        response: The response object.
    """
    response.text = "About Sunbreeze"


@app.route("/hello/{name}")
def greeting(request: Request, response: Response, name: str) -> None:
    """Greeting route handler.

    Args:
        request: The request object.
        response: The response object.
        name: The name to greet.
    """
    response.text = f"Hello, {name}"


@app.route("/book")
class BooksResource:
    """Books resource handler."""

    def get(self: BooksResource, request: Request, response: Response) -> None:
        """GET method handler.

        Args:
            request: The request object.
            response: The response object.
        """
        logger.debug(f"GET {request.path}")
        response.text = "Books Page"


@app.route("/template")
def template_handler(request: Request, response: Response) -> None:
    """Render a template.

    Args:
        request: The request object.
        response: The response object.
    """
    response.body = app.template(
        template_name="index.html",
        context={"name": "TheLovinator", "title": "Sunbreeze"},
    )
