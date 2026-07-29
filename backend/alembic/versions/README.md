# Alembic Migrations

Never manually edit the database schema. All changes must go through Alembic migrations.

## Commands

```bash
# Generate a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```
