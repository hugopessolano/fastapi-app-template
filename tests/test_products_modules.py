import importlib
import unittest

class TestGeneratedModules(unittest.TestCase):
    def test_modules_import(self):
        modules = [
            "app.endpoints_logic.v1.products",
            "app.routers.v1.products",
            "app.schemas.products_schemas",
            "app.database.models.products_models",
        ]
        for module in modules:
            with self.subTest(module=module):
                importlib.import_module(module)
