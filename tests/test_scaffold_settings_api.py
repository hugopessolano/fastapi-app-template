import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from tools.scaffold.api.app import create_api_app


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestScaffoldSettingsApi(unittest.TestCase):
    def test_reads_and_writes_settings(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            env_path = root / ".env"
            write_file(env_path, "AUTH_MODE=built_in\nRATE_LIMIT_DEFAULT_REQUESTS=60\n")

            app = create_api_app(root)
            client = TestClient(app)

            response = client.get("/settings")
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
            )
            self.assertEqual(response.status_code, 200)

            updated = env_path.read_text(encoding="utf-8")
            self.assertIn("RATE_LIMIT_DEFAULT_REQUESTS=120", updated)
            self.assertIn("AUTH_MODE=disabled", updated)

    def test_rejects_unknown_setting(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            app = create_api_app(root)
            client = TestClient(app)

            response = client.post(
                "/settings",
                json={"settings": {"NOT_A_SETTING": "true"}},
            )
            self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
