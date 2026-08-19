# PropWise AI

A Flask-based property valuation platform powered by machine learning. Predict
property prices across Indian metropolitan cities, explore comparable listings,
run what-if scenarios, and manage an admin analytics dashboard — all backed by a
trained ML pipeline and a SQLite database.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Available Endpoints](#available-endpoints)
- [Machine Learning Pipeline](#machine-learning-pipeline)
- [Database Migrations](#database-migrations)
- [Testing](#testing)
- [Utility Scripts](#utility-scripts)
- [Default Credentials](#default-credentials)
- [Linting](#linting)
- [Deployment](#deployment)

---

## Features

- **Property Valuation** — Predict sale prices for apartments, houses, villas, and plots using trained XGBoost models with SHAP-based explainability.
- **What-If Analysis** — Simulate price changes by adjusting BHK, area, bathrooms, and property age.
- **Comparables** — Find nearby properties and price-per-sqft comparisons for a given locality.
- **Bulk Valuation** — Upload a CSV of properties and receive valuations for all rows.
- **Market Intelligence** — Visualize price heatmaps and city-level analytics.
- **User Management** — Register, log in, reset passwords, and track user roles (user / admin).
- **Admin Dashboard** — Analytics summary, user management, and audit logs.
- **Activity Tracking** — Every user action is logged for analytics and audit purposes.
- **Out-of-Distribution Detection** — Flags predictions for properties outside the training data distribution.

---

## Architecture

The project follows a **full MVC architecture** with a clean separation between
the backend (Model + Controller + services) and the frontend (View layer):

```
PropWise AI
├── backend/              # Backend application (MVC: Model + Controller + Service)
│   ├── __init__.py       # Package entry-point; creates the Flask app
│   ├── __main__.py       # Development server entry point (python -m backend)
│   ├── extensions.py     # SQLAlchemy, Flask-Login, Bcrypt, CORS instances
│   ├── factory.py        # Application factory and extension wiring
│   ├── health.py         # Health-check blueprint
│   ├── security.py       # HTTP security headers and admin_required decorator
│   ├── runtime.py        # Lazy ML-engine lifecycle container
│   ├── legacy_monolith.py# Legacy migration archive (not imported at runtime)
│   ├── wsgi.py           # WSGI entry point for production servers
│   ├── config/           # Configuration layer
│   │   ├── config.py     # Default configuration mapping
│   │   ├── database.py   # SQLite URL helper
│   │   └── security.py   # RBAC role-based access decorators
│   ├── models/           # ORM schema (SQLAlchemy)
│   │   ├── user.py       # User model with role-based auth
│   │   ├── prediction.py # Prediction record model
│   │   ├── activity.py   # Activity log model
│   │   ├── admin.py      # Admin model
│   │   ├── audit.py      # Audit log model
│   │   ├── comparable.py # Comparable result model
│   │   └── database.py   # db instance + compatibility re-exports
│   ├── controllers/      # MVC Controller — API blueprints
│   │   ├── __init__.py     # Blueprint registration
│   │   ├── auth_controller.py
│   │   ├── user_controller.py
│   │   ├── admin_controller.py
│   │   ├── analytics_controller.py
│   │   ├── valuation_controller.py
│   │   ├── comparable_controller.py
│   │   ├── what_if_controller.py
│   │   ├── behavior_controller.py
│   │   ├── map_controller.py
│   │   ├── password_reset_controller.py
│   │   └── web/          # HTML/browser route controllers
│   │       ├── __init__.py
│   │       ├── public_controller.py
│   │       ├── dashboard_controller.py
│   │       ├── valuation_controller.py
│   │       ├── admin_controller.py
│   │       └── insights_controller.py
│   ├── services/         # Business logic layer
│   │   ├── auth_service.py
│   │   ├── activity_service.py
│   │   ├── analytics.py
│   │   ├── valuation_engine.py
│   │   ├── valuation_service.py
│   ├── scripts/          # Operational utility scripts
│   │   ├── check_production_readiness.py
│   │   └── migrate_sqlite_to_postgres.py
│   ├── tests/            # Backend and integration test suite
│   └── migrations/       # Alembic database migrations
│       ├── env.py
│       ├── README.md
│       └── script.py.mako
├── frontend/             # Frontend (MVC View layer)
│   ├── templates/        # Jinja2 HTML templates
│   └── static/           # Browser assets (CSS, JS, images)
├── ml/                   # ML training and evaluation pipeline
│   ├── error_analysis/   # OOD detection and residual analysis
│   ├── evaluation/       # Model evaluation and metrics
│   ├── preprocessing/    # Data pipeline and feature engineering
│   └── training/         # Model training (XGBoost, RandomForest, Ridge)
├── models/               # Trained ML model artifacts (.joblib, .json)
├── data/                 # Raw, processed, and report data
├── requirements.txt      # Shared Python dependencies
├── .env.example          # Environment variable template
├── .flake8               # Flake8 linting configuration
├── .gitignore
├── ARCHITECTURE.md       # Detailed architecture documentation
└── .github/workflows/    # CI/CD pipelines
```

---

## Prerequisites

- **Python** >= 3.10 (developed on 3.11; compatible with 3.10+; 3.12 and 3.13
  should work as all dependencies are maintained)
- **pip** (or any compatible package manager)
- **Git** (for cloning the repository)

No external database server is required — the application uses **SQLite** by
default, which is built into Python's standard library.

---

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd propwise-ai
```

### 2. Create and activate a virtual environment

#### Linux / macOS

```bash
python -m venv venv
source venv/bin/activate
```

#### Windows (PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### Windows (Command Prompt)

```cmd
python -m venv venv
venv\Scripts\activate.bat
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

For database migrations, also install Alembic:

```bash
pip install alembic
```

For production WSGI serving via `wsgi.py`, also install:

```bash
pip install python-dotenv
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` to adjust paths and keys as needed (see
[Configuration](#configuration) below).

---

## Configuration

Environment variables are read from `.env` (loaded automatically by `wsgi.py`
and the test suite). Create a `.env` file from the template:

| Variable        | Description                                      | Default                          |
|-----------------|--------------------------------------------------|----------------------------------|
| `DATABASE_URL`  | SQLAlchemy database connection URL               | `sqlite:///./backend/propwise.db`|
| `SECRET_KEY`    | Flask session signing key                        | `propwise-ai-secret-key-2024`    |
| `FLASK_ENV`     | Flask environment (`development`, `production`)  | `development`                    |
| `PROPWISE_TESTING`| Set to `1` to use in-memory SQLite for tests   | (not set)                        |
| `TESTING`       | Flask testing flag                               | (not set)                        |

The `.env.example` file contains a portable, OS-agnostic configuration:

```dotenv
DATABASE_URL=sqlite:///./backend/propwise.db
SECRET_KEY=change-this-in-development
FLASK_ENV=development
```

> **Note:** The `.env` file is listed in `.gitignore` and is never committed to
> version control.

---

## Running the Application

### Development server

The quickest way to start the app with auto-reload, database initialization, and
a default admin user:

```bash
python -m backend
```

This will:
1. Create all database tables (`db.create_all()`)
2. Create a default admin user if none exists (`admin` / `admin123`)
3. Load the ML valuation engine lazily
4. Start the Flask development server on `http://localhost:5000`

### Production WSGI server

Use the `wsgi.py` entry point with a production WSGI server such as Gunicorn:

```bash
# Install Gunicorn if you haven't already
pip install gunicorn

# Run with 4 worker processes
gunicorn -w 4 -b 0.0.0.0:5000 backend.wsgi:application
```

Or with uWSGI:

```bash
pip install uwsgi
uwsgi --http :5000 --module backend.wsgi:application --processes 4
```

---

## Available Endpoints

### Web (HTML) Routes

These serve Jinja2 templates from `frontend/templates/`.

| Method | Path                     | Description                          |
|--------|--------------------------|--------------------------------------|
| GET    | `/`                      | Landing page                         |
| GET,POST | `/login`               | Login page                           |
| GET,POST | `/register`            | Registration page                    |
| GET    | `/logout`               | Log out                              |
| GET,POST | `/forgot-password`     | Password reset request               |
| GET    | `/dashboard`            | Dashboard                            |
| GET    | `/user/dashboard`       | User dashboard                       |
| GET    | `/predict`              | Property valuation form              |
| GET,POST | `/what-if`             | What-if analysis                     |
| GET,POST | `/comparables`         | Find comparable properties           |
| GET    | `/market-intelligence`  | Market intelligence map              |
| GET    | `/map`                  | Map view                             |
| GET    | `/model-performance`    | Model performance metrics            |
| GET    | `/experiments`          | Experiment tracking                  |
| GET    | `/admin`                | Admin dashboard (admin only)        |
| GET    | `/admin/users`          | Admin user management (admin only)  |
| GET    | `/admin/analytics`      | Admin analytics (admin only)         |
| GET    | `/admin/audit`          | Admin audit log (admin only)         |

### JSON API

All API routes share the `/api/` prefix and return JSON responses. Most require
authentication via `@login_required`.

#### Authentication (`/api/auth`)

| Method | Path             | Auth     | Description                          |
|--------|------------------|----------|--------------------------------------|
| POST   | `/api/auth/register` | No    | Register a new user                  |
| POST   | `/api/auth/login`    | No    | Log in and receive session cookie   |
| POST   | `/api/auth/logout`   | Yes   | Log out                              |
| GET    | `/api/auth/me`       | Yes   | Get current user info                |

#### Valuation (`/api/valuation`)

| Method | Path                | Auth | Description                         |
|--------|---------------------|------|-------------------------------------|
| POST   | `/api/valuation/predict` | Yes | Predict a property value            |

#### Analytics (`/api/analytics`)

| Method | Path                      | Auth  | Description                              |
|--------|---------------------------|-------|------------------------------------------|
| GET    | `/api/analytics/admin/summary` | Admin | Get overall platform summary statistics |

#### Admin (`/api/admin`)

| Method | Path             | Auth  | Description                          |
|--------|------------------|-------|--------------------------------------|
| GET    | `/api/admin/users`   | Admin | List all users with stats            |
| GET    | `/api/admin/dashboard` | Admin | Get dashboard summary data            |
| GET    | `/api/admin/audit`   | Admin | Get audit log entries                |

#### Other API Controllers

- `/api/comparables` — Find comparable properties
- `/api/what-if` — What-if scenario analysis
- `/api/behavior` — User behavior tracking
- `/api/map` — Map and location data
- `/api/password-reset` — Password reset flow

---

## Machine Learning Pipeline

The `ml/` directory contains the full ML lifecycle:

### 1. Preprocessing (`ml/preprocessing/`)

- `data_pipeline.py` — Cleans raw property data from `data/raw/`, handles missing
  values, encodes categorical features, and produces `data/processed/master_dataset.csv`.

### 2. Training (`ml/training/`)

- `model_trainer.py` — Trains property-type-specific models (Apartment, House,
  Villa, Plot) using XGBoost, RandomForest, and Ridge regressors. Models are
  saved to `models/` as `.joblib` files with accompanying metadata `.json` files.

### 3. Evaluation (`ml/evaluation/`)

- `evaluator.py` — Evaluates trained models against the test set and produces
  performance reports.
- `metrics.py` — Regression metrics (MAE, RMSE, R², MAPE).
- `locked_test.py` — Locked/holdout evaluation suite.

### 4. Error Analysis (`ml/error_analysis/`)

- `residual_analysis.py` — Analyzes prediction residuals.
- `report.py` — Generates error analysis reports.

### Training a Model

```bash
python ml/training/model_trainer.py
```

### Evaluating Models

```bash
python -m ml.evaluation.evaluator
```

---

## Database Migrations

Alembic is used for database schema migrations.

### Initialize / run migrations

```bash
# Generate a new migration
alembic revision --autogenerate -m "description of change"

# Apply pending migrations
alembic upgrade head

# Roll back the last migration
alembic downgrade -1

# View current migration status
alembic history
```

Migrations are configured via `backend/alembic.ini` and
`backend/migrations/env.py`. By default, they use the `DATABASE_URL`
environment variable or fall back to `sqlite:///backend/propwise.db`.

---

## Testing

The test suite uses **pytest** and runs an in-memory SQLite database by default
(setting `PROPWISE_TESTING=1`), so no real database is touched during tests.

### Run all tests

```bash
pytest
```

### Run tests with verbose output

```bash
pytest -v
```

### Run a specific test file

```bash
pytest backend/tests/test_all.py -v
```

### Test structure

```
backend/tests/
├── conftest.py                    # Sets PROPWISE_TESTING for in-memory DB
├── test_all.py                  # Data pipeline + valuation engine tests
├── api/                         # API endpoint tests
│   ├── test_protected_api.py
│   └── test_protected_routes.py
├── auth/                        # Authentication tests
│   ├── test_auth_api.py
│   └── test_auth_security.py
├── database/                    # Database configuration tests
│   └── test_sqlite_config.py
├── integration/                 # Full integration tests
│   ├── test_health.py
│   ├── test_modular_api.py
│   ├── test_user_journey.py
│   └── test_complete_user_journey.py
├── ml/                          # ML pipeline tests
│   └── test_evaluation.py
└── security/                    # Security and RBAC tests
    ├── test_rbac.py
    ├── test_rbac_api.py
    ├── test_password_reset.py
    └── test_authorization_matrix.py
```

---

## Utility Scripts

| Script | Purpose |
|--------|---------|
| `python -m backend` | Start the development server with DB init and admin creation |
| `python backend/scripts/check_production_readiness.py` | Verify production environment configuration |
| `python backend/scripts/migrate_sqlite_to_postgres.py` | Migrate an existing SQLite database to PostgreSQL |

### Production readiness check

```bash
FLASK_ENV=production SECRET_KEY=your-secret-key DATABASE_URL=sqlite:///./backend/propwise.db \
  python backend/scripts/check_production_readiness.py
```

---

## Default Credentials

When the app starts via `python -m backend`, a default admin user is created
automatically (only if no admin exists yet):

| Username | Password   | Role  |
|----------|------------|-------|
| `admin`  | `admin123` | admin |

Change these immediately in any non-development environment.

---

## Linting

```bash
flake8 backend ml --count --statistics
```

Configuration is in `.flake8` (max line length: 127; ignores E402, W503, W292,
W504).

---

## Deployment

### GitHub Actions CI

The project includes GitHub Actions workflows at `.github/workflows/`:

- **`ci.yml`** — Runs on push/PR to `main`. Compiles Python, runs Flake8, and
  executes the test suite.
- **`deploy.yml`** — Triggered on tagged releases (`v*.*.*`). Runs production
  readiness checks and provides a deployment placeholder.

### WSGI Production

For production deployment, use the WSGI entry point:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 backend.wsgi:application
```

### Environment secrets (GitHub Actions)

| Secret                  | Description                        |
|-------------------------|------------------------------------|
| `PROPWISE_SECRET_KEY`   | Flask SECRET_KEY for sessions      |
| `PROPWISE_DATABASE_URL` | Database connection string         |

---

## Data Sources

The application ships with property data from major Indian metropolitan cities:

| City      | Source file                           |
|-----------|---------------------------------------|
| Hyderabad | `Hyderbad_House_price.csv`            |
| Bengaluru | `bengaluru_house_prices.csv`          |
| Chennai   | `Chennai houseing sale.csv`           |
| Kolkata   | `Kolkata.csv`                         |
| Mumbai    | `Mumbai.csv`                          |
| Pune      | `output_Pune_*.csv`                   |
| Other     | `Property_cleaned.csv`, `clean_data.csv`, `houses.csv`, and more |

Raw data is stored in `data/raw/`, processed data in `data/processed/`, and
generated reports (data quality, model performance, error analysis) in
`data/reports/`.
