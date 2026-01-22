import json
from pathlib import Path

from fastapi.testclient import TestClient

from tools.scaffold.api.app import create_api_app


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def create_scaffold_client(scaffold_root: Path) -> TestClient:
    app = create_api_app(scaffold_root)
    return TestClient(app)


def create_minimal_project(root: Path) -> None:
    write_file(
        root / "app" / "database" / "models" / "__init__.py",
        "from .base_models import Base\n\n__all__ = [\"Base\"]\n",
    )
    write_file(root / "app" / "routers" / "v1" / "__init__.py", "API_PREFIX = \"/v1\"\n")


def open_project(client: TestClient, root: Path, name: str = "sample") -> dict:
    response = client.post("/projects/open", json={"path": str(root), "name": name})
    if response.status_code != 200:
        raise AssertionError(f"Project open failed: {response.status_code} {response.text}")
    return response.json()["project"]


def project_headers(project: dict) -> dict[str, str]:
    return {"X-Scaffold-Project": project["id"]}
