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


class TestScaffoldSettingsApi(unittest.TestCase):
    def test_reads_and_writes_settings(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            scaffold_root = Path(tempdir)
            project_root = scaffold_root / "demo"
            create_minimal_project(project_root)
            env_path = project_root / ".env"
            write_file(env_path, "AUTH_MODE=built_in\nRATE_LIMIT_DEFAULT_REQUESTS=60\n")

            client = create_scaffold_client(scaffold_root)
            project = open_project(client, project_root)
            headers = project_headers(project)

            response = client.get("/settings", headers=headers)
            self.assertEqual(response.status_code, 200)
            settings = response.json()["settings"]
            self.assertEqual(settings["AUTH_MODE"], "built_in")
            self.assertEqual(settings["RATE_LIMIT_DEFAULT_REQUESTS"], "60")

            response = client.post(
                "/settings",
                json={
                    "settings": {
                        "RATE_LIMIT_DEFAULT_REQUESTS": 120,
                        "AUTH_MODE": "disabled",
                    }
                },
                headers=headers,
            )
            self.assertEqual(response.status_code, 200)

            updated = env_path.read_text(encoding="utf-8")
            self.assertIn("RATE_LIMIT_DEFAULT_REQUESTS=120", updated)
            self.assertIn("AUTH_MODE=disabled", updated)

    def test_rejects_unknown_setting(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            scaffold_root = Path(tempdir)
            project_root = scaffold_root / "demo"
            create_minimal_project(project_root)
            client = create_scaffold_client(scaffold_root)
            project = open_project(client, project_root)
            headers = project_headers(project)

            response = client.post(
                "/settings",
                json={"settings": {"NOT_A_SETTING": "true"}},
                headers=headers,
            )
            self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
