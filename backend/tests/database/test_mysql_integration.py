import os

import pytest
from sqlalchemy import text

from backend import create_app
from backend.extensions import db


@pytest.mark.skipif(
    not os.getenv("MYSQL_TEST_DATABASE_URL"),
    reason="Set MYSQL_TEST_DATABASE_URL to run the real MySQL integration test.",
)
def test_mysql_real_connection():
    mysql_url = os.environ["MYSQL_TEST_DATABASE_URL"]

    # Force this test to use the real MySQL database.
    os.environ["DATABASE_URL"] = mysql_url
    os.environ.pop("PROPWISE_TESTING", None)

    app = create_app(
        {
            "SQLALCHEMY_DATABASE_URI": mysql_url,
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        }
    )

    with app.app_context():
        with db.engine.connect() as connection:
            value = connection.execute(text("SELECT 1")).scalar_one()

            assert value == 1
            assert db.engine.url.get_backend_name() == "mysql"