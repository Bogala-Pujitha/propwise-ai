import os
import sys


def main():
    env = os.environ.get("FLASK_ENV", "").lower()
    secret = os.environ.get("SECRET_KEY", "")
    url = os.environ.get("DATABASE_URL", "")

    problems = []

    if env in {"production", "prod"}:
        if not secret:
            problems.append("SECRET_KEY is missing")
        if not url.startswith("mysql+pymysql://"):
            problems.append("DATABASE_URL must be mysql+pymysql://")

    if problems:
        print("PRODUCTION READINESS FAILED")
        for item in problems:
            print("-", item)
        return 1

    print("PRODUCTION READINESS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
