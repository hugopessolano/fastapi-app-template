# External Database Guide

Use this guide to connect the template to an additional database (legacy system, reporting warehouse, etc.) via `EXTERNAL_DB_URL` without touching the primary database used for auth/roles.

## 1. Requirements
- The external database must be reachable (SQLite, MariaDB, Postgres, etc.).
- Know the SQLAlchemy connection string. Examples:
  - SQLite: `sqlite:///./app/external.db`
  - MySQL/MariaDB (`mysqlclient`): `mysql+mysqldb://user:pass@host/dbname`
  - Postgres: `postgresql+psycopg2://user:pass@host/dbname`

## 2. Configure `.env`
```
EXTERNAL_DB_URL="sqlite:///./app/external.db"
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
`app/database/external.py` exposes `get_external_db()`. Inject it via FastAPI dependencies.

```python - <<'PY'
from fastapi import APIRouter, Depends
from sqlalchemy import text
from app.database.external import get_external_db

router = APIRouter(prefix="/legacy", tags=["Legacy"])

@router.get("/items")
def list_legacy_items(conn = Depends(get_external_db)):
    rows = conn.execute(text("SELECT id, name FROM legacy_items")).fetchall()
    return [{"id": row[0], "name": row[1]} for row in rows]
```

> If `EXTERNAL_DB_URL` is empty, `get_external_db()` raises a clear error. You can catch it to return a friendly message or guard the route behind a feature flag if needed.

## 5. Validate the connection
1. Start the API (`uvicorn` or `docker compose up --build`).
2. Call the endpoint you created (e.g., `/legacy/items`).
3. Confirm it returns data from the external database.

## 6. Best practices
- **Separate sessions**: always use `get_external_db()` rather than hand-crafted engines so dependency injection handles creation and cleanup.
- **Multiple external DBs**: if you need more than one source, create helpers like `external_reports.py`, `external_legacy.py` modeled after `external.py`, each pointing to a different URL.
- **Handle secrets carefully**: never commit real credentials. Document new variables in `.env.example`.

With this pattern the primary database stays focused on users/roles while you safely integrate any number of secondary databases.
