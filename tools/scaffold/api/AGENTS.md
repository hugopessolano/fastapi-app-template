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
| [scaffold-api](./skills/scaffold-api/skill.md) | Scaffold API endpoints for specs, settings, and external DBs. | tools/scaffold/api |
<!-- SKILLS-LIST-END -->

*Note: The table is empty for now. The sync script will populate it.*
