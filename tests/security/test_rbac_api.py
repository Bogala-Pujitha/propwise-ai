from app import app, db


def test_admin_api_requires_authentication():
    app.config.update(TESTING=True)
    with app.test_client() as client:
        response = client.get("/api/admin/dashboard")
        assert response.status_code in (401, 403)


def test_user_cannot_access_admin_api():
    app.config.update(TESTING=True)
    with app.app_context():
        db.create_all()
        with app.test_client() as client:
            response = client.post("/api/auth/register", json={
                "username": "normal_user_rbac",
                "email": "normal_user_rbac@example.com",
                "password": "StrongPass1!",
            })
            assert response.status_code == 201
            client.post("/api/auth/login", json={
                "username": "normal_user_rbac",
                "password": "StrongPass1!",
                "role": "user",
            })
            response = client.get("/api/admin/dashboard")
            assert response.status_code == 403
        db.session.rollback()
        db.drop_all()
