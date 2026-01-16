---
name: testing
description: Test setup for backend (unittest) and scaffold UI (vitest).
metadata:
  scope: root
  auto_invoke: "Adding or updating tests"
---

# Testing

## When to use
- Adding tests or validating changes.

## Project patterns
- Backend tests live in `tests/` and use `unittest`.
- Scaffold UI tests live in `tools/scaffold/ui/app/__tests__` and use `vitest` + Testing Library.
- UI tests typically stub `fetch` and render with `ScaffoldStatusProvider`.

## Commands
- UI tests: `cd tools/scaffold/ui && npm test`
- API tests: `python -m unittest`
