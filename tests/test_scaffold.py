import json
import tempfile
import unittest
from pathlib import Path

from tools.scaffold.scaffold import create_resource, remove_resource, sync_resource


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def create_minimal_repo(root: Path) -> None:
    write_file(
        root / "app" / "database" / "models" / "__init__.py",
        "from .base_models import Base\n\n__all__ = [\"Base\"]\n",
    )
    write_file(root / "app" / "routers" / "v1" / "__init__.py", "API_PREFIX = \"/v1\"\n")


def create_spec(root: Path, resource: str) -> Path:
    spec = {
        "version": "v1",
        "name": resource,
        "plural": f"{resource}s",
        "table_name": f"{resource}s",
        "tags": [resource.capitalize() + "s"],
        "auth_required": True,
        "tenant_scoped": False,
        "soft_delete": True,
        "pagination": True,
        "ordering": True,
        "fields": [
            {"name": "name", "type": "String", "nullable": False, "unique": False}
        ],
        "endpoints": {
            "list": True,
            "get": True,
            "create": True,
            "update": True,
            "delete": True,
        },
        "tests": {"enabled": True},
    }
    path = root / "specs" / f"{resource}s.json"
    write_file(path, json.dumps(spec, indent=2))
    return path


class TestScaffold(unittest.TestCase):
    def test_create_generates_files_and_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            create_minimal_repo(root)
            spec_path = create_spec(root, "widget")

            create_resource(root, spec_path)

            model_path = root / "app" / "database" / "models" / "widgets_models.py"
            schema_path = root / "app" / "schemas" / "widgets_schemas.py"
            logic_path = root / "app" / "endpoints_logic" / "v1" / "widgets.py"
            router_path = root / "app" / "routers" / "v1" / "widgets.py"
            test_path = root / "tests" / "test_widgets_modules.py"
            registry_path = root / "app" / "routers" / "registry_data.json"

            self.assertTrue(model_path.exists())
            self.assertTrue(schema_path.exists())
            self.assertTrue(logic_path.exists())
            self.assertTrue(router_path.exists())
            self.assertTrue(test_path.exists())
            self.assertTrue(registry_path.exists())

            registry = read_json(registry_path)
            self.assertIn("v1", registry)
            self.assertTrue(
                any(item["name"] == "widgets" for item in registry["v1"])
            )

    def test_sync_updates_spec_from_code(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            create_minimal_repo(root)
            spec_path = create_spec(root, "widget")
            create_resource(root, spec_path)

            model_path = root / "app" / "database" / "models" / "widgets_models.py"
            content = model_path.read_text(encoding="utf-8")
            target = "name = Column(String, nullable=False, unique=False)\n"
            updated = content.replace(
                target,
                target + "    status = Column(String, nullable=True, unique=False)\n",
            )
            model_path.write_text(updated, encoding="utf-8")

            sync_resource(root, spec_path)

            spec = read_json(spec_path)
            field_names = {field["name"] for field in spec["fields"]}
            self.assertIn("status", field_names)

    def test_sync_updates_code_from_spec(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            create_minimal_repo(root)
            spec_path = create_spec(root, "widget")
            create_resource(root, spec_path)

            spec = read_json(spec_path)
            spec["fields"].append(
                {"name": "size", "type": "String", "nullable": True, "unique": False}
            )
            write_file(spec_path, json.dumps(spec, indent=2))

            sync_resource(root, spec_path)

            model_path = root / "app" / "database" / "models" / "widgets_models.py"
            content = model_path.read_text(encoding="utf-8")
            self.assertIn("size = Column(String, nullable=True, unique=False)", content)

    def test_remove_cleans_generated_files(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            create_minimal_repo(root)
            spec_path = create_spec(root, "widget")

            create_resource(root, spec_path)
            remove_resource(root, spec_path)

            model_path = root / "app" / "database" / "models" / "widgets_models.py"
            schema_path = root / "app" / "schemas" / "widgets_schemas.py"
            logic_path = root / "app" / "endpoints_logic" / "v1" / "widgets.py"
            router_path = root / "app" / "routers" / "v1" / "widgets.py"
            test_path = root / "tests" / "test_widgets_modules.py"
            manifest_path = root / ".scaffold" / "manifest.json"
            registry_path = root / "app" / "routers" / "registry_data.json"
            models_init = root / "app" / "database" / "models" / "__init__.py"

            self.assertFalse(model_path.exists())
            self.assertFalse(schema_path.exists())
            self.assertFalse(logic_path.exists())
            self.assertFalse(router_path.exists())
            self.assertFalse(test_path.exists())
            self.assertFalse(manifest_path.exists())
            self.assertTrue(spec_path.exists())

            registry = read_json(registry_path)
            self.assertNotIn("v1", registry)

            init_content = models_init.read_text(encoding="utf-8")
            self.assertNotIn("from .widgets_models import Widgets", init_content)
            self.assertNotIn("\"Widgets\"", init_content)

    def test_relations_generate_fk_and_relationships(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            create_minimal_repo(root)
            spec = {
                "version": "v1",
                "name": "sale",
                "plural": "sales",
                "table_name": "sales",
                "tags": ["Sales"],
                "auth_required": True,
                "tenant_scoped": False,
                "soft_delete": True,
                "pagination": True,
                "ordering": True,
                "fields": [
                    {"name": "code", "type": "String", "nullable": False, "unique": True}
                ],
                "endpoints": {
                    "list": True,
                    "get": True,
                    "create": True,
                    "update": True,
                    "delete": True,
                },
                "tests": {"enabled": True},
                "relations": [
                    {
                        "name": "customer",
                        "type": "belongs_to",
                        "target": "customers",
                        "foreign_key": "customer_id",
                        "nullable": False,
                        "on_delete": "restrict",
                        "back_populates": "sales",
                    },
                    {
                        "name": "items",
                        "type": "has_many",
                        "target": "sale_items",
                        "back_populates": "sale",
                        "soft_delete_cascade": True,
                    },
                    {
                        "name": "products",
                        "type": "many_to_many",
                        "target": "products",
                        "through": "sales_products",
                        "back_populates": "sales",
                    },
                ],
            }
            spec_path = root / "specs" / "sales.json"
            write_file(spec_path, json.dumps(spec, indent=2))

            create_resource(root, spec_path)

            model_path = root / "app" / "database" / "models" / "sales_models.py"
            model_content = model_path.read_text(encoding="utf-8")
            self.assertIn(
                "customer_id = Column(String, ForeignKey(\"customers.id\"",
                model_content,
            )
            self.assertIn("customer = relationship(\"Customers\"", model_content)
            self.assertIn("items: Mapped[List[\"SaleItems\"]]", model_content)
            self.assertIn("soft_delete_cascade", model_content)
            self.assertIn("sales_products = Table(", model_content)
            self.assertIn("secondary=sales_products", model_content)

            schema_path = root / "app" / "schemas" / "sales_schemas.py"
            schema_content = schema_path.read_text(encoding="utf-8")
            self.assertIn("customer_id: str", schema_content)

    def test_schema_variants_embed_relations(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            create_minimal_repo(root)
            spec = {
                "version": "v1",
                "name": "order",
                "plural": "orders",
                "table_name": "orders",
                "tags": ["Orders"],
                "auth_required": True,
                "tenant_scoped": False,
                "soft_delete": True,
                "pagination": True,
                "ordering": True,
                "fields": [
                    {"name": "number", "type": "String", "nullable": False, "unique": True}
                ],
                "endpoints": {
                    "list": True,
                    "get": True,
                    "create": True,
                    "update": True,
                    "delete": True,
                },
                "tests": {"enabled": True},
                "relations": [
                    {
                        "name": "items",
                        "type": "has_many",
                        "target": "order_items",
                        "back_populates": "order",
                        "soft_delete_cascade": True,
                    },
                ],
                "schemas": {
                    "response": {
                        "relations": [{"name": "items", "mode": "embedded"}],
                    }
                },
            }
            spec_path = root / "specs" / "orders.json"
            write_file(spec_path, json.dumps(spec, indent=2))

            create_resource(root, spec_path)

            schema_path = root / "app" / "schemas" / "orders_schemas.py"
            schema_content = schema_path.read_text(encoding="utf-8")
            self.assertIn("class BaseOrderCore", schema_content)
            self.assertIn("items: Optional[List[BaseOrderItemCore]] = None", schema_content)
            self.assertIn("from app.schemas.order_items_schemas import BaseOrderItemCore", schema_content)

    def test_schema_field_constraints_render(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            create_minimal_repo(root)
            spec = {
                "version": "v1",
                "name": "widget",
                "plural": "widgets",
                "table_name": "widgets",
                "tags": ["Widgets"],
                "auth_required": True,
                "tenant_scoped": False,
                "soft_delete": True,
                "pagination": True,
                "ordering": True,
                "fields": [
                    {"name": "name", "type": "String", "nullable": False, "unique": False}
                ],
                "endpoints": {
                    "list": True,
                    "get": True,
                    "create": True,
                    "update": True,
                    "delete": True,
                },
                "tests": {"enabled": True},
                "schemas": {
                    "create": {
                        "fields": [
                            {
                                "name": "name",
                                "type": "String",
                                "required": True,
                                "constraints": {"min_length": 2, "max_length": 40},
                            }
                        ]
                    }
                },
            }
            spec_path = root / "specs" / "widgets.json"
            write_file(spec_path, json.dumps(spec, indent=2))

            create_resource(root, spec_path)

            schema_path = root / "app" / "schemas" / "widgets_schemas.py"
            schema_content = schema_path.read_text(encoding="utf-8")
            self.assertIn("name: str = Field(..., min_length=2, max_length=40)", schema_content)
