import pytest


@pytest.fixture()
def app():
    from app import app as flask_app
    flask_app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret-key",
    )
    yield flask_app


def test_password_reset_token_round_trip(app):
    from app import User
    from app.services.password_reset import (
        generate_reset_token,
        verify_reset_token,
    )

    with app.app_context():
        user = User(
            id=123,
            username="reset-test",
            email="reset@example.com",
            password_hash="not-used",
            role="user",
        )

        token = generate_reset_token(user)
        payload = verify_reset_token(token, max_age=1800)

        assert payload == (123, "reset@example.com")


def test_invalid_password_reset_token(app):
    from app.services.password_reset import verify_reset_token

    with app.app_context():
        assert verify_reset_token("invalid-token") is None
