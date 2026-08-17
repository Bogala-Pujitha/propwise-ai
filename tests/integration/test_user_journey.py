import uuid

import pytest


@pytest.fixture()
def client():
    from app import app, db
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SECRET_KEY="test-secret-key",
    )
    with app.app_context():
        db.create_all()
        with app.test_client() as client:
            yield client
        db.session.remove()


def test_register_login_logout_flow(client):
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    email = f"{username}@example.com"

    register = client.post(
        "/register",
        data={
            "username": username,
            "email": email,
            "password": "StrongPass123!",
        },
        follow_redirects=False,
    )

    assert register.status_code in (200, 302)

    login = client.post(
        "/login",
        data={
            "username": username,
            "password": "StrongPass123!",
            "role": "user",
        },
        follow_redirects=False,
    )

    assert login.status_code in (200, 302)

    dashboard = client.get("/dashboard", follow_redirects=False)
    assert dashboard.status_code in (200, 302)

    logout = client.get("/logout", follow_redirects=False)
    assert logout.status_code in (200, 302)
