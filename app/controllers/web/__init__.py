"""HTML controllers registered with stable endpoint names."""

from .admin_controller import (
    admin_analytics,
    admin_audit,
    admin_dashboard,
    admin_users,
)

from .dashboard_controller import (
    api_dropdown_data,
    dashboard,
    user_analytics,
    user_audit,
    user_dashboard,
    user_users,
)

from .insights_controller import (
    experiments,
    map_view,
    market_intelligence,
    model_performance,
)

from .public_controller import (
    forgot_password,
    landing,
    login,
    logout,
    register,
)

from .valuation_controller import (
    bulk_valuation,
    comparables,
    predict,
    what_if,
)


def register_web_routes(app):
    """Attach browser endpoints without changing existing endpoint names."""

    routes = (
        # Public
        (
            "/",
            "landing",
            landing,
            ("GET",),
        ),
        (
            "/register",
            "register",
            register,
            ("GET", "POST"),
        ),
        (
            "/login",
            "login",
            login,
            ("GET", "POST"),
        ),
        (
            "/logout",
            "logout",
            logout,
            ("GET",),
        ),
        (
            "/forgot-password",
            "forgot_password",
            forgot_password,
            ("GET", "POST"),
        ),

        # User
        (
            "/api/dropdown-data",
            "api_dropdown_data",
            api_dropdown_data,
            ("GET",),
        ),
        (
            "/dashboard",
            "dashboard",
            dashboard,
            ("GET",),
        ),
        (
            "/user/dashboard",
            "user_dashboard",
            user_dashboard,
            ("GET",),
        ),
        (
            "/user/users",
            "user_users",
            user_users,
            ("GET",),
        ),
        (
            "/user/analytics",
            "user_analytics",
            user_analytics,
            ("GET",),
        ),
        (
            "/user/audit",
            "user_audit",
            user_audit,
            ("GET",),
        ),

        # Valuation
        (
            "/predict",
            "predict",
            predict,
            ("POST",),
        ),
        (
            "/what-if",
            "what_if",
            what_if,
            ("GET", "POST"),
        ),
        (
            "/comparables",
            "comparables",
            comparables,
            ("GET", "POST"),
        ),
        (
            "/bulk-valuation",
            "bulk_valuation",
            bulk_valuation,
            ("GET", "POST"),
        ),

        # Insights
        (
            "/market-intelligence",
            "market_intelligence",
            market_intelligence,
            ("GET",),
        ),
        (
            "/map",
            "map_view",
            map_view,
            ("GET",),
        ),
        (
            "/model-performance",
            "model_performance",
            model_performance,
            ("GET",),
        ),
        (
            "/experiments",
            "experiments",
            experiments,
            ("GET",),
        ),

        # Existing Admin routes - DO NOT CHANGE
        (
            "/admin",
            "admin_dashboard",
            admin_dashboard,
            ("GET",),
        ),
        (
            "/admin/users",
            "admin_users",
            admin_users,
            ("GET",),
        ),
        (
            "/admin/analytics",
            "admin_analytics",
            admin_analytics,
            ("GET",),
        ),
        (
            "/admin/audit",
            "admin_audit",
            admin_audit,
            ("GET",),
        ),
    )

    for rule, endpoint, view_func, methods in routes:
        if endpoint not in app.view_functions:
            app.add_url_rule(
                rule,
                endpoint=endpoint,
                view_func=view_func,
                methods=methods,
            )