# How To Test the Template (Docker Workflow)

Follow these steps exactly. You only need Docker and a terminal; no coding skills required.

## 1. Requirements
- Docker Desktop (Windows/macOS) or Docker Engine + Docker Compose v2 (Linux).
- Clone the repository and move to the template root (directory that contains `docker-compose.yml`).

## 2. Prepare environment variables
```bash
cp .env.example .env
```
Open `.env` and confirm:
- `AUTH_MODE=built_in`
- `AUTO_BUILD_PERMISSIONS=true`
- `ENABLE_SEED_DATA=true`

## 3. Build and start with Docker Compose
```bash
docker compose up --build
```
The first run may take a few minutes. When you see messages such as `Service Running` or `Finished initializing base data`, the API is ready.

## 4. Verify the API responds
1. Open `http://localhost:8000/` in your browser -> you should see `{"message":"Service Running"}`.
2. Visit `http://localhost:8000/docs` -> Swagger UI must load without errors.

## 5. Test the login (built_in mode)
In another terminal:
```bash
curl -X POST http://localhost:8000/auth/login \
  -d "username=admin@admin.com" \
  -d "password=admin"
```
Copy the `access_token` from the response.

## 6. Call a protected endpoint
```bash
curl -H "Authorization: Bearer TOKEN_HERE" \
     http://localhost:8000/tenants
```
Seeing a list (empty or containing `Base Tenant`) confirms authenticated reads work.

## 7. Create a resource
```bash
curl -X POST http://localhost:8000/tenants \
  -H "Authorization: Bearer TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"name":"Sample Tenant","address":"123 Demo St"}'
```
You should receive the new tenant in JSON form, proving writes and seeds are working.

## 8. List users (requires token)
```bash
curl -H "Authorization: Bearer TOKEN_HERE" \
     http://localhost:8000/users
```
Expect to see at least the admin user; this validates the `/users` CRUD.

## 9. Switch auth mode (optional)
1. Edit `.env` and set `AUTH_MODE=disabled`.
2. Restart the stack:
   ```bash
   docker compose down
   docker compose up --build
   ```
3. Hit `http://localhost:8000/tenants` without a token. If it works, the no-auth mode is enabled.

## 10. Stop containers
```bash
docker compose down
```

If every step completes without errors, the template has been verified end-to-end and is ready for customization.
