import json
from pathlib import Path

from tools.scaffold.inspect_code import parse_endpoints_from_router, parse_fields_from_model
from tools.scaffold.manifest import hash_file, hash_text, load_manifest, save_manifest
from tools.scaffold.registry import ensure_registry_entry
from tools.scaffold.spec import ResourceSpec, load_spec
from tools.scaffold.templates import logic_template, model_template, router_template, schema_template, test_template


def create_resource(root: Path, spec_path: Path) -> None:
    spec = load_spec(spec_path)
    paths = build_paths(root, spec)
    for path in paths.values():
        if path.exists():
            raise FileExistsError(f"{path} already exists.")
    write_scaffold_files(spec, paths)
    update_models_init(root, spec)
    ensure_registry_entry(root, spec)
    update_manifest(root, spec, spec_path, paths)


def modify_resource(root: Path, spec_path: Path) -> None:
    spec = load_spec(spec_path)
    paths = build_paths(root, spec)
    for path in paths.values():
        if not path.exists():
            raise FileNotFoundError(f"{path} does not exist.")
    write_scaffold_files(spec, paths)
    update_models_init(root, spec)
    ensure_registry_entry(root, spec)
    update_manifest(root, spec, spec_path, paths)


def sync_resource(root: Path, spec_path: Path) -> None:
    spec = load_spec(spec_path)
    paths = build_paths(root, spec)
    manifest = load_manifest(root)
    resource_key = spec.plural
    record = manifest.get("resources", {}).get(resource_key)

    spec_hash = hash_spec(spec_path)
    file_hashes = {str(path): hash_file(path) for path in paths.values() if path.exists()}
    code_changed = record is None or record.get("files") != file_hashes
    spec_changed = record is None or record.get("spec_hash") != spec_hash

    if spec_changed and not code_changed:
        write_scaffold_files(spec, paths)
        update_models_init(root, spec)
        ensure_registry_entry(root, spec)
        update_manifest(root, spec, spec_path, paths)
        return

    if code_changed and not spec_changed:
        sync_spec_from_code(spec, spec_path, paths)
        update_manifest(root, spec, spec_path, paths)
        return

    if spec_changed and code_changed:
        write_scaffold_files(spec, paths)
        update_models_init(root, spec)
        ensure_registry_entry(root, spec)
        update_manifest(root, spec, spec_path, paths)
        return

    update_manifest(root, spec, spec_path, paths)


def build_paths(root: Path, spec: ResourceSpec) -> dict[str, Path]:
    return {
        "model": root / "app" / "database" / "models" / f"{spec.plural}_models.py",
        "schema": root / "app" / "schemas" / f"{spec.plural}_schemas.py",
        "logic": root / "app" / "endpoints_logic" / spec.version / f"{spec.plural}.py",
        "router": root / "app" / "routers" / spec.version / f"{spec.plural}.py",
        "test": root / "tests" / f"test_{spec.plural}_modules.py",
    }


def write_scaffold_files(spec: ResourceSpec, paths: dict[str, Path]) -> None:
    write_file(paths["model"], model_template(spec))
    write_file(paths["schema"], schema_template(spec))
    write_file(paths["logic"], logic_template(spec))
    write_file(paths["router"], router_template(spec))
    if spec.tests.enabled:
        write_file(paths["test"], test_template(spec))


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def update_models_init(root: Path, spec: ResourceSpec) -> None:
    path = root / "app" / "database" / "models" / "__init__.py"
    model_import = f"from .{spec.plural}_models import {spec.model_class}"
    if path.exists():
        content = path.read_text(encoding="utf-8")
    else:
        content = "from .base_models import Base\n\n__all__ = [\"Base\"]\n"

    if model_import not in content:
        content = content.rstrip() + "\n" + model_import + "\n"

    if "__all__" in content:
        content = update_all_list(content, spec.model_class)
    else:
        content = content.rstrip() + f"\n__all__ = [\"Base\", \"{spec.model_class}\"]\n"

    path.write_text(content, encoding="utf-8")


def update_all_list(content: str, item: str) -> str:
    prefix = "__all__ = ["
    if prefix not in content:
        return content
    start = content.index(prefix) + len(prefix)
    end = content.index("]", start)
    entries = [
        entry.strip().strip("\"'")
        for entry in content[start:end].split(",")
        if entry.strip()
    ]
    if item not in entries:
        entries.append(item)
    updated = prefix + ", ".join(f"\"{entry}\"" for entry in entries) + "]"
    return content[: content.index(prefix)] + updated + content[end + 1 :]


def hash_spec(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    return hash_text(json.dumps(data, sort_keys=True))


def update_manifest(root: Path, spec: ResourceSpec, spec_path: Path, paths: dict[str, Path]) -> None:
    manifest = load_manifest(root)
    resource_key = spec.plural
    manifest.setdefault("resources", {})
    manifest["resources"][resource_key] = {
        "spec_path": str(spec_path),
        "spec_hash": hash_spec(spec_path),
        "files": {str(path): hash_file(path) for path in paths.values() if path.exists()},
    }
    save_manifest(root, manifest)


def sync_spec_from_code(spec: ResourceSpec, spec_path: Path, paths: dict[str, Path]) -> None:
    fields = parse_fields_from_model(paths["model"], spec.tenant_scoped)
    endpoints = parse_endpoints_from_router(paths["router"])
    data = json.loads(spec_path.read_text(encoding="utf-8"))
    data["fields"] = [
        {
            "name": field.name,
            "type": field.type,
            "nullable": field.nullable,
            "unique": field.unique,
        }
        for field in fields
    ]
    data["endpoints"] = endpoints
    spec_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
