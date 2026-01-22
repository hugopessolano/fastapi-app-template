import json
import tempfile
import unittest
from pathlib import Path

from tests.scaffold_test_utils import read_json, write_file
from tools.scaffold.factory import create_project


def build_template_root(root: Path) -> None:
    write_file(root / "app" / "main.py", "# main\n")
    write_file(root / "requirements.txt", "fastapi\n")
    write_file(root / "Dockerfile", "FROM python:3.13-slim\n")
    write_file(root / ".env.example", "AUTH_MODE=built_in\n")

    write_file(root / "app" / "routers" / "v1" / "auth.py", "# auth\n")
    write_file(root / "app" / "routers" / "v1" / "customers.py", "# customers\n")
    registry = {
        "v1": [
            {
                "name": "auth",
                "module": "app.routers.v1.auth",
                "requires_auth": True,
                "requires_tenants": False,
                "enabled": True,
            },
            {
                "name": "customers",
                "module": "app.routers.v1.customers",
                "requires_auth": False,
                "requires_tenants": False,
                "enabled": True,
            },
        ]
    }
    write_file(
        root / "app" / "routers" / "registry_data.json",
        json.dumps(registry, indent=2),
    )

    write_file(root / "app" / "database" / "models" / "users_models.py", "# users\n")
    write_file(
        root / "app" / "database" / "models" / "customers_models.py",
        "# customers\n",
    )
    write_file(
        root / "app" / "database" / "models" / "__init__.py",
        "\n".join(
            [
                "from .base_models import Base",
                "from .users_models import Users",
                "from .customers_models import Customers",
                "",
                "__all__ = [\"Base\", \"Users\", \"Customers\"]",
                "",
            ]
        ),
    )

    write_file(root / "app" / "schemas" / "users_schemas.py", "# users\n")
    write_file(root / "app" / "schemas" / "customers_schemas.py", "# customers\n")
    write_file(root / "app" / "schemas" / "token_schemas.py", "# token\n")

    write_file(root / "app" / "endpoints_logic" / "v1" / "users.py", "# users\n")
    write_file(
        root / "app" / "endpoints_logic" / "v1" / "customers.py",
        "# customers\n",
    )

    write_file(root / "tests" / "test_customers_modules.py", "# test\n")


class TestScaffoldFactory(unittest.TestCase):
    def test_create_project_prunes_non_auth_resources(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            temp_path = Path(tempdir)
            template_root = temp_path / "template"
            base_path = temp_path / "output"
            build_template_root(template_root)

            project_root = create_project(template_root, base_path, "demo")

            self.assertTrue((project_root / "app" / "main.py").exists())
            self.assertTrue((project_root / ".env").exists())
            self.assertTrue((project_root / "app" / "routers" / "v1" / "auth.py").exists())
            self.assertFalse(
                (project_root / "app" / "routers" / "v1" / "customers.py").exists()
            )
            self.assertFalse(
                (project_root / "app" / "database" / "models" / "customers_models.py").exists()
            )
            self.assertFalse(
                (project_root / "app" / "schemas" / "customers_schemas.py").exists()
            )
            self.assertFalse(
                (project_root / "app" / "endpoints_logic" / "v1" / "customers.py").exists()
            )
            self.assertFalse((project_root / "tests" / "test_customers_modules.py").exists())

            models_init = (project_root / "app" / "database" / "models" / "__init__.py").read_text(
                encoding="utf-8"
            )
            self.assertNotIn("Customers", models_init)

            registry = read_json(project_root / "app" / "routers" / "registry_data.json")
            names = [item["name"] for item in registry.get("v1", [])]
            self.assertEqual(
                names,
                ["tenants", "roles", "permissions", "users", "auth"],
            )


if __name__ == "__main__":
    unittest.main()
