# PropWise AI urgent remaining pack

Copy these files into the matching paths.

Main fixes included:
- Correct MySQL CI indentation/readiness
- MySQL config
- Health endpoint
- ML evaluation
- ML error analysis
- Production readiness check
- MySQL integration test
- Alembic environment

IMPORTANT:
1. Do not duplicate your existing controllers/services.
2. In app/factory.py register health_bp once.
3. Remove psycopg2-binary and add PyMySQL in requirements.txt.
4. Delete scripts/migrate_sqlite_to_postgres.py.
5. Before claiming the Hyderabad test is locked, exclude its rows from final training.
