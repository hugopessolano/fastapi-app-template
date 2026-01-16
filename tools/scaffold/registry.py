import json
from pathlib import Path

from tools.scaffold.spec import ResourceSpec


def registry_path(root: Path) -> Path:
    return root / "app" / "routers" / "registry_data.json"


def load_registry(root: Path) -> dict:
    path = registry_path(root)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_registry(root: Path, data: dict) -> None:
    path = registry_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def ensure_registry_entry(root: Path, spec: ResourceSpec) -> None:
    data = load_registry(root)
    version = spec.version
    data.setdefault(version, [])
    module = f"app.routers.{spec.version}.{spec.plural}"
    entry = next((item for item in data[version] if item.get("name") == spec.plural), None)
    if entry:
        entry["module"] = module
        entry["requires_auth"] = spec.auth_required
        entry["requires_tenants"] = spec.tenant_scoped
        if "enabled" not in entry:
            entry["enabled"] = True
    else:
        data[version].append(
            {
                "name": spec.plural,
                "module": module,
                "requires_auth": spec.auth_required,
                "requires_tenants": spec.tenant_scoped,
                "enabled": True,
            }
        )
    save_registry(root, data)


def remove_registry_entry(root: Path, spec: ResourceSpec) -> None:
    data = load_registry(root)
    version = spec.version
    if version not in data:
        return
    data[version] = [item for item in data[version] if item.get("name") != spec.plural]
    if not data[version]:
        data.pop(version)
    save_registry(root, data)
