# Scaffold UI Guide

This UI is an optional tool to manage scaffold specs and trigger create/modify/sync/remove actions.
It runs separately from the main FastAPI app.

## 1) Start the API
From the repo root:
```
python -m tools.scaffold.api
```
Default URL: `http://127.0.0.1:8001`

## 2) Start the UI
```
cd tools/scaffold/ui
npm install
npm run dev
```
Default URL: `http://127.0.0.1:3000`
General settings screen: `http://127.0.0.1:3000/settings`

## 2.1) Docker Compose
From the repo root:
```
docker compose up scaffold-api scaffold-ui
```
UI: `http://127.0.0.1:3000`
API: `http://127.0.0.1:8001`

## 3) Configure the API URL (optional)
Set in `tools/scaffold/ui/.env.local`:
```
NEXT_PUBLIC_SCAFFOLD_API_URL=http://127.0.0.1:8001
```

## 4) API endpoints used by the UI
- `GET /specs`
- `GET /specs/read?path=specs/example.json`
- `POST /specs/write`
- `GET /settings`
- `POST /settings`
- `POST /scaffold/create`
- `POST /scaffold/modify`
- `POST /scaffold/sync-to-code`
- `POST /scaffold/sync-from-code`
- `POST /scaffold/remove`
