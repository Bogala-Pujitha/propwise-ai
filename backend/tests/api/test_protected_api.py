from backend import app


def test_user_profile_requires_login():
    app.config.update(TESTING=True)
    with app.test_client() as client:
        response = client.get("/api/user/profile")
        assert response.status_code in (401, 302)


def test_user_history_requires_login():
    app.config.update(TESTING=True)
    with app.test_client() as client:
        response = client.get("/api/user/history")
        assert response.status_code in (401, 302)
