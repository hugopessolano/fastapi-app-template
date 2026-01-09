import importlib
import json
from pathlib import Path
from typing import Iterable, List

from fastapi import APIRouter


def get_router_modules(auth_mode: str | None, tenants_enabled: bool = True) -> List[str]:
    mode = _normalize_auth_mode(auth_mode)
    registry = _load_registry_data()
    modules = []
    for entry in registry.get("v1", []):
        if not entry.get("enabled", True):
            continue
        if entry.get("requires_tenants") and not tenants_enabled:
            continue
        if entry.get("requires_auth") and mode == "disabled":
            continue
        modules.append(entry["module"])
    return modules


def load_routers(module_paths: Iterable[str]) -> List[APIRouter]:
    routers = []
    for module_path in module_paths:
        module = importlib.import_module(module_path)
        routers.append(module.router)
    return routers


def _normalize_auth_mode(auth_mode: str | None) -> str:
    return (auth_mode or "built_in").strip().lower()


def _load_registry_data() -> dict:
    path = Path(__file__).with_name("registry_data.json")
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
