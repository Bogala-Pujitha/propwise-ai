"""
Migrate an existing PropWise SQLite database into PostgreSQL.

Usage (PowerShell):
    $env:SQLITE_DATABASE_URL="sqlite:///instance/propwise.db"
    $env:DATABASE_URL="postgresql+psycopg2://propwise:password@localhost:5432/propwise"
    python scripts/migrate_sqlite_to_postgres.py

The target PostgreSQL database should already exist.
The script creates the application's SQLAlchemy tables, copies rows, and
resets PostgreSQL integer sequences where possible.
"""

import os
import sys
from pathlib import Path

from sqlalchemy import MetaData, create_engine, text


def normalize_sqlalchemy_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql+psycopg2://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg2://" + url[len("postgresql://") :]
    return url


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def get_app_metadata(target_url: str):
    """
    Import the existing application after DATABASE_URL is set so that the
    established SQLAlchemy models define the PostgreSQL schema.
    """
    os.environ["DATABASE_URL"] = target_url

    try:
        from app import app, db
    except Exception as exc:
        raise SystemExit(
            "Could not import the PropWise application. "
            "Apply the PostgreSQL DATABASE_URL configuration first.\n"
            f"Original error: {exc}"
        ) from exc

    return app, db


def main() -> int:
    sqlite_url = normalize_sqlalchemy_url(require_env("SQLITE_DATABASE_URL"))
    target_url = normalize_sqlalchemy_url(require_env("DATABASE_URL"))

    if not sqlite_url.startswith("sqlite"):
        raise SystemExit("SQLITE_DATABASE_URL must point to the existing SQLite database.")
    if not target_url.startswith("postgresql"):
        raise SystemExit("DATABASE_URL must point to PostgreSQL.")

    sqlite_engine = create_engine(sqlite_url)
    postgres_engine = create_engine(target_url, pool_pre_ping=True)

    # Make sure the source exists before doing anything to the target.
    with sqlite_engine.connect() as source_conn:
        source_conn.execute(text("SELECT 1"))

    app, db = get_app_metadata(target_url)

    with app.app_context():
        db.create_all()
        target_metadata = db.metadata

    source_metadata = MetaData()
    source_metadata.reflect(bind=sqlite_engine)

    if not source_metadata.tables:
        raise SystemExit("No SQLite tables were found.")

    ordered_target_tables = [
        table for table in target_metadata.sorted_tables
        if table.name in source_metadata.tables
    ]

    print(f"SQLite tables found: {len(source_metadata.tables)}")
    print(f"Tables to migrate: {len(ordered_target_tables)}")

    with sqlite_engine.connect() as source_conn, postgres_engine.begin() as target_conn:
        for target_table in ordered_target_tables:
            source_table = source_metadata.tables[target_table.name]
            rows = source_conn.execute(source_table.select()).mappings().all()

            if not rows:
                print(f"{target_table.name}: 0 rows")
                continue

            # Do not duplicate data in a target that already contains rows.
            existing = target_conn.execute(
                text(f'SELECT COUNT(*) FROM "{target_table.name}"')
            ).scalar_one()

            if existing:
                print(
                    f"{target_table.name}: skipped (target already contains "
                    f"{existing} rows)"
                )
                continue

            column_names = {
                column.name for column in target_table.columns
            }

            payload = [
                {
                    key: value
                    for key, value in dict(row).items()
                    if key in column_names
                }
                for row in rows
            ]

            if payload:
                target_conn.execute(target_table.insert(), payload)

            print(f"{target_table.name}: migrated {len(payload)} rows")

        # Advance common PostgreSQL integer sequences after explicit id inserts.
        for target_table in ordered_target_tables:
            if "id" not in target_table.c:
                continue

            sequence_sql = text(
                "SELECT pg_get_serial_sequence(:table_name, 'id')"
            )
            sequence_name = target_conn.execute(
                sequence_sql, {"table_name": target_table.name}
            ).scalar_one_or_none()

            if not sequence_name:
                continue

            max_id = target_conn.execute(
                text(f'SELECT MAX("id") FROM "{target_table.name}"')
            ).scalar_one_or_none()

            if max_id is None:
                continue

            target_conn.execute(
                text(
                    "SELECT setval(:sequence_name::regclass, "
                    ":max_id, true)"
                ),
                {
                    "sequence_name": sequence_name,
                    "max_id": int(max_id),
                },
            )

    print("\nSQLite → PostgreSQL migration completed.")
    print("Verify row counts and run the PropWise test suite before deleting SQLite.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
