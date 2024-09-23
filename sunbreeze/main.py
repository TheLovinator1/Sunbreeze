from starlette.requests import Request
from starlette.responses import PlainTextResponse

from sunbreeze import BaseView, Sunbreeze

# Create an instance of Sunbreeze
app = Sunbreeze(
    debug=True,
    log_level="DEBUG",
    name="Sunbreeze Example",
    version="0.2.0",
)


@app.view("/", methods=["GET"])
class ExampleView(BaseView):
    """Example view class for Sunbreeze."""

    async def get(self, request: Request) -> PlainTextResponse:
        """GET method handler."""
        # Raise an exception to demonstrate the debug mode
        msg = "An error occurred."
        raise Exception(msg)  # noqa: TRY002

        return PlainTextResponse(f"Welcome to the Home Page, this is your request: {request}")
