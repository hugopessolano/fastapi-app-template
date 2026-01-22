import json
import os
import re
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

from app.database.external_registry import ExternalConnectionError, parse_permissions

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
from tools.scaffold.projects import (
    browse_projects,
    get_project,
    prune_missing_projects,
    register_project,
    resolve_projects_path,
)
from tools.scaffold.factory import create_project, resolve_template_root


class SpecWriteRequest(BaseModel):
    path: str
    spec: dict[str, Any]


class SpecPathRequest(BaseModel):
    spec_path: str
    delete_spec: bool = False


class SettingsRequest(BaseModel):
    settings: dict[str, Any]


class ExternalDbRequest(BaseModel):
    name: str
    url: str
    permissions: list[str] | str | None = None


class ExternalDbDeleteRequest(BaseModel):
    name: str


class ExternalDbTestRequest(BaseModel):
    url: str


class ProjectOpenRequest(BaseModel):
    path: str
    name: str | None = None


class ProjectCreateRequest(BaseModel):
    base_path: str
    name: str


EXTERNAL_DB_PREFIX = "EXTERNAL_DB_"
EXTERNAL_DB_URL_SUFFIX = "_URL"
EXTERNAL_DB_PERMISSIONS_SUFFIX = "_PERMISSIONS"
LEGACY_EXTERNAL_URL_KEY = "EXTERNAL_DB_URL"
LEGACY_EXTERNAL_PERMISSIONS_KEY = "EXTERNAL_DB_PERMISSIONS"
EXTERNAL_ALLOWED_BACKENDS = {"sqlite", "postgresql", "mysql", "mariadb"}
EXTERNAL_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")
PROJECT_HEADER = "X-Scaffold-Project"


