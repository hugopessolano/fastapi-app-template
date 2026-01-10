import importlib
import unittest

class TestGeneratedModules(unittest.TestCase):
    def test_modules_import(self):
        modules = [
            "app.endpoints_logic.v1.order_items",
            "app.routers.v1.order_items",
            "app.schemas.order_items_schemas",
            "app.database.models.order_items_models",
        ]
        for module in modules:
            with self.subTest(module=module):
                importlib.import_module(module)
