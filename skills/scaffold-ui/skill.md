---
name: scaffold-ui
description: Next.js UI patterns for the scaffold tooling.
metadata:
  scope: tools/scaffold/ui
  auto_invoke: "Changing scaffold UI pages or layout"
---

# Scaffold UI

## When to use
- Editing UI flows for endpoints, models, schemas, settings, or external DBs.

## Project patterns
- Layout and sidebar live in `tools/scaffold/ui/components/scaffold-shell.tsx`.
- Global status messages use `ScaffoldStatusProvider` (`components/scaffold-status.tsx`).
- API calls go through `lib/scaffold-api.ts` via `fetchJson`.
- Pages live under `tools/scaffold/ui/app/`:
  - `/endpoints` lists specs and versions.
  - `/endpoints/editor` edits a specific spec.
  - `/models`, `/schemas`, `/settings`, `/external-dbs` are separate sections.
