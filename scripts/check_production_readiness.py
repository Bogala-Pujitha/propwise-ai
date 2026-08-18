"""Fail fast on obvious production configuration problems."""

from __future__ import annotations

import os
import sys
from urllib.parse import urlsplit


def main() -> int:
    problems = []

    secret = os.getenv("SECRET_KEY", "")
    database_url = os.getenv("DATABASE_URL", "")
    flask_env = os.getenv("FLASK_ENV", "").lower()

    if flask_env in {"production", "prod"} and not secret:
        problems.append("SECRET_KEY is missing.")

    if flask_env in {"production", "prod"} and (
        not database_url.startswith("mysql+pymysql://")
    ):
        problems.append("DATABASE_URL must be mysql+pymysql:// in production.")

    if database_url:
        parsed = urlsplit(database_url)
        if parsed.scheme != "mysql+pymysql":
            problems.append(
                f"Unexpected database driver: {parsed.scheme!r}"
            )

    if problems:
        print("PRODUCTION READINESS CHECK FAILED")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("PRODUCTION READINESS CHECK PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
