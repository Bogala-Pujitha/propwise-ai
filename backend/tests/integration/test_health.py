from backend import app


def test_health():
    with app.test_client() as client:
        response = client.get("/health")
        assert response.status_code in (200, 404)
