import os
import shutil
from pathlib import Path

AUTH_ROUTER_NAMES = ("tenants", "roles", "permissions", "users", "auth")
ALLOWED_ROUTER_FILES = {f"{name}.py" for name in AUTH_ROUTER_NAMES}
ALLOWED_ROUTER_FILES.add("__init__.py")

ALLOWED_LOGIC_FILES = set(ALLOWED_ROUTER_FILES)
ALLOWED_SCHEMA_FILES = {
    "__init__.py",
    "base_schema.py",
    "token_schemas.py",
    "tenants_schemas.py",
    "users_schemas.py",
}
ALLOWED_MODEL_FILES = {
    "__init__.py",
    "base_models.py",
    "tenants_models.py",
    "users_models.py",
}

PRUNE_TEST_FILES = {
    "test_customers_modules.py",
    "test_products_modules.py",
    "test_orders_modules.py",
    "test_order_items_modules.py",
    "test_nested_relations.py",
    "test_scaffold.py",
    "test_scaffold_api.py",
    "test_scaffold_external_dbs_api.py",
    "test_scaffold_settings_api.py",
}


def resolve_template_root(scaffold_root: Path) -> Path:
    env_root = os.getenv("SCAFFOLD_TEMPLATE_ROOT")
    candidate = Path(env_root).expanduser() if env_root else scaffold_root.parent.parent
    resolved = candidate.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Template root not found: {resolved}")
    return resolved


def create_project(template_root: Path, base_path: Path, name: str) -> Path:
    target_root = base_path.expanduser().resolve() / name
    if target_root.exists():
        raise FileExistsError(f"Target path already exists: {target_root}")
    target_root.parent.mkdir(parents=True, exist_ok=True)

    shutil.copytree(
        template_root,
        target_root,
        ignore=_ignore_template_entries,
    )
    _ensure_env_file(target_root)
    _prune_resources(target_root)
    return target_root


def _ignore_template_entries(directory: str, entries: list[str]) -> set[str]:
    ignored = set()
    base = Path(directory).name
    for entry in entries:
        if entry in {
            ".git",
            ".venv",
            ".scaffold",
            "__pycache__",
            "node_modules",
            "tools",
        }:
            ignored.add(entry)
            continue
        if entry in {"test.db", "working.md", ".env"}:
            ignored.add(entry)
            continue
        if base == "specs" and entry == "examples":
            ignored.add(entry)
    return ignored


def _ensure_env_file(project_root: Path) -> None:
    env_path = project_root / ".env"
    if env_path.exists():
        return
    example_path = project_root / ".env.example"
    if example_path.exists():
        env_path.write_text(example_path.read_text(encoding="utf-8"), encoding="utf-8")


def _prune_resources(project_root: Path) -> None:
    _prune_folder(project_root / "app" / "routers" / "v1", ALLOWED_ROUTER_FILES)
    _prune_folder(project_root / "app" / "endpoints_logic" / "v1", ALLOWED_LOGIC_FILES)
    _prune_folder(project_root / "app" / "schemas", ALLOWED_SCHEMA_FILES)
    _prune_folder(project_root / "app" / "database" / "models", ALLOWED_MODEL_FILES)
    _prune_tests(project_root / "tests")
    _prune_specs(project_root / "specs")
    _rewrite_models_init(project_root)
    _rewrite_registry(project_root)


def _prune_folder(folder: Path, allowed_files: set[str]) -> None:
    if not folder.exists():
        return
    for path in folder.iterdir():
        if path.is_dir():
            continue
        if path.name in allowed_files:
            continue
        path.unlink()


def _prune_tests(tests_root: Path) -> None:
    if not tests_root.exists():
        return
    for name in PRUNE_TEST_FILES:
        path = tests_root / name
        if path.exists():
            path.unlink()


def _prune_specs(specs_root: Path) -> None:
    if not specs_root.exists():
        specs_root.mkdir(parents=True, exist_ok=True)
        return
    examples = specs_root / "examples"
    if examples.exists():
        shutil.rmtree(examples)


def _rewrite_models_init(project_root: Path) -> None:
    path = project_root / "app" / "database" / "models" / "__init__.py"
    content = "\n".join(
        [
            "from .base_models import Base",
            "from .tenants_models import Tenants",
            "from .users_models import Users, Roles, Permissions, UserRoles, RolePermissions, UserTenants",
            "",
            "__all__ = [\"Base\", \"Tenants\", \"Users\", \"Roles\", \"Permissions\", \"UserRoles\", \"RolePermissions\", \"UserTenants\"]",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _rewrite_registry(project_root: Path) -> None:
    path = project_root / "app" / "routers" / "registry_data.json"
    entries = [
        {
            "name": "tenants",
            "module": "app.routers.v1.tenants",
            "requires_auth": False,
            "requires_tenants": True,
            "enabled": True,
        },
        {
            "name": "roles",
            "module": "app.routers.v1.roles",
            "requires_auth": True,
            "requires_tenants": False,
            "enabled": True,
        },
        {
            "name": "permissions",
            "module": "app.routers.v1.permissions",
            "requires_auth": True,
            "requires_tenants": False,
            "enabled": True,
        },
        {
            "name": "users",
            "module": "app.routers.v1.users",
            "requires_auth": True,
            "requires_tenants": False,
            "enabled": True,
        },
        {
            "name": "auth",
            "module": "app.routers.v1.auth",
            "requires_auth": True,
            "requires_tenants": False,
            "enabled": True,
        },
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{\n  \"v1\": " + _format_entries(entries) + "\n}\n", encoding="utf-8")


def _format_entries(entries: list[dict]) -> str:
    lines = ["["]
    for entry in entries:
        lines.append("    {")
        for key, value in entry.items():
            value_text = "true" if value is True else "false" if value is False else f"\"{value}\""
            lines.append(f"      \"{key}\": {value_text},")
        lines[-1] = lines[-1].rstrip(",")
        lines.append("    },")
    if lines[-1].endswith(","):
        lines[-1] = lines[-1].rstrip(",")
    lines.append("  ]")
    return "\n".join(lines)
