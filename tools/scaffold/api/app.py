import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
