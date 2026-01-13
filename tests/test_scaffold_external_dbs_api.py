import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from tools.scaffold.api.app import create_api_app


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestScaffoldExternalDbsApi(unittest.TestCase):
    def test_lists_named_and_legacy_connections(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            env_path = root / ".env"
            write_file(
                env_path,
                "\n".join(
                    [
                        "EXTERNAL_DB_REPORTING_URL=sqlite:///./reporting.db",
                        "EXTERNAL_DB_REPORTING_PERMISSIONS=read,update",
                        "EXTERNAL_DB_URL=sqlite:///./legacy.db",
                        "EXTERNAL_DB_PERMISSIONS=read",
                        "",
                    ]
                ),
            )

            app = create_api_app(root)
            client = TestClient(app)

            response = client.get("/external-dbs")
            self.assertEqual(response.status_code, 200)
            connections = {item["name"]: item for item in response.json()["connections"]}

            self.assertIn("reporting", connections)
            self.assertEqual(connections["reporting"]["permissions"], ["read", "update"])
            self.assertIn("default", connections)
            self.assertEqual(connections["default"]["source"], "legacy")

    def test_creates_updates_and_deletes_connection(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            env_path = root / ".env"
            write_file(env_path, "")

            app = create_api_app(root)
            client = TestClient(app)

            response = client.post(
                "/external-dbs",
                json={
                    "name": "analytics",
                    "url": "sqlite:///./analytics.db",
                    "permissions": ["read"],
                },
            )
            self.assertEqual(response.status_code, 200)

            updated = env_path.read_text(encoding="utf-8")
            self.assertIn("EXTERNAL_DB_ANALYTICS_URL=sqlite:///./analytics.db", updated)
            self.assertIn("EXTERNAL_DB_ANALYTICS_PERMISSIONS=read", updated)

            response = client.post(
                "/external-dbs/delete",
                json={"name": "analytics"},
            )
            self.assertEqual(response.status_code, 200)
            updated = env_path.read_text(encoding="utf-8")
            self.assertNotIn("EXTERNAL_DB_ANALYTICS_URL", updated)

    def test_updates_legacy_default_without_creating_named_default(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            env_path = root / ".env"
            write_file(env_path, "EXTERNAL_DB_URL=sqlite:///./legacy.db\n")

            app = create_api_app(root)
            client = TestClient(app)

            response = client.post(
                "/external-dbs",
                json={
                    "name": "default",
                    "url": "sqlite:///./updated.db",
                    "permissions": "read",
                },
            )
            self.assertEqual(response.status_code, 200)

            updated = env_path.read_text(encoding="utf-8")
            self.assertIn("EXTERNAL_DB_URL=sqlite:///./updated.db", updated)
            self.assertNotIn("EXTERNAL_DB_DEFAULT_URL", updated)

    def test_rejects_invalid_name_url_and_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            app = create_api_app(root)
            client = TestClient(app)

            response = client.post(
                "/external-dbs",
                json={"name": "bad name", "url": "sqlite:///./db.sqlite"},
            )
            self.assertEqual(response.status_code, 400)

            response = client.post(
                "/external-dbs",
                json={"name": "analytics", "url": "not-a-url"},
            )
            self.assertEqual(response.status_code, 400)

            response = client.post(
                "/external-dbs",
                json={
                    "name": "analytics",
                    "url": "sqlite:///./db.sqlite",
                    "permissions": "read,execute",
                },
            )
            self.assertEqual(response.status_code, 400)

    def test_connection_test_endpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            app = create_api_app(root)
            client = TestClient(app)

            response = client.post(
                "/external-dbs/test",
                json={"url": "sqlite:///./test.db"},
            )
            self.assertEqual(response.status_code, 200)

            response = client.post(
                "/external-dbs/test",
                json={"url": "not-a-url"},
            )
            self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
