import importlib
import unittest


class TestEndpointsLogicModules(unittest.TestCase):
    def test_logic_modules_are_importable(self) -> None:
        modules = [
            "app.endpoints_logic.tenants",
            "app.endpoints_logic.users",
            "app.endpoints_logic.roles",
            "app.endpoints_logic.permissions",
            "app.endpoints_logic.auth",
        ]
        for module in modules:
            with self.subTest(module=module):
                importlib.import_module(module)
