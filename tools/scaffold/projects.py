import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4


def projects_path(scaffold_root: Path) -> Path:
    return scaffold_root / "projects.json"


def load_projects(scaffold_root: Path) -> list[dict[str, Any]]:
    path = projects_path(scaffold_root)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    projects = data.get("projects", [])
    if isinstance(projects, list):
        return [item for item in projects if isinstance(item, dict)]
    return []


def save_projects(scaffold_root: Path, projects: list[dict[str, Any]]) -> None:
    path = projects_path(scaffold_root)
    payload = {"projects": projects}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def prune_missing_projects(scaffold_root: Path) -> list[dict[str, Any]]:
    projects = load_projects(scaffold_root)
    kept = [item for item in projects if Path(item.get("path", "")).exists()]
    if kept != projects:
        save_projects(scaffold_root, kept)
    return kept


def get_projects_root(scaffold_root: Path) -> Path:
    raw = os.getenv("SCAFFOLD_PROJECTS_ROOT", "")
    if raw.strip():
        return Path(raw).expanduser().resolve()
    return scaffold_root.resolve()


def resolve_projects_path(scaffold_root: Path, path: str | None) -> tuple[Path, Path]:
    root = get_projects_root(scaffold_root)
    if not root.exists():
        raise FileNotFoundError(f"Projects root not found: {root}")
    candidate = Path(path) if path else Path(".")
    resolved = (root / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise PermissionError("Path is outside the allowed root.") from exc
    if not resolved.exists():
        raise FileNotFoundError(f"Project path not found: {resolved}")
    return root, resolved


def register_project(scaffold_root: Path, name: str | None, path: str) -> dict[str, Any]:
    _, resolved = resolve_projects_path(scaffold_root, path)

    projects = prune_missing_projects(scaffold_root)
    existing = next(
        (item for item in projects if Path(item.get("path", "")).resolve() == resolved),
        None,
    )
    if existing:
        if name and existing.get("name") != name:
            existing["name"] = name
            save_projects(scaffold_root, projects)
        return existing

    project = {
        "id": uuid4().hex,
        "name": name or resolved.name,
        "path": str(resolved),
    }
    projects.append(project)
    save_projects(scaffold_root, projects)
    return project


def get_project(scaffold_root: Path, project_id: str) -> dict[str, Any] | None:
    projects = prune_missing_projects(scaffold_root)
    return next((item for item in projects if item.get("id") == project_id), None)


def browse_projects(scaffold_root: Path, path: str | None) -> dict[str, Any]:
    root, resolved = resolve_projects_path(scaffold_root, path)
    if not resolved.is_dir():
        raise NotADirectoryError(f"Not a directory: {resolved}")
    relative = "" if resolved == root else str(resolved.relative_to(root))
    directories = [
        {
            "name": entry.name,
            "path": str(entry.relative_to(root)),
        }
        for entry in sorted(resolved.iterdir())
        if entry.is_dir() and not entry.name.startswith(".")
    ]
    parent = None
    if resolved != root:
        parent = str(resolved.parent.relative_to(root))
    return {
        "root": str(root),
        "path": relative,
        "parent": parent,
        "directories": directories,
    }
