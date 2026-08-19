"""High-value authenticated user journey smoke tests."""

import pytest

from backend import app, db, User, bcrypt


@pytest.fixture
def client():
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.rollback()


def _create_user():
    username = "journey_user"
    user = User.query.filter_by(username=username).first()
    if user:
        return user

    user = User(
        username=username,
        email="journey@example.com",
        password_hash=bcrypt.generate_password_hash("StrongPass123").decode("utf-8"),
        role="user",
    )
    db.session.add(user)
    db.session.commit()
    return user


def test_user_journey(client):
    _create_user()

    login = client.post(
        "/api/auth/login",
        json={"username": "journey_user", "password": "StrongPass123"},
    )
    assert login.status_code == 200

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.get_json()["role"] == "user"

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200

    history = client.get("/api/user/history")
    assert history.status_code == 200

    event = client.post(
        "/api/behavior/track",
        json={
            "event_type": "location_view",
            "payload": {
                "city": "Hyderabad",
                "locality": "Gachibowli",
            },
        },
    )
    assert event.status_code == 200

    logout = client.post("/api/auth/logout")
    assert logout.status_code == 200
