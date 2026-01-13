# External Database Guide

Use this guide to connect the template to one or more external databases (legacy system, reporting warehouse, etc.) without touching the primary database used for auth/roles.

## 1. Requirements
- The external database must be reachable (SQLite, MariaDB, Postgres, etc.).
- Install the driver for the engine you use (`pymysql` for MariaDB/MySQL, `psycopg2-binary` for Postgres).
- Know the SQLAlchemy connection string. Examples:
  - SQLite: `sqlite:///./app/external.db`
  - MySQL/MariaDB (`pymysql`): `mysql+pymysql://user:pass@host/dbname`
  - Postgres: `postgresql+psycopg2://user:pass@host/dbname`

## 2. Configure `.env`
```
# Legacy single-connection (optional)
EXTERNAL_DB_URL="sqlite:///./app/external.db"

# Multiple connections (recommended)
EXTERNAL_DB_REPORTING_URL="sqlite:///./app/reporting.db"
EXTERNAL_DB_REPORTING_PERMISSIONS="read"

EXTERNAL_DB_LEGACY_URL="sqlite:///./app/legacy.db"
EXTERNAL_DB_LEGACY_PERMISSIONS="read,update"
```
If you run via Docker Compose, the existing `env_file: .env` entry already exposes this value to the container.

## 3. Prepare the external DB
### Quick SQLite example
```python - <<'PY'
import sqlite3
conn = sqlite3.connect('app/external.db')
conn.execute("CREATE TABLE IF NOT EXISTS legacy_items(id INTEGER PRIMARY KEY, name TEXT)")
conn.execute("INSERT INTO legacy_items(name) VALUES ('Legacy item')")
conn.commit()
conn.close()
PY
```
For other engines, create tables and grant permissions using their native tools/migrations.

## 4. Use the helper in the app
`app/database/external_registry.py` exposes helpers for named connections. Inject them via FastAPI dependencies.

```python - <<'PY'
from fastapi import APIRouter, Depends
from sqlalchemy import text
from app.database.external_registry import external_db_dependency

router = APIRouter(prefix="/v1/legacy", tags=["Legacy"])

@router.get("/items")
def list_legacy_items(conn = Depends(external_db_dependency("legacy", ["read"]))):
    rows = conn.execute(text("SELECT id, name FROM legacy_items")).fetchall()
    return [{"id": row[0], "name": row[1]} for row in rows]
```

> If a connection is missing, `external_db_dependency` raises a clear error. You can catch it to return a friendly message or guard the route behind a feature flag if needed.

## 5. Validate the connection
1. Start the API (`uvicorn` or `docker compose up --build`).
2. Call the endpoint you created (e.g., `/v1/legacy/items`).
3. Confirm it returns data from the external database.

## 6. Best practices
- **Separate sessions**: always use `get_external_db()` rather than hand-crafted engines so dependency injection handles creation and cleanup.
- **Multiple external DBs**: declare each connection with `EXTERNAL_DB_<NAME>_URL` and use `external_db_dependency("<name>")`.
- **Permissions**: set `EXTERNAL_DB_<NAME>_PERMISSIONS` to a comma-separated list (`read,create,update,delete`). If omitted, all permissions are allowed.
- **Handle secrets carefully**: never commit real credentials. Document new variables in `.env.example`.

With this pattern the primary database stays focused on users/roles while you safely integrate any number of secondary databases.
