from app import app


def test_modular_blueprints_register_once():
    from app.controllers import register_blueprints

    names_before = set(app.blueprints.keys())
    for name in [
        "auth_api", "user_api", "admin_api", "analytics_api",
        "valuation_api", "comparable_api", "what_if_api",
    ]:
        if name not in names_before:
            register_blueprints(app)
            break

    for expected in [
        "auth_api", "user_api", "admin_api", "analytics_api",
        "valuation_api", "comparable_api", "what_if_api",
    ]:
        assert expected in app.blueprints
