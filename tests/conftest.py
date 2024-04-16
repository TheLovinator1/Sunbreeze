import pytest
from httpx import Client

from sunbreeze.wsgi import Sunbreeze


@pytest.fixture()
def api() -> Sunbreeze:
    """So we can use @api.route in our tests."""
    return Sunbreeze()


@pytest.fixture()
def client(api: Sunbreeze) -> Client:
    """Create a test session for the API.

    Args:
        api: The API instance.

    Returns:
        An httpx.Client instance.
    """
    return api.test_session()