def create_api_app(scaffold_root: Path) -> FastAPI:
    app = FastAPI(title="Scaffold API")
    app.state.scaffold_root = scaffold_root
    prune_missing_projects(scaffold_root)
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

    @app.get("/projects")
    def list_projects() -> dict[str, list[dict[str, Any]]]:
        return {"projects": prune_missing_projects(scaffold_root)}

    @app.get("/projects/browse")
    def browse_project_dirs(path: str | None = None) -> dict[str, Any]:
        try:
            return browse_projects(scaffold_root, path)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except NotADirectoryError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/projects/open")
    def open_project(payload: ProjectOpenRequest) -> dict[str, dict[str, Any]]:
        try:
            root, resolved = resolve_projects_path(scaffold_root, payload.path)
            if not resolved.is_dir():
                raise HTTPException(status_code=400, detail="Project path is not a folder.")
            project = register_project(scaffold_root, payload.name, str(resolved))
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"project": project}

    @app.post("/projects/create")
    def create_project_endpoint(payload: ProjectCreateRequest) -> dict[str, dict[str, Any]]:
        try:
            _, base_path = resolve_projects_path(scaffold_root, payload.base_path)
            if not base_path.is_dir():
                raise HTTPException(status_code=400, detail="Base path is not a folder.")
            template_root = resolve_template_root(scaffold_root)
            project_root = create_project(
                template_root,
                base_path,
                payload.name,
            )
        except FileExistsError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        project = register_project(scaffold_root, payload.name, str(project_root))
        return {"project": project}

    @app.get("/specs")
    def list_specs(request: Request) -> dict[str, list[dict[str, str]]]:
        root = require_project_root(request)
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
    def read_spec(request: Request, path: str) -> dict[str, Any]:
        root = require_project_root(request)
        spec_path = resolve_path(root, path)
        if not spec_path.exists():
            raise HTTPException(status_code=404, detail="Spec not found")
        return {"spec": json.loads(spec_path.read_text(encoding="utf-8-sig"))}

    @app.post("/specs/write")
    def write_spec(request: Request, payload: SpecWriteRequest) -> dict[str, str]:
        root = require_project_root(request)
        spec_path = resolve_path(root, payload.path)
        try:
            validate_spec(payload.spec)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        spec_path.write_text(json.dumps(payload.spec, indent=2), encoding="utf-8")
        return {"status": "ok", "path": relative_to_root(root, spec_path)}

    @app.post("/scaffold/create")
    def scaffold_create(request: Request, payload: SpecPathRequest) -> dict[str, str]:
        root = require_project_root(request)
        return scaffold_action(root, payload.spec_path, create_resource)

    @app.post("/scaffold/modify")
    def scaffold_modify(request: Request, payload: SpecPathRequest) -> dict[str, str]:
        root = require_project_root(request)
        return scaffold_action(root, payload.spec_path, modify_resource)

    @app.post("/scaffold/sync")
    def scaffold_sync(request: Request, payload: SpecPathRequest) -> dict[str, str]:
        root = require_project_root(request)
        return scaffold_action(root, payload.spec_path, sync_resource)

    @app.post("/scaffold/sync-to-code")
    def scaffold_sync_to_code(request: Request, payload: SpecPathRequest) -> dict[str, str]:
        root = require_project_root(request)
        return scaffold_action(root, payload.spec_path, sync_resource_to_code)

    @app.post("/scaffold/sync-from-code")
    def scaffold_sync_from_code(request: Request, payload: SpecPathRequest) -> dict[str, str]:
        root = require_project_root(request)
        return scaffold_action(root, payload.spec_path, sync_resource_from_code)

    @app.post("/scaffold/remove")
    def scaffold_remove(request: Request, payload: SpecPathRequest) -> dict[str, str]:
        root = require_project_root(request)
        return scaffold_action(
            root,
            payload.spec_path,
            lambda root_path, spec_path: remove_resource(
                root_path, spec_path, delete_spec=payload.delete_spec
            ),
        )

    @app.get("/settings")
    def read_settings(request: Request) -> dict[str, dict[str, str]]:
        root = require_project_root(request)
        env_path = root / ".env"
        settings = _load_env_settings(env_path)
        filtered = {key: value for key, value in settings.items() if key in SETTINGS_KEYS}
        return {"settings": filtered}

    @app.post("/settings")
    def write_settings(request: Request, payload: SettingsRequest) -> dict[str, dict[str, str]]:
        root = require_project_root(request)
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

    @app.get("/external-dbs")
    def read_external_dbs(request: Request) -> dict[str, list[dict[str, Any]]]:
        root = require_project_root(request)
        env_path = root / ".env"
        settings = _load_env_settings(env_path)
        return {"connections": _parse_external_connections(settings)}

    @app.post("/external-dbs")
    def upsert_external_db(
        request: Request, payload: ExternalDbRequest
    ) -> dict[str, list[dict[str, Any]]]:
        root = require_project_root(request)
        env_path = root / ".env"
        settings = _load_env_settings(env_path)
        name = _normalize_external_name(payload.name)
        url = _validate_external_url(payload.url)
        permission_value, _ = _normalize_external_permissions(payload.permissions)
        url_key, perm_key = _resolve_external_keys(name, settings)
        _write_env_settings(env_path, {url_key: url, perm_key: permission_value})
        return {"connections": _parse_external_connections(_load_env_settings(env_path))}

    @app.post("/external-dbs/delete")
    def delete_external_db(
        request: Request, payload: ExternalDbDeleteRequest
    ) -> dict[str, list[dict[str, Any]]]:
        root = require_project_root(request)
        env_path = root / ".env"
        settings = _load_env_settings(env_path)
        name = _normalize_external_name(payload.name)
        url_key, perm_key = _resolve_external_keys(name, settings)
        _remove_env_keys(env_path, {url_key, perm_key})
        return {"connections": _parse_external_connections(_load_env_settings(env_path))}

    @app.post("/external-dbs/test")
    def test_external_db(request: Request, payload: ExternalDbTestRequest) -> dict[str, str]:
        url = _validate_external_url(payload.url)
        try:
            engine = create_engine(url, **_external_engine_kwargs(url))
            with engine.connect():
                pass
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"status": "ok"}

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


