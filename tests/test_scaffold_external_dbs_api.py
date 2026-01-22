import tempfile
import unittest
from pathlib import Path

from tests.scaffold_test_utils import (
    create_minimal_project,
    create_scaffold_client,
    open_project,
    project_headers,
    write_file,
)


class TestScaffoldExternalDbsApi(unittest.TestCase):
    def test_lists_named_and_legacy_connections(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            scaffold_root = Path(tempdir)
            project_root = scaffold_root / "demo"
            create_minimal_project(project_root)
            env_path = project_root / ".env"
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

            client = create_scaffold_client(scaffold_root)
            project = open_project(client, project_root)
            headers = project_headers(project)

            response = client.get("/external-dbs", headers=headers)
            self.assertEqual(response.status_code, 200)
            connections = {item["name"]: item for item in response.json()["connections"]}

            self.assertIn("reporting", connections)
            self.assertEqual(connections["reporting"]["permissions"], ["read", "update"])
            self.assertIn("default", connections)
            self.assertEqual(connections["default"]["source"], "legacy")

    def test_creates_updates_and_deletes_connection(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            scaffold_root = Path(tempdir)
            project_root = scaffold_root / "demo"
            create_minimal_project(project_root)
            env_path = project_root / ".env"
            write_file(env_path, "")

            client = create_scaffold_client(scaffold_root)
            project = open_project(client, project_root)
            headers = project_headers(project)

            response = client.post(
                "/external-dbs",
                json={
                    "name": "analytics",
                    "url": "sqlite:///./analytics.db",
                    "permissions": ["read"],
                },
                headers=headers,
            )
            self.assertEqual(response.status_code, 200)

            updated = env_path.read_text(encoding="utf-8")
            self.assertIn("EXTERNAL_DB_ANALYTICS_URL=sqlite:///./analytics.db", updated)
            self.assertIn("EXTERNAL_DB_ANALYTICS_PERMISSIONS=read", updated)

            response = client.post(
                "/external-dbs/delete",
                json={"name": "analytics"},
                headers=headers,
            )
            self.assertEqual(response.status_code, 200)
            updated = env_path.read_text(encoding="utf-8")
            self.assertNotIn("EXTERNAL_DB_ANALYTICS_URL", updated)

    def test_updates_legacy_default_without_creating_named_default(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            scaffold_root = Path(tempdir)
            project_root = scaffold_root / "demo"
            create_minimal_project(project_root)
            env_path = project_root / ".env"
            write_file(env_path, "EXTERNAL_DB_URL=sqlite:///./legacy.db\n")

            client = create_scaffold_client(scaffold_root)
            project = open_project(client, project_root)
            headers = project_headers(project)

            response = client.post(
                "/external-dbs",
                json={
                    "name": "default",
                    "url": "sqlite:///./updated.db",
                    "permissions": "read",
                },
                headers=headers,
            )
            self.assertEqual(response.status_code, 200)

            updated = env_path.read_text(encoding="utf-8")
            self.assertIn("EXTERNAL_DB_URL=sqlite:///./updated.db", updated)
            self.assertNotIn("EXTERNAL_DB_DEFAULT_URL", updated)

    def test_rejects_invalid_name_url_and_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            scaffold_root = Path(tempdir)
            project_root = scaffold_root / "demo"
            create_minimal_project(project_root)
            client = create_scaffold_client(scaffold_root)
            project = open_project(client, project_root)
            headers = project_headers(project)

            response = client.post(
                "/external-dbs",
                json={"name": "bad name", "url": "sqlite:///./db.sqlite"},
                headers=headers,
            )
            self.assertEqual(response.status_code, 400)

            response = client.post(
                "/external-dbs",
                json={"name": "analytics", "url": "not-a-url"},
                headers=headers,
            )
            self.assertEqual(response.status_code, 400)

            response = client.post(
                "/external-dbs",
                json={
                    "name": "analytics",
                    "url": "sqlite:///./db.sqlite",
                    "permissions": "read,execute",
                },
                headers=headers,
            )
            self.assertEqual(response.status_code, 400)

    def test_connection_test_endpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            scaffold_root = Path(tempdir)
            project_root = scaffold_root / "demo"
            create_minimal_project(project_root)
            client = create_scaffold_client(scaffold_root)
            project = open_project(client, project_root)
            headers = project_headers(project)

            response = client.post(
                "/external-dbs/test",
                json={"url": "sqlite:///./test.db"},
                headers=headers,
            )
            self.assertEqual(response.status_code, 200)

            response = client.post(
                "/external-dbs/test",
                json={"url": "not-a-url"},
                headers=headers,
            )
            self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
