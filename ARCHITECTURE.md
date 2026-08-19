# PropWise AI application layout

The runtime follows a full MVC architecture with separate `backend/` and
`frontend/` directories.  The `backend/` package implements the Model,
Controller, and service layers; the `frontend/` directory holds the View layer
(Jinja templates and static assets).

```
propwise-ai/
├── backend/                     # Backend application (MVC Model + Controller)
│   ├── __init__.py              # Package entry-point; creates the Flask app
│   ├── __main__.py              # Development server entry point (python -m backend)
│   ├── extensions.py            # SQLAlchemy, Flask-Login, Bcrypt, CORS instances
│   ├── factory.py               # Application factory and extension wiring
│   ├── health.py                # Health-check blueprint
│   ├── security.py              # HTTP security headers and admin_required decorator
│   ├── runtime.py               # Lazy ML-engine lifecycle container
│   ├── legacy_monolith.py       # Legacy migration archive (not imported at runtime)
│   ├── wsgi.py                  # WSGI entry point for production servers
│   ├── config/                  # Configuration layer
│   │   ├── __init__.py
│   │   ├── config.py            # Default configuration mapping
│   │   ├── database.py          # SQLite / PostgreSQL URL helpers
│   │   └── security.py          # RBAC role-based access decorators
│   ├── models/                  # MVC Model — ORM schema (SQLAlchemy)
│   │   ├── __init__.py          # Public model exports (User, Prediction, …)
│   │   ├── activity.py
│   │   ├── admin.py
│   │   ├── audit.py
│   │   ├── comparable.py
│   │   ├── database.py          # db instance + compatibility re-exports
│   │   ├── prediction.py
│   │   └── user.py
│   ├── controllers/             # MVC Controller — API blueprints
│   │   ├── __init__.py          # Blueprint registration
│   │   ├── admin_controller.py
│   │   ├── analytics_controller.py
│   │   ├── auth_controller.py
│   │   ├── behavior_controller.py
│   │   ├── comparable_controller.py
│   │   ├── map_controller.py
│   │   ├── password_reset_controller.py
│   │   ├── user_controller.py
│   │   ├── valuation_controller.py
│   │   ├── what_if_controller.py
│   │   └── web/                 # HTML/browser route controllers
│   │       ├── __init__.py      # Stable endpoint registration
│   │       ├── admin_controller.py
│   │       ├── dashboard_controller.py
│   │       ├── insights_controller.py
│   │       ├── public_controller.py
│   │       └── valuation_controller.py
│   ├── services/                # Business logic layer
│   │   ├── __init__.py
│   │   ├── activity_service.py
│   │   ├── analytics.py
│   │   ├── audit_hooks.py
│   │   ├── auth_service.py
│   │   ├── behavior_analytics.py
│   │   ├── behavior_tracking.py
│   │   ├── dashboard_service.py
│   │   ├── email_service.py
│   │   ├── experiment_discovery.py
│   │   ├── geocoding.py
│   │   ├── password_reset.py
│   │   ├── valuation_engine.py
│   │   └── valuation_service.py
│   ├── scripts/                 # Operational utility scripts
│   │   ├── check_production_readiness.py
│   │   ├── migrate_sqlite_to_mysql.py
│   │   └── migrate_sqlite_to_postgres.py
│   ├── tests/                   # Backend and integration test suite
│   └── migrations/              # Alembic database migrations
│       ├── env.py
│       ├── README.md
│       └── script.py.mako
├── frontend/                    # Frontend (MVC View layer)
│   ├── templates/               # Jinja2 HTML templates
│   └── static/                  # Browser assets (CSS, JS, images)
├── ml/                          # ML training and evaluation pipeline
├── models/                      # Trained ML model artifacts (.joblib, .json)
├── data/                        # Raw, processed, and report data
├── requirements.txt             # Shared Python dependencies
├── .env.example                 # Environment variable template
├── .flake8                      # Flake8 linting configuration
├── .gitignore
└── .github/workflows/           # CI/CD pipelines
```

Data safety guarantees:

- The default SQLite target remains `backend/propwise.db`.
- `users`, `predictions`, `activities`, and `audit_logs` retain their original
  names, columns, relationships, and data.
- Root-level `data/` and `models/` artifacts remain in their existing paths.
- The `frontend/templates/` directory is served via `template_folder`;
  `frontend/static/` is served via `static_folder`.
- Existing public imports such as `from backend import app, db, User` and all
  established route URLs remain supported.

`backend/legacy_monolith.py` is a source-only migration archive and is not imported
by the runtime. It can be removed after a release window once downstream
integrations have adopted the modular entry points.
