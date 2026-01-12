from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Generator, Iterable, Mapping, Optional, Set

from dotenv import dotenv_values
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import sessionmaker

ALLOWED_PERMISSIONS = {"create", "read", "update", "delete"}
LEGACY_ENV_KEY = "EXTERNAL_DB_URL"
LEGACY_NAME = "default"


class ExternalConnectionError(RuntimeError):
    pass


class ExternalPermissionError(RuntimeError):
    pass


@dataclass(frozen=True)
class ExternalConnection:
    name: str
    url: str
    permissions: Set[str]
    engine: Engine
    session_factory: sessionmaker


def parse_permissions(value: Optional[str]) -> Set[str]:
    if not value:
        return set(ALLOWED_PERMISSIONS)
    normalized = value.strip().lower()
    if normalized in {"all", "*", "inherit", "db"}:
        return set(ALLOWED_PERMISSIONS)
    permissions = {token.strip().lower() for token in value.split(",") if token.strip()}
    unknown = permissions - ALLOWED_PERMISSIONS
    if unknown:
        raise ExternalConnectionError(
            f"Invalid permissions: {', '.join(sorted(unknown))}. "
            f"Allowed: {', '.join(sorted(ALLOWED_PERMISSIONS))}."
        )
    if not permissions:
        return set(ALLOWED_PERMISSIONS)
    return permissions


def _build_engine_kwargs(url: str) -> dict:
    connect_args = {}
    try:
        backend = make_url(url).get_backend_name()
        if backend == "sqlite":
            connect_args = {"check_same_thread": False, "timeout": 30}
    except Exception:
        connect_args = {}
    return {"connect_args": connect_args} if connect_args else {}


def parse_external_configs(environ: Mapping[str, str]) -> Dict[str, Dict[str, object]]:
    configs: Dict[str, Dict[str, object]] = {}
    upper_env = {key.upper(): value for key, value in environ.items()}
    for key, value in upper_env.items():
        if not key.startswith("EXTERNAL_DB_") or not key.endswith("_URL"):
            continue
        name = key[len("EXTERNAL_DB_") : -len("_URL")].strip().lower()
        if not name:
            continue
        url = (value or "").strip()
        if not url:
            continue
        perm_key = f"EXTERNAL_DB_{name.upper()}_PERMISSIONS"
        permissions = parse_permissions(upper_env.get(perm_key))
        configs[name] = {"url": url, "permissions": permissions}

    legacy_url = (upper_env.get(LEGACY_ENV_KEY) or "").strip()
    if legacy_url and LEGACY_NAME not in configs:
        configs[LEGACY_NAME] = {
            "url": legacy_url,
            "permissions": parse_permissions(upper_env.get("EXTERNAL_DB_PERMISSIONS")),
        }

    return configs


def _collect_env(environ: Optional[Mapping[str, str]]) -> Dict[str, str]:
    if environ is not None:
        return {key: value for key, value in environ.items() if value is not None}
    values = {key: value for key, value in dotenv_values(".env").items() if value is not None}
    values.update(os.environ)
    return {key: value for key, value in values.items() if value is not None}


def build_external_registry(
    environ: Optional[Mapping[str, str]] = None,
) -> Dict[str, ExternalConnection]:
    env = _collect_env(environ)
    configs = parse_external_configs(env)
    registry: Dict[str, ExternalConnection] = {}
    for name, config in configs.items():
        url = str(config["url"])
        permissions = set(config["permissions"])
        engine = create_engine(url, **_build_engine_kwargs(url))
        session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        registry[name] = ExternalConnection(
            name=name,
            url=url,
            permissions=permissions,
            engine=engine,
            session_factory=session_factory,
        )
    return registry


@lru_cache
def get_external_registry() -> Dict[str, ExternalConnection]:
    return build_external_registry()


def get_external_connection(name: str) -> ExternalConnection:
    registry = get_external_registry()
    key = (name or "").strip().lower()
    if key in registry:
        return registry[key]
    raise ExternalConnectionError(f"External connection '{name}' is not configured.")


def require_external_permissions(name: str, permissions: Iterable[str]) -> None:
    connection = get_external_connection(name)
    required = {perm.strip().lower() for perm in permissions if perm.strip()}
    if not required:
        return
    missing = required - connection.permissions
    if missing:
        raise ExternalPermissionError(
            f"External connection '{name}' lacks permissions: {', '.join(sorted(missing))}."
        )


def external_db_dependency(
    name: str, required_permissions: Optional[Iterable[str]] = None
):
    def _get_db() -> Generator:
        if required_permissions:
            require_external_permissions(name, required_permissions)
        connection = get_external_connection(name)
        db = connection.session_factory()
        try:
            yield db
        finally:
            db.close()

    return _get_db
