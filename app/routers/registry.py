import importlib
from typing import Iterable, List

from fastapi import APIRouter


def get_router_modules(auth_mode: str | None) -> List[str]:
    mode = _normalize_auth_mode(auth_mode)
    modules = ["app.routers.v1.tenants"]
    if mode != "disabled":
        modules.extend(
            [
                "app.routers.v1.roles",
                "app.routers.v1.permissions",
                "app.routers.v1.users",
                "app.routers.v1.auth",
            ]
        )
    return modules


def load_routers(module_paths: Iterable[str]) -> List[APIRouter]:
    routers = []
    for module_path in module_paths:
        module = importlib.import_module(module_path)
        routers.append(module.router)
    return routers


def _normalize_auth_mode(auth_mode: str | None) -> str:
    return (auth_mode or "built_in").strip().lower()
