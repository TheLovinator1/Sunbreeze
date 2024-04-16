import os

import httpx
import pytest
from webob import Request, Response

from sunbreeze.wsgi import Sunbreeze


def test_basic_route(api: Sunbreeze, client: httpx.Client) -> None:
    """Test a basic route.

    Args:
        api: The API instance.
        client: The httpx.Client instance.
    """
    random_string: str = os.urandom(8).hex()

    @api.route("/home")
    def home(request: Request, response: Response) -> None:  # type: ignore  # noqa: PGH003
        response.text = random_string

    response: httpx.Response = client.get("/home")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert (
        response.text == random_string
    ), f"Expected {random_string}, got {response.text}"

    # Add a second route with the same path to see if it raises an error.
    with pytest.raises(AssertionError):

        @api.route("/home")
        def home2(request: Request, response: Response) -> None:  # type: ignore  # noqa: PGH003
            response.text = "Hello, World!"


def test_parameterized_route(api: Sunbreeze, client: httpx.Client) -> None:
    @api.route("/{name}")
    def hello(request: Request, response: Response, name: str) -> None:  # type: ignore  # noqa: PGH003
        response.text = f"Hello {name}"

    assert (
        client.get("http://testserver/first").text == "Hello first"
    ), f"Expected 'Hello first', got {client.get('http://testserver/first').text}"
    assert (
        client.get("http://testserver/second").text == "Hello second"
    ), f"Expected 'Hello second', got {client.get('http://testserver/second').text}"


def test_default_404_response(client: httpx.Client) -> None:
    response: httpx.Response = client.get("http://testserver/doesnotexist")

    assert response.status_code == 404
    assert response.text == "Not Found"


def test_alternative_route(api: Sunbreeze, client: httpx.Client) -> None:
    response_text = "Alternative way to add a route"

    def home(request: Request, response: Response) -> None:
        response.text = response_text

    api.add_route("/alternative", home)

    assert client.get("http://testserver/alternative").text == response_text
