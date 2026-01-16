# AGENTS.md
A simple, open format for guiding coding agents on this project.

## Setup commands
- Install deps: `pip install -r requirements.txt` (API) / `cd tools/scaffold/ui && npm install` (Scaffold UI)
- Start dev server: `uvicorn app.main:app --reload --port 8000` (API) / `cd tools/scaffold/ui && npm run dev` (Scaffold UI)
- Run tests: `cd tools/scaffold/ui && npm test`

## Code style
- ESLint uses Next.js core-web-vitals + TypeScript presets (`tools/scaffold/ui/eslint.config.mjs`).
- TypeScript strict mode is enabled; `noEmit` and `moduleResolution: "bundler"` are set (`tools/scaffold/ui/tsconfig.json`).
- React uses the `react-jsx` transform (`tools/scaffold/ui/tsconfig.json`).

## Available Skills
| Skill | Description | Scope |
|-------|-------------|-------|
<!-- SKILLS-LIST-START -->
| [alembic-migrations](./skills/alembic-migrations/skill.md) | Alembic configuration and migration workflow for this repo. | app |
| [auth-permissions](./skills/auth-permissions/skill.md) | AuthContext behavior and permission auto-build rules. | app |
| [external-db-connections](./skills/external-db-connections/skill.md) | External DB registry and permissioned connection helpers. | app |
| [fastapi-core](./skills/fastapi-core/skill.md) | FastAPI router patterns and app wiring used in this project. | app |
| [logging-observability](./skills/logging-observability/skill.md) | Logging setup and request middleware used by the API. | app |
| [sqlalchemy-models](./skills/sqlalchemy-models/skill.md) | SQLAlchemy model conventions for this template. | app |
<!-- SKILLS-LIST-END -->

*Note: The table is empty for now. The sync script will populate it.*
