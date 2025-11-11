# Customization Checklist

Use this list when adapting the template to a new project or domain.

## 1. Naming & Metadata
- [ ] Update `app_template/README_template.md` with the new project name and description.
- [ ] Adjust `APP_NAME` and `ENVIRONMENT` in `.env`.
- [ ] Review `docker-compose.yml` container names/ports.

## 2. Configuration & Secrets
- [ ] Set `DATABASE_URL` to the target database (Postgres/MySQL/Cloud).
- [ ] Rotate `SECRET_KEY`, token expiry, and logging levels.
- [ ] Decide `AUTH_MODE` (`built_in`, `disabled`, `custom`). Document your choice.
- [ ] If using external services, add new settings fields to `app/config.py`.
- [ ] Configure `EXTERNAL_DB_URL` (if you need a secondary DB) and use `app/database/external.py` to access it from routers/services.

## 3. Database & Migrations
- [ ] Remove placeholder data (Base Store, admin user) if not needed.
- [ ] Add new models in `app/database/models/` and run `alembic revision --autogenerate`.
- [ ] Clean `app/app-bkp.db` or mount a persistent volume suited for the new environment.

## 4. Routers & Schemas
- [ ] Duplicate `stores.py` as a baseline for new resources.
- [ ] Create Pydantic schemas in `app/schemas/`.
- [ ] Register the new router inside `app/main.py`.
- [ ] Tag routes thoughtfully so permissions make sense (`tags=['Inventory']`, etc.).

## 5. Auth & Permissions
- [ ] Confirm `build_permissions(app)` is still desired (or seed permissions manually).
- [ ] If `AUTH_MODE=custom`, provide your `AuthContext` dependency and update docs.
- [ ] Review roles/permissions seeds to ensure they align with the new domain.

## 6. Middleware & Logging
- [ ] Adjust logging formats or sinks in `app/logging.py`.
- [ ] Toggle/extend middleware in `app/main.py` (e.g., add tracing, rate limiting).

## 7. Documentation & Teaching Aids
- [ ] Update `docs/quickstart.md` with domain-specific examples.
- [ ] Expand the checklist if your team has extra compliance or deployment steps.
- [ ] Keep `suggestions.md` up to date as the template evolves.

## 8. Validation
- [ ] Run local tests or add new ones under `tests/` (not included by default).
- [ ] Verify seeds and migrations from a clean environment.
- [ ] Ensure Swagger reflects the new routes and their security requirements.
