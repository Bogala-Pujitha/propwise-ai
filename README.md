# PropWise AI — remaining production files

This add-on pack covers the remaining project-level gaps identified after the
PostgreSQL → MySQL switch:

1. Database migration management with Alembic.
2. MySQL-backed CI integration test.
3. Production-readiness validation script.
4. Deployment workflow template.
5. Health/readiness endpoint helper.

These are additive and do not replace your existing ML, controller, service,
model, authentication or test code.

Before enabling deployment, fill in the required repository secrets/environment
values in GitHub Actions and verify your hosting provider's start command.
