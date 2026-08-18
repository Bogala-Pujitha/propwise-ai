"""Authorization matrix tests for PropWise AI."""

import pytest

from app import app, db, User, bcrypt


@pytest.fixture
def client():
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.rollback()


def _create_user(username, role="user"):
    user = User(
        username=username,
        email=f"{username}@example.com",
        password_hash=bcrypt.generate_password_hash("StrongPass123").decode("utf-8"),
        role=role,
    )
    db.session.add(user)
    db.session.commit()
    return user


def test_anonymous_admin_api_is_denied(client):
    response = client.get("/api/admin/dashboard")
    assert response.status_code == 403


def test_anonymous_admin_ui_is_not_authorized(client):
    response = client.get("/admin")
    assert response.status_code in (302, 401, 403)


def test_normal_user_cannot_access_admin_api(client):
    _create_user("normal")
    response = client.post(
        "/api/auth/login",
        json={"username": "normal", "password": "StrongPass123"},
    )
    assert response.status_code == 200

    response = client.get("/api/admin/dashboard")
    assert response.status_code == 403


def test_admin_can_access_admin_api(client):
    _create_user("admin_user", role="admin")
    response = client.post(
        "/api/auth/login",
        json={"username": "admin_user", "password": "StrongPass123", "role": "admin"},
    )
    assert response.status_code == 200

    response = client.get("/api/admin/dashboard")
    assert response.status_code == 200
