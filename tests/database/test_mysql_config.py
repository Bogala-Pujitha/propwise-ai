from app.config.database import get_database_url


def test_mysql_url_is_normalized(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "mysql://user:password@localhost:3306/propwise_ai",
    )

    url = get_database_url()

    assert url.startswith(
        "mysql+pymysql://user:password@localhost:3306/propwise_ai"
    )
    assert "charset=utf8mb4" in url


def test_mysql_driver_url_is_accepted(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "mysql+pymysql://user:password@localhost:3306/propwise_ai",
    )

    url = get_database_url()

    assert url.startswith("mysql+pymysql://")


def test_postgresql_url_is_rejected(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg2://user:password@localhost:5432/propwise_ai",
    )

    try:
        get_database_url()
    except RuntimeError as exc:
        assert "MySQL" in str(exc)
    else:
        raise AssertionError("PostgreSQL URL should be rejected")
