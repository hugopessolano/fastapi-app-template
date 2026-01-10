import os
import unittest

from app.config import get_settings
from app.main import create_app


class TestOpenApiAuth(unittest.TestCase):
    def test_openapi_includes_oauth2_security(self) -> None:
        os.environ["AUTH_MODE"] = "built_in"
        get_settings.cache_clear()
        app = create_app()
        spec = app.openapi()

        schemes = spec.get("components", {}).get("securitySchemes", {})
        self.assertIn("OAuth2PasswordBearer", schemes)

        secured = [
            (path, method)
            for path, methods in spec.get("paths", {}).items()
            for method, data in methods.items()
            if data.get("security")
        ]
        self.assertTrue(secured)
