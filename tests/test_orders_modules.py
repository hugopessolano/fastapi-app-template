import importlib
import unittest

class TestGeneratedModules(unittest.TestCase):
    def test_modules_import(self):
        modules = [
            "app.endpoints_logic.v1.orders",
            "app.routers.v1.orders",
            "app.schemas.orders_schemas",
            "app.database.models.orders_models",
        ]
        for module in modules:
            with self.subTest(module=module):
                importlib.import_module(module)
