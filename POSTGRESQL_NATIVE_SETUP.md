# PropWise AI — Native PostgreSQL Setup

PostgreSQL is the only supported application database.

There is no SQLite fallback and there is no SQLite-to-PostgreSQL migration
utility in this architecture.

## Runtime architecture

    PropWise AI
         ↓
    Flask-SQLAlchemy
         ↓
    psycopg2
         ↓
    PostgreSQL

## 1. Create the PostgreSQL database

Create a PostgreSQL database named:

    propwise

Create a PostgreSQL user with permission to use that database.

## 2. Configure the environment

Copy `.env.example` to `.env` and set:

    DATABASE_URL=postgresql+psycopg2://propwise:<password>@localhost:5432/propwise

Also set a secure `SECRET_KEY`.

Do not commit `.env`.

## 3. Install dependencies

Activate the existing Python virtual environment:

    .\.venv\Scripts\Activate.ps1

Install:

    pip install -r requirements.txt

The PostgreSQL driver is already included:

    psycopg2-binary==2.9.9

## 4. Configure the existing Flask application

Use the existing SQLAlchemy object in the project. Do not create a second
database instance.

Where the current application initializes its database configuration, call:

    from app.config.database import configure_database
    configure_database(app)

Then keep the project's existing `db = SQLAlchemy(app)` or
`db.init_app(app)` pattern.

## 5. Initialize the PostgreSQL schema

Use the application's established SQLAlchemy models and initialization flow.

For a fresh development PostgreSQL database, the application can create the
schema through the existing project initialization mechanism.

No SQLite database is required anywhere in the runtime.

## 6. Verify

Run:

    pytest -q

Then start PropWise AI and verify:

- registration
- login/logout
- prediction
- prediction history
- What-If
- comparable search
- admin dashboard
- analytics
- audit logs

## Expected final state

The project should contain:

    DATABASE_URL
    PostgreSQL
    Flask-SQLAlchemy
    psycopg2

It should NOT contain:

    SQLite runtime configuration
    sqlite:///...
    SQLite database files
    SQLite migration scripts
    SQLite fallback logic

The established ML, valuation, SHAP, OOD, uncertainty, reliability,
comparables and What-If components do not need to be rewritten for this
database backend change.
