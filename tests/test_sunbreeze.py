from typing import TYPE_CHECKING

from httpx._models import Response
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.testclient import TestClient

from sunbreeze import METHOD_NOT_ALLOWED_MESSAGE, BaseView, Sunbreeze

if TYPE_CHECKING:
    from httpx import Response


class SimpleView(BaseView):
    """A simple test view to validate HTTP method handling."""

    async def get(self, request: Request) -> PlainTextResponse:
        return PlainTextResponse(content="GET response")

    async def post(self, request: Request) -> PlainTextResponse:
        return PlainTextResponse(content="POST response")


def test_baseview_get() -> None:
    sunbreeze = Sunbreeze()
    sunbreeze.add_route(path="/", route=SimpleView())

    client = TestClient(app=sunbreeze.app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.text == "GET response"


def test_baseview_post() -> None:
    """Test that the POST method dispatches correctly."""
    sunbreeze = Sunbreeze()
    sunbreeze.add_route(path="/", route=SimpleView())

    client = TestClient(app=sunbreeze.app)
    response: Response = client.post("/")
    assert response.status_code == 200
    assert response.text == "POST response"


def test_baseview_method_not_allowed() -> None:
    """Test that an unsupported method returns 405."""
    sunbreeze = Sunbreeze()
    sunbreeze.add_route(path="/", route=SimpleView())

    client = TestClient(app=sunbreeze.app)
    response: Response = client.put("/")
    assert response.status_code == 405
    assert response.text == METHOD_NOT_ALLOWED_MESSAGE


# Test Sunbreeze Application
def test_sunbreeze_view_registration() -> None:
    """Test that views are correctly registered with the Sunbreeze app."""
    app = Sunbreeze()

    @app.view(path="/", methods=["GET", "POST"])
    class IndexView(BaseView):
        async def get(self, request: Request) -> PlainTextResponse:
            return PlainTextResponse(content="Hello, World!")

        async def post(self, request: Request) -> PlainTextResponse:
            return PlainTextResponse(content="Posted!")

    client = TestClient(app=app())
    get_response: Response = client.get(url="/")
    post_response: Response = client.post(url="/")

    assert get_response.status_code == 200
    assert get_response.text == "Hello, World!"
    assert post_response.status_code == 200
    assert post_response.text == "Posted!"


def test_sunbreeze_debug_mode() -> None:
    """Test that debug mode is correctly applied and traceback is sent on error."""
    app = Sunbreeze(debug=True)

    @app.view(path="/error")
    class ErrorView(BaseView):
        async def get(self, request: Request) -> PlainTextResponse:
            msg = "Intentional error for testing"
            raise RuntimeError(msg)

    client = TestClient(app=app())
    response: Response = client.get(url="/error")

    assert response.status_code == 500
    assert "Intentional error for testing" in response.text  # Check if the error message is present
    assert "Traceback" in response.text  # Ensure traceback is included


def test_sunbreeze_production_mode() -> None:
    """Test that production mode is correctly applied and generic error message is sent on error."""
    app = Sunbreeze(debug=False)

    @app.view(path="/error")
    class ErrorView(BaseView):
        async def get(self, request: Request) -> PlainTextResponse:
            msg = "Intentional error for testing"
            raise RuntimeError(msg)

    client = TestClient(app=app())
    response: Response = client.get(url="/error")

    assert response.status_code == 500
    assert "Something ducky happened." in response.text  # Check if the generic error message is present
    assert "Traceback" not in response.text  # Ensure traceback is not included
