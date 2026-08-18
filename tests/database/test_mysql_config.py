import os
import pytest
from sqlalchemy.engine import make_url


def test_mysql_dependency():
    import pymysql
    assert pymysql.__version__


@pytest.mark.skipif(
    "DATABASE_URL" not in os.environ,
    reason="DATABASE_URL not configured",
)
def test_database_url_uses_mysql():
    url = make_url(os.environ["DATABASE_URL"])
    assert url.get_backend_name() == "mysql"
