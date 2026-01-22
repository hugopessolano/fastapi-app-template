import json
import os
import tempfile
import unittest
from pathlib import Path

from tests.scaffold_test_utils import (
    create_minimal_project,
    create_scaffold_client,
    open_project,
    write_file,
)


class TestScaffoldProjectsApi(unittest.TestCase):
    def test_browse_projects_root(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            scaffold_root = Path(tempdir) / "scaffold"
            scaffold_root.mkdir()
            projects_root = Path(tempdir) / "projects"
            (projects_root / "alpha").mkdir(parents=True)
            (projects_root / "beta").mkdir(parents=True)

            os.environ["SCAFFOLD_PROJECTS_ROOT"] = str(projects_root)
            client = create_scaffold_client(scaffold_root)

            response = client.get("/projects/browse")
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            names = {item["name"] for item in payload["directories"]}
            self.assertEqual(names, {"alpha", "beta"})
            self.assertEqual(payload["path"], "")
            self.assertEqual(payload["root"], str(projects_root))

            os.environ.pop("SCAFFOLD_PROJECTS_ROOT", None)

    def test_rejects_create_outside_projects_root(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            scaffold_root = Path(tempdir) / "scaffold"
            scaffold_root.mkdir()
            projects_root = Path(tempdir) / "projects"
            projects_root.mkdir()

            os.environ["SCAFFOLD_PROJECTS_ROOT"] = str(projects_root)
            client = create_scaffold_client(scaffold_root)

            response = client.post(
                "/projects/create",
                json={"base_path": str(Path(tempdir).parent), "name": "bad"},
            )
            self.assertEqual(response.status_code, 400)

            os.environ.pop("SCAFFOLD_PROJECTS_ROOT", None)

    def test_open_project_registers_and_lists(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            scaffold_root = Path(tempdir)
            project_root = scaffold_root / "demo"
            create_minimal_project(project_root)

            client = create_scaffold_client(scaffold_root)
            project = open_project(client, project_root, name="Demo API")

            response = client.get("/projects")
            self.assertEqual(response.status_code, 200)
            projects = response.json()["projects"]
            self.assertTrue(any(item["id"] == project["id"] for item in projects))

    def test_prunes_missing_projects_on_read(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            scaffold_root = Path(tempdir)
            missing_path = scaffold_root / "missing"
            projects_path = scaffold_root / "projects.json"
            write_file(
                projects_path,
                json.dumps(
                    {
                        "projects": [
                            {
                                "id": "missing",
                                "name": "Missing",
                                "path": str(missing_path),
                            }
                        ]
                    },
                    indent=2,
                ),
            )

            client = create_scaffold_client(scaffold_root)
            response = client.get("/projects")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["projects"], [])
            updated = json.loads(projects_path.read_text(encoding="utf-8"))
            self.assertEqual(updated.get("projects", []), [])

    def test_requires_project_header_for_specs(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            scaffold_root = Path(tempdir)
            client = create_scaffold_client(scaffold_root)

            response = client.get("/specs")
            self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
