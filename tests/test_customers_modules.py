import importlib
import unittest

class TestGeneratedModules(unittest.TestCase):
    def test_modules_import(self):
        modules = [
            "app.endpoints_logic.v1.customers",
            "app.routers.v1.customers",
            "app.schemas.customers_schemas",
            "app.database.models.customers_models",
        ]
        for module in modules:
            with self.subTest(module=module):
                importlib.import_module(module)
