import pytest

from backend import app, db

try:
    from backend.controllers import register_blueprints
except ImportError:
    register_blueprints = None


@pytest.fixture()
def client():
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    if register_blueprints:
        # Avoid duplicate registration in a repeated pytest process.
        names = {bp.name for bp in getattr(app, "blueprints", {}).values()}
        if "auth_api" not in names:
            register_blueprints(app)
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def test_register_and_login(client):
    response = client.post("/api/auth/register", json={
        "username": "testuser_auth",
        "email": "testuser_auth@example.com",
        "password": "StrongPass1!",
    })
    assert response.status_code == 201

    response = client.post("/api/auth/login", json={
        "username": "testuser_auth",
        "password": "StrongPass1!",
        "role": "user",
    })
    assert response.status_code == 200
    assert response.get_json()["role"] == "user"


def test_duplicate_registration_rejected(client):
    payload = {
        "username": "duplicate_user",
        "email": "duplicate@example.com",
        "password": "StrongPass1!",
    }
    assert client.post("/api/auth/register", json=payload).status_code == 201
    assert client.post("/api/auth/register", json=payload).status_code == 400