def require_project_root(request: Request) -> Path:
    project_id = request.headers.get(PROJECT_HEADER)
    if not project_id:
        raise HTTPException(status_code=400, detail="Missing project header.")
    scaffold_root = request.app.state.scaffold_root
    project = get_project(scaffold_root, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return Path(project["path"]).resolve()


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


def _remove_env_keys(path: Path, keys: set[str]) -> None:
    if not path.exists():
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    kept: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            kept.append(line)
            continue
        key = line.split("=", 1)[0].strip()
        if key in keys:
            continue
        kept.append(line)
    content = "\n".join(kept)
    if content and not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8")


def _normalize_external_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail="External DB name is required.")
    if not EXTERNAL_NAME_PATTERN.fullmatch(cleaned):
        raise HTTPException(
            status_code=400,
            detail="External DB name must use letters, numbers, or underscores.",
        )
    return cleaned.lower()


def _validate_external_url(url: str) -> str:
    cleaned = url.strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail="External DB URL is required.")
    try:
        backend = make_url(cleaned).get_backend_name()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid database URL.") from exc
    if backend not in EXTERNAL_ALLOWED_BACKENDS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported database engine. Use sqlite, postgresql, or mysql/mariadb.",
        )
    return cleaned


def _normalize_external_permissions(
    permissions: list[str] | str | None,
) -> tuple[str, list[str]]:
    if permissions is None:
        raw = ""
    elif isinstance(permissions, list):
        raw = ",".join(permissions)
    else:
        raw = str(permissions)
    try:
        parsed = parse_permissions(raw)
    except ExternalConnectionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return raw, sorted(parsed)


def _resolve_external_keys(name: str, settings: dict[str, str]) -> tuple[str, str]:
    upper = name.upper()
    named_url_key = f"{EXTERNAL_DB_PREFIX}{upper}{EXTERNAL_DB_URL_SUFFIX}"
    named_perm_key = f"{EXTERNAL_DB_PREFIX}{upper}{EXTERNAL_DB_PERMISSIONS_SUFFIX}"
    if name == "default" and LEGACY_EXTERNAL_URL_KEY in settings and named_url_key not in settings:
        return LEGACY_EXTERNAL_URL_KEY, LEGACY_EXTERNAL_PERMISSIONS_KEY
    return named_url_key, named_perm_key


def _safe_backend(url: str) -> str:
    try:
        return make_url(url).get_backend_name()
    except Exception:
        return "unknown"


def _external_engine_kwargs(url: str) -> dict[str, Any]:
    try:
        backend = make_url(url).get_backend_name()
    except Exception:
        return {}
    if backend == "sqlite":
        return {"connect_args": {"check_same_thread": False, "timeout": 30}}
    return {}


def _parse_external_connections(settings: dict[str, str]) -> list[dict[str, Any]]:
    connections: dict[str, dict[str, Any]] = {}
    for key, value in settings.items():
        if key == LEGACY_EXTERNAL_URL_KEY:
            continue
        if not key.startswith(EXTERNAL_DB_PREFIX) or not key.endswith(EXTERNAL_DB_URL_SUFFIX):
            continue
        name = key[len(EXTERNAL_DB_PREFIX) : -len(EXTERNAL_DB_URL_SUFFIX)].strip().lower()
        if not name:
            continue
        url = value.strip()
        if not url:
            continue
        perm_key = f"{EXTERNAL_DB_PREFIX}{name.upper()}{EXTERNAL_DB_PERMISSIONS_SUFFIX}"
        _, permissions = _normalize_external_permissions(settings.get(perm_key, ""))
        connections[name] = {
            "name": name,
            "url": url,
            "permissions": permissions,
            "backend": _safe_backend(url),
            "source": "named",
        }

    legacy_url = settings.get(LEGACY_EXTERNAL_URL_KEY, "").strip()
    if legacy_url and "default" not in connections:
        _, permissions = _normalize_external_permissions(
            settings.get(LEGACY_EXTERNAL_PERMISSIONS_KEY, "")
        )
        connections["default"] = {
            "name": "default",
            "url": legacy_url,
            "permissions": permissions,
            "backend": _safe_backend(legacy_url),
            "source": "legacy",
        }

    return [connections[name] for name in sorted(connections)]
