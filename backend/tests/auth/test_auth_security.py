import pytest


def _app():
    from backend import app
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


def test_register_requires_fields(client):
    response = client.post("/register", data={})
    assert response.status_code in (200, 302)


def test_protected_dashboard_requires_auth(client):
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code in (302, 401, 403)


def test_protected_prediction_requires_auth(client):
    response = client.post("/predict", json={"property_type": "Apartment"})
    assert response.status_code in (302, 401, 403)
