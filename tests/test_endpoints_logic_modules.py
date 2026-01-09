import importlib
import unittest


class TestEndpointsLogicModules(unittest.TestCase):
    def test_logic_modules_are_importable(self) -> None:
        modules = [
            "app.endpoints_logic.v1.tenants",
            "app.endpoints_logic.v1.users",
            "app.endpoints_logic.v1.roles",
            "app.endpoints_logic.v1.permissions",
            "app.endpoints_logic.v1.auth",
        ]
        for module in modules:
            with self.subTest(module=module):
                importlib.import_module(module)
