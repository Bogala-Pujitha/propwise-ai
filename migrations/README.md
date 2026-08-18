Run migrations after installing Alembic:

```bash
pip install alembic
alembic revision --autogenerate -m "initial mysql schema"
alembic upgrade head
```

Do not generate an initial revision blindly if the MySQL database already
contains tables. First inspect the generated migration and compare it with the
actual database schema.
