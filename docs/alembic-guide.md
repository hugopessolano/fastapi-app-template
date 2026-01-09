# Alembic Guide (Step by Step)

This guide explains how to create and apply database migrations safely.
It assumes you run commands from the repository root.

## 1) Configure the database URL
Update `.env` with the database you want to migrate:
```
DATABASE_URL="sqlite:///./app/app.db"
```

Alembic reads `DATABASE_URL` through the application settings, so it stays aligned with the API.

## 2) Create a new migration
1. Change or add SQLAlchemy models in `app/database/models/`.
2. Generate a migration file:
```
alembic revision --autogenerate -m "short_message"
```

## 3) Apply migrations
```
alembic upgrade head
```

## 4) Roll back (if needed)
Rollback one revision:
```
alembic downgrade -1
```

Rollback all migrations:
```
alembic downgrade base
```

## 5) Check current revision
```
alembic current
```

## Notes
- Always run Alembic from the repo root so it picks up `alembic.ini`.
- If you switch databases, update `DATABASE_URL` and run migrations again.
