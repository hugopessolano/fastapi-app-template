import json
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from tools.scaffold.api.app import create_api_app


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def create_minimal_repo(root: Path) -> None:
    write_file(
        root / "app" / "database" / "models" / "__init__.py",
        "from .base_models import Base\n\n__all__ = [\"Base\"]\n",
    )
    write_file(root / "app" / "routers" / "v1" / "__init__.py", "API_PREFIX = \"/v1\"\n")


def create_spec(root: Path, resource: str) -> Path:
    spec = {
        "version": "v1",
        "name": resource,
        "plural": f"{resource}s",
        "table_name": f"{resource}s",
        "tags": [resource.capitalize() + "s"],
        "auth_required": True,
        "tenant_scoped": False,
        "soft_delete": True,
        "pagination": True,
        "ordering": True,
        "fields": [
            {"name": "name", "type": "String", "nullable": False, "unique": False}
        ],
        "endpoints": {
            "list": True,
            "get": True,
            "create": True,
            "update": True,
            "delete": True,
        },
        "tests": {"enabled": True},
    }
    path = root / "specs" / f"{resource}s.json"
    write_file(path, json.dumps(spec, indent=2))
    return path


class TestScaffoldApi(unittest.TestCase):
    def test_list_and_read_specs(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            create_minimal_repo(root)
            spec_path = create_spec(root, "widget")

            app = create_api_app(root)
            client = TestClient(app)

            response = client.get("/specs")
            self.assertEqual(response.status_code, 200)
            specs = response.json()["specs"]
            self.assertTrue(any(item["path"] == str(spec_path.relative_to(root)) for item in specs))

            response = client.get("/specs/read", params={"path": str(spec_path.relative_to(root))})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["spec"]["name"], "widget")

    def test_spec_write_and_scaffold_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            create_minimal_repo(root)
            spec_path = root / "specs" / "widgets.json"

            app = create_api_app(root)
            client = TestClient(app)

            spec = {
                "version": "v1",
                "name": "widget",
                "plural": "widgets",
                "table_name": "widgets",
                "tags": ["Widgets"],
                "auth_required": True,
                "tenant_scoped": False,
                "soft_delete": True,
                "pagination": True,
                "ordering": True,
                "fields": [
                    {"name": "name", "type": "String", "nullable": False, "unique": False}
                ],
                "endpoints": {
                    "list": True,
                    "get": True,
                    "create": True,
                    "update": True,
                    "delete": True,
                },
                "tests": {"enabled": True},
            }
            response = client.post(
                "/specs/write",
                json={"path": str(spec_path.relative_to(root)), "spec": spec},
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(spec_path.exists())

            response = client.post(
                "/scaffold/create",
                json={"spec_path": str(spec_path.relative_to(root))},
            )
            self.assertEqual(response.status_code, 200)

            model_path = root / "app" / "database" / "models" / "widgets_models.py"
            self.assertTrue(model_path.exists())

            spec["fields"].append(
                {"name": "status", "type": "String", "nullable": True, "unique": False}
            )
            write_file(spec_path, json.dumps(spec, indent=2))
            response = client.post(
                "/scaffold/sync-to-code",
                json={"spec_path": str(spec_path.relative_to(root))},
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn("status = Column(String, nullable=True, unique=False)", model_path.read_text(encoding="utf-8"))

            content = model_path.read_text(encoding="utf-8")
            updated = content.replace(
                "status = Column(String, nullable=True, unique=False)\n",
                "status = Column(String, nullable=True, unique=False)\n    size = Column(String, nullable=True, unique=False)\n",
            )
            model_path.write_text(updated, encoding="utf-8")

            response = client.post(
                "/scaffold/sync-from-code",
                json={"spec_path": str(spec_path.relative_to(root))},
            )
            self.assertEqual(response.status_code, 200)
            updated_spec = read_json(spec_path)
            field_names = {field["name"] for field in updated_spec["fields"]}
            self.assertIn("size", field_names)

            response = client.post(
                "/scaffold/remove",
                json={"spec_path": str(spec_path.relative_to(root))},
            )
            self.assertEqual(response.status_code, 200)
            self.assertFalse(model_path.exists())
            self.assertTrue(spec_path.exists())

    def test_rejects_paths_outside_root(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            create_minimal_repo(root)
            app = create_api_app(root)
            client = TestClient(app)

            response = client.get("/specs/read", params={"path": "../outside.json"})
            self.assertEqual(response.status_code, 400)

    def test_schema_config_generates_constraints(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            create_minimal_repo(root)
            spec_path = root / "specs" / "widgets.json"

            app = create_api_app(root)
            client = TestClient(app)

            spec = {
                "version": "v1",
                "name": "widget",
                "plural": "widgets",
                "table_name": "widgets",
                "tags": ["Widgets"],
                "auth_required": True,
                "tenant_scoped": False,
                "soft_delete": True,
                "pagination": True,
                "ordering": True,
                "fields": [
                    {"name": "name", "type": "String", "nullable": False, "unique": False}
                ],
                "endpoints": {
                    "list": True,
                    "get": True,
                    "create": True,
                    "update": True,
                    "delete": True,
                },
                "tests": {"enabled": True},
                "schemas": {
                    "create": {
                        "fields": [
                            {
                                "name": "name",
                                "type": "String",
                                "required": True,
                                "constraints": {"min_length": 2},
                            }
                        ]
                    }
                },
            }
            response = client.post(
                "/specs/write",
                json={"path": str(spec_path.relative_to(root)), "spec": spec},
            )
            self.assertEqual(response.status_code, 200)

            response = client.post(
                "/scaffold/create",
                json={"spec_path": str(spec_path.relative_to(root))},
            )
            self.assertEqual(response.status_code, 200)

            schema_path = root / "app" / "schemas" / "widgets_schemas.py"
            content = schema_path.read_text(encoding="utf-8")
            self.assertIn("Field(..., min_length=2)", content)

    def test_external_db_helpers_generated(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            create_minimal_repo(root)
            spec_path = root / "specs" / "widgets.json"

            app = create_api_app(root)
            client = TestClient(app)

            spec = {
                "version": "v1",
                "name": "widget",
                "plural": "widgets",
                "table_name": "widgets",
                "tags": ["Widgets"],
                "auth_required": True,
                "tenant_scoped": False,
                "soft_delete": True,
                "pagination": True,
                "ordering": True,
                "fields": [
                    {"name": "name", "type": "String", "nullable": False, "unique": False}
                ],
                "endpoints": {
                    "list": True,
                    "get": True,
                    "create": True,
                    "update": True,
                    "delete": True,
                },
                "tests": {"enabled": True},
                "external_dbs": [
                    {"name": "reporting", "permissions": ["read"]},
                    {"name": "legacy", "permissions": []},
                ],
            }
            response = client.post(
                "/specs/write",
                json={"path": str(spec_path.relative_to(root)), "spec": spec},
            )
            self.assertEqual(response.status_code, 200)

            response = client.post(
                "/scaffold/create",
                json={"spec_path": str(spec_path.relative_to(root))},
            )
            self.assertEqual(response.status_code, 200)

            logic_path = root / "app" / "endpoints_logic" / "v1" / "widgets.py"
            content = logic_path.read_text(encoding="utf-8")
            self.assertIn("def external_session", content)
            self.assertIn("def get_reporting_db()", content)
            self.assertIn("def get_legacy_db()", content)

    def test_registry_updates_auth_flags_on_modify(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            create_minimal_repo(root)
            spec_path = root / "specs" / "widgets.json"

            app = create_api_app(root)
            client = TestClient(app)

            spec = {
                "version": "v1",
                "name": "widget",
                "plural": "widgets",
                "table_name": "widgets",
                "tags": ["Widgets"],
                "auth_required": True,
                "tenant_scoped": False,
                "soft_delete": True,
                "pagination": True,
                "ordering": True,
                "fields": [
                    {"name": "name", "type": "String", "nullable": False, "unique": False}
                ],
                "endpoints": {
                    "list": True,
                    "get": True,
                    "create": True,
                    "update": True,
                    "delete": True,
                },
                "tests": {"enabled": True},
            }
            response = client.post(
                "/specs/write",
                json={"path": str(spec_path.relative_to(root)), "spec": spec},
            )
            self.assertEqual(response.status_code, 200)

            response = client.post(
                "/scaffold/create",
                json={"spec_path": str(spec_path.relative_to(root))},
            )
            self.assertEqual(response.status_code, 200)

            registry_path = root / "app" / "routers" / "registry_data.json"
            registry = read_json(registry_path)
            entry = next(item for item in registry["v1"] if item["name"] == "widgets")
            self.assertTrue(entry["requires_auth"])

            spec["auth_required"] = False
            response = client.post(
                "/specs/write",
                json={"path": str(spec_path.relative_to(root)), "spec": spec},
            )
            self.assertEqual(response.status_code, 200)

            response = client.post(
                "/scaffold/modify",
                json={"spec_path": str(spec_path.relative_to(root))},
            )
            self.assertEqual(response.status_code, 200)

            registry = read_json(registry_path)
            entry = next(item for item in registry["v1"] if item["name"] == "widgets")
            self.assertFalse(entry["requires_auth"])
