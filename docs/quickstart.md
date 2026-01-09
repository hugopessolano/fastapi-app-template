# Quickstart Guide

Use this checklist to run the template with Docker (recommended) and hit your first endpoint. Local Python instructions are included at the end as an alternative.

## 1. Clone the repo
```bash
git clone <your-fork-url> fastapi-template
cd fastapi-template/app_template
```

## 2. Prepare environment variables
```bash
cp .env.example .env
```
Key entries to review:
- `DATABASE_URL`: defaults to SQLite. Point to Postgres/MySQL when needed.
- `AUTH_MODE`: `built_in`, `disabled`, or `custom`.
- `TENANTS_ENABLED`: toggle the `/v1/tenants` router on or off.
- `RATE_LIMIT_DEFAULT_REQUESTS` / `RATE_LIMIT_DEFAULT_WINDOW_SECONDS`: defaults for opt-in rate limiting.
- `RETRY_MAX_ATTEMPTS`: default retry attempts for external calls.
- `CACHE_ENABLED` / `CACHE_DEFAULT_TTL_SECONDS`: enable caching helpers when desired.
- `AUTO_BUILD_PERMISSIONS` / `ENABLE_SEED_DATA`: keep them `true` for the first run.

## 3. Run with Docker Compose (recommended)
```bash
docker compose up --build
```
What happens:
1. The image is built from the included `Dockerfile`.
2. The container loads `.env` (thanks to `env_file`).
3. Uvicorn serves the API at `http://localhost:8000/`.

Stop the stack with `Ctrl+C` or:
```bash
docker compose down
```

## 4. Optional: run locally instead of Docker
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## 5. Verify the API
1. Visit `http://localhost:8000/` → `{"message":"Service Running"}`.
2. Visit `http://localhost:8000/docs` → Swagger UI should load without errors.

## 6. Authenticate (built-in mode)
```bash
curl -X POST http://localhost:8000/v1/auth/login \
  -d "username=admin@admin.com" \
  -d "password=admin"
```
Copy the `access_token` from the response.

## 7. Call a protected endpoint
```bash
curl -H "Authorization: Bearer TOKEN_HERE" \
     http://localhost:8000/v1/tenants
```

## 8. Create a tenant (write test)
```bash
curl -X POST http://localhost:8000/v1/tenants \
  -H "Authorization: Bearer TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"name":"Sample Tenant","address":"123 Demo St"}'
```

## 9. Explore other routers
- `/v1/users` lets you list/manage users (requires admin token). Try `curl -H "Authorization: Bearer TOKEN" http://localhost:8000/v1/users`.
- `/v1/roles` and `/v1/permissions` show how authorization rules are managed.
- `AuthContext` adapts behavior automatically if you switch `AUTH_MODE`.

Next steps: follow `docs/how_to_test.md` for a more detailed validation and `docs/customization-checklist.md` to adapt the template to your domain.
