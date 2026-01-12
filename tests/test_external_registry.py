import unittest

from app.database.external_registry import (
    ExternalConnectionError,
    build_external_registry,
    parse_external_configs,
    parse_permissions,
)


class TestExternalRegistry(unittest.TestCase):
    def test_parse_multiple_connections(self) -> None:
        env = {
            "EXTERNAL_DB_REPORTING_URL": "sqlite:///./reporting.db",
            "EXTERNAL_DB_REPORTING_PERMISSIONS": "read,update",
            "EXTERNAL_DB_LEGACY_URL": "sqlite:///./legacy.db",
        }
        configs = parse_external_configs(env)
        self.assertIn("reporting", configs)
        self.assertIn("legacy", configs)
        self.assertEqual(configs["reporting"]["permissions"], {"read", "update"})
        self.assertEqual(configs["legacy"]["permissions"], {"create", "read", "update", "delete"})

    def test_legacy_env_is_supported(self) -> None:
        env = {"EXTERNAL_DB_URL": "sqlite:///./legacy.db"}
        configs = parse_external_configs(env)
        self.assertIn("default", configs)
        self.assertEqual(configs["default"]["url"], "sqlite:///./legacy.db")

    def test_parse_permissions_rejects_unknown(self) -> None:
        with self.assertRaises(ExternalConnectionError):
            parse_permissions("read,execute")

    def test_build_registry_creates_entries(self) -> None:
        env = {
            "EXTERNAL_DB_REPORTING_URL": "sqlite:///./reporting.db",
            "EXTERNAL_DB_REPORTING_PERMISSIONS": "read",
        }
        registry = build_external_registry(env)
        self.assertIn("reporting", registry)
        self.assertEqual(registry["reporting"].permissions, {"read"})
