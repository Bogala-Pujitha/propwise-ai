"""Copy a local SQLite PropWise database into MySQL.

Usage:
    set MYSQL_DATABASE_URL=mysql+pymysql://user:pass@host:3306/propwise_ai
    python scripts/migrate_sqlite_to_mysql.py

This is intended for migration of the current application's SQLAlchemy-backed
tables. Always back up the source and destination before migration.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Iterable

from sqlalchemy import create_engine, inspect, text


DEFAULT_SQLITE = Path("backend/propwise.db")


def mysql_url() -> str:
    value = os.environ.get("MYSQL_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not value:
        raise RuntimeError(
            "Set MYSQL_DATABASE_URL or DATABASE_URL to a mysql+pymysql:// URL."
        )
    if value.startswith("mysql://"):
        value = "mysql+pymysql://" + value[len("mysql://") :]
    if not value.startswith("mysql+pymysql://"):
        raise RuntimeError("Destination must be a mysql+pymysql:// URL.")
    return value


def sqlite_rows(connection: sqlite3.Connection, table: str, columns: list[str]):
    placeholders = ", ".join("?" for _ in columns)
    quoted = ", ".join(f'"{c}"' for c in columns)
    sql = f'SELECT {quoted} FROM "{table}"'
    cursor = connection.execute(sql)
    for row in cursor:
        yield dict(zip(columns, row))


def copy_table(
    sqlite_connection: sqlite3.Connection,
    mysql_connection,
    table: str,
) -> int:
    inspector = inspect(mysql_connection)
    if table not in inspector.get_table_names():
        raise RuntimeError(
            f"MySQL table {table!r} does not exist. "
            "Run the application's db.create_all/migration step first."
        )

    columns = [col["name"] for col in inspector.get_columns(table)]
    rows = sqlite_rows(sqlite_connection, table, columns)

    if not columns:
        return 0

    quoted_columns = ", ".join(f"`{c}`" for c in columns)
    values = ", ".join(f":v{i}" for i in range(len(columns)))

    statement = text(
        f"INSERT INTO `{table}` ({quoted_columns}) VALUES ({values})"
    )

    count = 0
    for row in rows:
        mysql_connection.execute(
            statement,
            {f"v{i}": row[column] for i, column in enumerate(columns)},
        )
        count += 1

    return count


def discover_tables(sqlite_connection: sqlite3.Connection) -> Iterable[str]:
    rows = sqlite_connection.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
        "ORDER BY name"
    )
    return [row[0] for row in rows]


def main() -> None:
    sqlite_path = Path(
        os.environ.get("SQLITE_SOURCE", str(DEFAULT_SQLITE))
    )

    if not sqlite_path.exists():
        raise FileNotFoundError(f"SQLite database not found: {sqlite_path}")

    engine = create_engine(mysql_url(), pool_pre_ping=True, pool_recycle=280)

    sqlite_connection = sqlite3.connect(sqlite_path)

    tables = list(discover_tables(sqlite_connection))
    if not tables:
        raise RuntimeError("SQLite database contains no application tables.")

    print(f"Found {len(tables)} SQLite tables: {', '.join(tables)}")

    with engine.begin() as mysql_connection:
        for table in tables:
            count = copy_table(
                sqlite_connection,
                mysql_connection,
                table,
            )
            print(f"{table}: copied {count} rows")

    sqlite_connection.close()
    print("SQLite → MySQL migration completed.")


if __name__ == "__main__":
    main()
