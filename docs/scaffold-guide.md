# Scaffold Tool Guide

The scaffold tool lives in `tools/scaffold/` and is optional. It helps create, modify, and sync resources using JSON specs.

## 1) CLI usage
Run from the repo root:
```
python -m tools.scaffold create --spec specs/widgets.json
python -m tools.scaffold modify --spec specs/widgets.json
python -m tools.scaffold sync --spec specs/widgets.json
```

## 2) Spec format (JSON)
Each resource lives in `specs/<resource>.json`:
```
{
  "version": "v1",
  "name": "widget",
  "plural": "widgets",
  "table_name": "widgets",
  "tags": ["Widgets"],
  "auth_required": true,
  "tenant_scoped": false,
  "soft_delete": true,
  "pagination": true,
  "ordering": true,
  "fields": [
    { "name": "name", "type": "String", "nullable": false, "unique": false }
  ],
  "endpoints": {
    "list": true,
    "get": true,
    "create": true,
    "update": true,
    "delete": true
  },
  "tests": { "enabled": true }
}
```

## 3) Create vs Modify
- `create`: creates new files and updates the router registry.
- `modify`: overwrites existing files from the spec.

If a file is missing for `modify`, the command fails.

## 4) Sync behavior
`sync` compares the spec with generated code:
- If only the spec changed, code is regenerated.
- If only code changed, the spec is updated from code.
- If both changed, the spec wins and code is regenerated.

Metadata lives in `.scaffold/manifest.json`.

## 5) Router registry
Routers are tracked in `app/routers/registry_data.json`.
The runtime registry loads from this file, so UI tooling can edit it safely.
