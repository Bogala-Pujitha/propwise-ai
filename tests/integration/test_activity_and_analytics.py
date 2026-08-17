import pytest


@pytest.fixture()
def app():
    from app import app as flask_app
    flask_app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret-key",
    )
    with flask_app.app_context():
        from app import db
        db.create_all()
        yield flask_app
        db.session.remove()


def test_analytics_service_returns_contract(app):
    with app.app_context():
        from app.services.analytics import admin_summary, activity_breakdown
        summary = admin_summary(days=30)
        breakdown = activity_breakdown()

        assert isinstance(summary, dict)
        assert "total_users" in summary
        assert "total_predictions" in summary
        assert isinstance(breakdown, list)
