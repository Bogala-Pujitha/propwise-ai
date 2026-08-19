import pytest


PROTECTED_GETS = [
    "/dashboard",
    "/comparables",
    "/what-if",
    "/market-intelligence",
    "/map",
    "/model-performance",
    "/experiments",
    "/admin",
]


@pytest.fixture()
def client():
    from backend import app
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SECRET_KEY="test-secret-key",
    )
    with app.test_client() as client:
        yield client


@pytest.mark.parametrize("route", PROTECTED_GETS)
def test_unauthenticated_routes_are_not_public(client, route):
    response = client.get(route, follow_redirects=False)
    assert response.status_code in (302, 401, 403)
