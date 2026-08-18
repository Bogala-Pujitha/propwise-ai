import os

import pytest
from sqlalchemy import text

from app import create_app


@pytest.mark.skipif(
    not os.getenv("MYSQL_TEST_DATABASE_URL"),
    reason="Set MYSQL_TEST_DATABASE_URL to run the real MySQL integration test.",
)
def test_mysql_real_connection():
    os.environ["DATABASE_URL"] = os.environ["MYSQL_TEST_DATABASE_URL"]
    os.environ.pop("PROPWISE_TESTING", None)

    app = create_app()
    db = app.extensions["sqlalchemy"].db

    with app.app_context():
        with db.engine.connect() as connection:
            value = connection.execute(text("SELECT 1")).scalar_one()
            assert value == 1
            assert db.engine.url.get_backend_name() == "mysql"
