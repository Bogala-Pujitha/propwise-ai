import pytest


def _app():
    from app import app
    return app


@pytest.fixture()
def client():
    application = _app()
    application.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SECRET_KEY="test-secret-key",
    )
    with application.test_client() as client:
        yield client


def test_admin_endpoint_is_protected(client):
    response = client.get("/admin", follow_redirects=False)
    assert response.status_code in (302, 401, 403)


def test_bulk_valuation_is_protected(client):
    response = client.get("/bulk-valuation", follow_redirects=False)
    assert response.status_code in (302, 401, 403)
