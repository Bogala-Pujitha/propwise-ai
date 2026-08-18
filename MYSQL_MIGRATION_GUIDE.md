# PostgreSQL → MySQL migration guide

## 1. Create the MySQL database

Example for MySQL 8:

```sql
CREATE DATABASE propwise_ai
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER 'propwise_user'@'localhost'
  IDENTIFIED BY 'CHANGE_ME';

GRANT ALL PRIVILEGES
  ON propwise_ai.*
  TO 'propwise_user'@'localhost';

FLUSH PRIVILEGES;
```

Use your existing MySQL host/user/password instead of these example values.

## 2. Create your virtual environment

Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Configure the environment

Copy:

```text
.env.example
```

to:

```text
.env
```

and set:

```text
DATABASE_URL=mysql+pymysql://propwise_user:PASSWORD@127.0.0.1:3306/propwise_ai?charset=utf8mb4
SECRET_KEY=your-real-secret
```

## 4. Verify connectivity

From the activated venv:

```bash
python -c "from sqlalchemy import create_engine; import os; e=create_engine(os.environ['DATABASE_URL']); c=e.connect(); print('MySQL connection OK:', c.engine.url.get_backend_name()); c.close()"
```

Expected backend:

```text
mysql
```

## 5. Create the schema

Your existing Flask application imports the SQLAlchemy models before
`db.init_app()`. After switching `DATABASE_URL`, use your existing application
database initialization process to create the tables.

If your project uses:

```python
db.create_all()
```

run it inside the Flask application context once against the new database.

Do not copy the old PostgreSQL schema blindly.

## 6. Existing SQLite data

If you need to preserve data from the local SQLite database:

```bash
set MYSQL_DATABASE_URL=mysql+pymysql://propwise_user:PASSWORD@127.0.0.1:3306/propwise_ai?charset=utf8mb4
python scripts/migrate_sqlite_to_mysql.py
```

Linux/macOS:

```bash
export MYSQL_DATABASE_URL='mysql+pymysql://propwise_user:PASSWORD@127.0.0.1:3306/propwise_ai?charset=utf8mb4'
python scripts/migrate_sqlite_to_mysql.py
```

The destination tables must exist first.

## 7. What stays unchanged

The database driver change does NOT require rewriting:

- Flask controllers
- Flask services
- SQLAlchemy model classes
- authentication logic
- admin/RBAC logic
- ML models
- model artifacts
- valuation engine
- SHAP
- OOD
- uncertainty
- reliability
- comparables
- What-if

## 8. CI

The current automated tests intentionally use:

```text
PROPWISE_TESTING=1
```

which gives the test suite SQLite in-memory isolation. That is useful because CI
does not need a running MySQL server for ordinary unit/integration tests.

For production/deployment, `PROPWISE_TESTING` must not be set to `1`, and
`DATABASE_URL` must point to MySQL.

## 9. PostgreSQL removal checklist

After this migration:

- Remove `psycopg2-binary` from requirements.
- Add `pymysql`.
- Remove PostgreSQL URL parsing.
- Remove PostgreSQL-only error messages.
- Delete `scripts/migrate_sqlite_to_postgres.py`.
- Replace any environment variables or deployment settings that still contain
  a PostgreSQL URL.
- Use `mysql+pymysql://` as the official application connection URL.

The resulting application architecture is:

```text
PropWise AI
    ↓
Flask
    ↓
Flask-SQLAlchemy
    ↓
SQLAlchemy
    ↓
PyMySQL
    ↓
MySQL 8+
```
