from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]

SQLITE_DB_PATH = BASE_DIR / "backend" / "propwise.db"


def get_database_url() -> str:
    """
    SQLite-only database configuration.
    """

    return f"sqlite:///{SQLITE_DB_PATH}"


def configure_database(app):
    """
    Configure SQLAlchemy to use SQLite.
    """

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        get_database_url()
    )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False