---
name: logging-observability
description: Logging setup and request middleware used by the API.
metadata:
  scope: app
  auto_invoke: "Logging changes or adding new routers"
---

# Logging and Observability

## When to use
- Adding logging to new endpoints or changing log sinks.

## Project patterns
- `app/logging.py` configures Loguru with stdout + SQLite sink.
  - SQLite sink writes structured JSON payloads into a `logs` table.
  - Log levels are driven by settings (`LOGGING_STDOUT_LEVEL`, `LOGGING_DB_LEVEL`).
- `child_logger` is the standard logger used by endpoints and middleware.
- `app/middleware.py` logs request metadata and adds `X-User-ID` when a token is present.
