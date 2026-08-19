"""Password reset token and API tests."""

from backend import app, db, User, bcrypt
from backend.services.password_reset import generate_reset_token, verify_reset_token


def test_reset_token_round_trip():
    with app.app_context():
        db.create_all()
        user = User.query.filter_by(username="reset_test").first()
        if user is None:
            user = User(
                username="reset_test",
                email="reset_test@example.com",
                password_hash=bcrypt.generate_password_hash("StrongPass123").decode("utf-8"),
                role="user",
            )
            db.session.add(user)
            db.session.commit()

        token = generate_reset_token(user)
        payload = verify_reset_token(token)

        assert payload is not None
        assert payload[0] == user.id
        assert payload[1] == user.email
