import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

SETTINGS_KEYS = {
    "APP_NAME",
    "ENVIRONMENT",
    "DATABASE_URL",
    "EXTERNAL_DB_URL",
    "AUTH_MODE",
    "TENANTS_ENABLED",
    "AUTO_BUILD_PERMISSIONS",
    "ENABLE_SEED_DATA",
    "SEED_CHECK_EXISTING_USERS",
    "RATE_LIMIT_DEFAULT_REQUESTS",
    "RATE_LIMIT_DEFAULT_WINDOW_SECONDS",
    "RETRY_MAX_ATTEMPTS",
    "RETRY_BASE_DELAY_SECONDS",
    "RETRY_MAX_DELAY_SECONDS",
    "RETRY_JITTER_SECONDS",
    "CACHE_ENABLED",
    "CACHE_DEFAULT_TTL_SECONDS",
    "LOGGING_STDOUT_LEVEL",
    "LOGGING_DB_LEVEL",
}

from tools.scaffold.scaffold import (
    create_resource,
    modify_resource,
    remove_resource,
    sync_resource,
    sync_resource_from_code,
    sync_resource_to_code,
)
from tools.scaffold.spec import validate_spec


class SpecWriteRequest(BaseModel):
    path: str
    spec: dict[str, Any]


class SpecPathRequest(BaseModel):
    spec_path: str
    delete_spec: bool = False


class SettingsRequest(BaseModel):
    settings: dict[str, Any]


def create_api_app(root: Path) -> FastAPI:
    app = FastAPI(title="Scaffold API")
    app.state.root = root
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/specs")
    def list_specs() -> dict[str, list[dict[str, str]]]:
        specs_root = root / "specs"
        if not specs_root.exists():
            return {"specs": []}
        specs = []
        for path in sorted(specs_root.rglob("*.json")):
            rel = path.relative_to(root)
            name = path.stem
            try:
                data = json.loads(path.read_text(encoding="utf-8-sig"))
                name = data.get("name", name)
            except json.JSONDecodeError:
                pass
            specs.append({"path": str(rel), "name": name})
        return {"specs": specs}

    @app.get("/specs/read")
    def read_spec(path: str) -> dict[str, Any]:
        spec_path = resolve_path(root, path)
        if not spec_path.exists():
            raise HTTPException(status_code=404, detail="Spec not found")
        return {"spec": json.loads(spec_path.read_text(encoding="utf-8-sig"))}

    @app.post("/specs/write")
    def write_spec(payload: SpecWriteRequest) -> dict[str, str]:
        spec_path = resolve_path(root, payload.path)
        try:
            validate_spec(payload.spec)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        spec_path.write_text(json.dumps(payload.spec, indent=2), encoding="utf-8")
        return {"status": "ok", "path": relative_to_root(root, spec_path)}

    @app.post("/scaffold/create")
    def scaffold_create(payload: SpecPathRequest) -> dict[str, str]:
        return scaffold_action(root, payload.spec_path, create_resource)

    @app.post("/scaffold/modify")
    def scaffold_modify(payload: SpecPathRequest) -> dict[str, str]:
        return scaffold_action(root, payload.spec_path, modify_resource)

    @app.post("/scaffold/sync")
    def scaffold_sync(payload: SpecPathRequest) -> dict[str, str]:
        return scaffold_action(root, payload.spec_path, sync_resource)

    @app.post("/scaffold/sync-to-code")
    def scaffold_sync_to_code(payload: SpecPathRequest) -> dict[str, str]:
        return scaffold_action(root, payload.spec_path, sync_resource_to_code)

    @app.post("/scaffold/sync-from-code")
    def scaffold_sync_from_code(payload: SpecPathRequest) -> dict[str, str]:
        return scaffold_action(root, payload.spec_path, sync_resource_from_code)

    @app.post("/scaffold/remove")
    def scaffold_remove(payload: SpecPathRequest) -> dict[str, str]:
        return scaffold_action(
            root,
            payload.spec_path,
            lambda root_path, spec_path: remove_resource(
                root_path, spec_path, delete_spec=payload.delete_spec
            ),
        )

    @app.get("/settings")
    def read_settings() -> dict[str, dict[str, str]]:
        env_path = root / ".env"
        settings = _load_env_settings(env_path)
        filtered = {key: value for key, value in settings.items() if key in SETTINGS_KEYS}
        return {"settings": filtered}

    @app.post("/settings")
    def write_settings(payload: SettingsRequest) -> dict[str, dict[str, str]]:
        updates = payload.settings
        unknown = [key for key in updates if key not in SETTINGS_KEYS]
        if unknown:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown settings keys: {', '.join(sorted(unknown))}",
            )
        env_path = root / ".env"
        normalized = {key: _normalize_setting_value(value) for key, value in updates.items()}
        _write_env_settings(env_path, normalized)
        return {"settings": normalized}

    return app


def resolve_path(root: Path, path: str) -> Path:
    candidate = Path(path)
    resolved = (root / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
    root_resolved = root.resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid path") from exc
    return resolved


def scaffold_action(root: Path, spec_path: str, action) -> dict[str, str]:
    resolved = resolve_path(root, spec_path)
    try:
        action(root, resolved)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "ok", "spec_path": relative_to_root(root, resolved)}


def relative_to_root(root: Path, path: Path) -> str:
    root_str = os.path.normcase(str(root.resolve()))
    path_str = os.path.normcase(str(path.resolve()))
    return os.path.relpath(path_str, root_str)


def _normalize_setting_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _load_env_settings(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    settings: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        settings[key.strip()] = value.strip()
    return settings


def _write_env_settings(path: Path, updates: dict[str, str]) -> None:
    lines = []
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()

    updated_keys = set()
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            continue
        key = line.split("=", 1)[0].strip()
        if key in updates:
            lines[idx] = f"{key}={updates[key]}"
            updated_keys.add(key)

    for key, value in updates.items():
        if key not in updated_keys:
            lines.append(f"{key}={value}")

    content = "\n".join(lines)
    if content and not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8")
