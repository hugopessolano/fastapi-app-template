from typing import Any

from tools.scaffold.spec import (
    CustomSchemaSpec,
    FieldSpec,
    RelationSpec,
    ResourceSpec,
    SchemaFieldSpec,
    SchemaRelationSpec,
    to_class_name,
)


TYPE_MAP = {
    "String": "String",
    "Boolean": "Boolean",
    "Integer": "Integer",
    "Float": "Float",
    "DateTime": "DateTime",
}


def model_template(spec: ResourceSpec) -> str:
    schema_fields = build_schema_fields(spec)
    type_imports = {TYPE_MAP[field.type] for field in schema_fields if field.type in TYPE_MAP}
    type_imports.add("String")
    base_imports = {"Column", *type_imports}
    if spec.tenant_scoped or has_foreign_keys(spec) or has_many_to_many(spec):
        base_imports.add("ForeignKey")
    if has_many_to_many(spec):
        base_imports.add("Table")

    imports = ", ".join(sorted(base_imports))
    lines = [
        f"from sqlalchemy import {imports}",
        "from .base_models import Base",
        "from sqlalchemy.orm import Mapped, mapped_column, relationship",
        "from typing import List",
        "import uuid",
        "",
    ]

    if has_many_to_many(spec):
        for relation in spec.relations:
            if relation.type != "many_to_many":
                continue
            table_name = relation.through or default_join_table(spec, relation)
            var_name = table_name
            target_fk = default_target_fk(relation)
            source_fk = default_source_fk(spec)
            ondelete = ondelete_clause(relation)
            lines.extend(
                [
                    f"{var_name} = Table(",
                    f"    \"{table_name}\",",
                    "    Base.metadata,",
                    f"    Column(\"{source_fk}\", String, ForeignKey(\"{spec.table_name}.id\"{ondelete})),",
                    f"    Column(\"{target_fk}\", String, ForeignKey(\"{relation.target}.id\"{ondelete})),",
                    ")",
                    "",
                ]
            )

    lines.extend(
        [
        f"class {spec.model_class}(Base):",
        f"    __tablename__ = \"{spec.table_name}\"",
        "",
        "    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))",
        ]
    )

    for field in spec.fields:
        type_name = TYPE_MAP.get(field.type, field.type)
        nullable = "True" if field.nullable else "False"
        unique = "True" if field.unique else "False"
        lines.append(
            f"    {field.name} = Column({type_name}, nullable={nullable}, unique={unique})"
        )

    for relation in spec.relations:
        if relation.type != "belongs_to":
            continue
        fk_name = relation.foreign_key or default_fk_name(relation)
        if not any(field.name == fk_name for field in spec.fields):
            nullable = "True" if relation.nullable else "False"
            ondelete = ondelete_clause(relation)
            lines.append(
                f"    {fk_name} = Column(String, ForeignKey(\"{relation.target}.id\"{ondelete}), nullable={nullable})"
            )

    if spec.tenant_scoped:
        lines.append("    tenant_id = Column(String, ForeignKey(\"tenants.id\"))")

    for relation in spec.relations:
        relationship_line = build_relationship_line(spec, relation)
        if relationship_line:
            lines.append(relationship_line)

    return "\n".join(lines) + "\n"


def schema_template(spec: ResourceSpec) -> str:
    base_name = spec.schema_base
    create_fields = [field for field in spec.schemas.create.fields if field.enabled]
    update_fields = [field for field in spec.schemas.update.fields if field.enabled]
    response_fields = [field for field in spec.schemas.response.fields if field.enabled]
    response_relations = spec.schemas.response.relations

    relation_fields = build_relation_schema_fields(spec, response_relations)
    all_response_fields = response_fields + relation_fields

    required_imports = gather_schema_imports(create_fields + update_fields + all_response_fields)
    relation_imports = build_relation_imports(spec, response_relations)
    lines = [
        "from __future__ import annotations",
        "",
        "from pydantic import BaseModel" + (", Field" if required_imports["field"] else ""),
        "from app.schemas.base_schema import BaseSchema",
    ]
    if required_imports["optional"]:
        lines.append("from typing import Optional")
    if required_imports["list"]:
        lines.append("from typing import List")
    if required_imports["datetime"]:
        lines.append("from datetime import datetime")
    if required_imports["uuid"]:
        lines.append("from uuid import UUID")
    if required_imports["decimal"]:
        lines.append("from decimal import Decimal")
    if required_imports["email"]:
        lines.append("from pydantic import EmailStr")
    if relation_imports:
        lines.extend(relation_imports)
    lines.extend(
        [
            "",
            f"class Base{base_name}Core(BaseSchema):",
        ]
    )
    for field in response_fields:
        lines.append(f"    {render_schema_field(field)}")
    if not response_fields:
        lines.append("    pass")
    lines.append("")
    lines.append(f"class Base{base_name}(Base{base_name}Core):")
    if relation_fields:
        for field in relation_fields:
            lines.append(f"    {render_schema_field(field)}")
    else:
        lines.append("    pass")
    lines.append("")
    lines.append(f"class {base_name}Create(BaseModel):")
    for field in create_fields:
        lines.append(f"    {render_schema_field(field)}")
    if not create_fields:
        lines.append("    pass")
    lines.append("")
    lines.append(f"class {base_name}Update(BaseModel):")
    for field in update_fields:
        lines.append(f"    {render_schema_field(field)}")
    if not update_fields:
        lines.append("    pass")
    lines.append("")
    lines.append("    class Config:")
    lines.append("        orm_mode = True")
    lines.append("")
    custom_blocks = build_custom_schema_blocks(spec.schemas.custom)
    if custom_blocks:
        lines.extend(custom_blocks)
    return "\n".join(lines)


def logic_template(spec: ResourceSpec) -> str:
    base_name = spec.schema_base
    model_class = spec.model_class
    plural = spec.plural
    list_name = f"list_{plural}"
    create_name = f"create_{spec.name}"
    update_name = f"update_{spec.name}"
    delete_name = f"delete_{spec.name}"
    get_name = f"get_{spec.name}"

    lines = [
        "from __future__ import annotations",
        "",
        "from typing import List, TYPE_CHECKING",
        "",
        "from fastapi import HTTPException, Request, Response",
        "from sqlalchemy.orm import Session",
        "",
        f"from app.database.models import {model_class}",
        "from app.database.soft_delete import soft_delete_by_id",
        "from app.routers.utils import calculate_next_and_last_pages, order_by_parameter, filter_by_tenant",
        f"from app.schemas.{plural}_schemas import {base_name}Create, {base_name}Update",
    ]

    if spec.tenant_scoped:
        lines.append("from app.tenants.context import TenantContext")

    lines.extend(
        [
            "",
            "if TYPE_CHECKING:",
            "    from app.auth.context import AuthContext",
            "",
            "_router_logger = None",
            "",
            "def _get_logger():",
            "    global _router_logger",
            "    if _router_logger is None:",
            "        from app.logging import child_logger",
            "",
            f"        _router_logger = child_logger.bind(router=\"{plural}\")",
            "    return _router_logger",
            "",
            f"SORTABLE_FIELDS_{plural.upper()} = {{",
        ]
    )

    for field in spec.fields:
        lines.append(f"    \"{field.name}\": {model_class}.{field.name},")
    lines.extend(
        [
            "    \"created_at\": {0}.created_at,".format(model_class),
            "    \"updated_at\": {0}.updated_at,".format(model_class),
            "}",
            "",
        ]
    )

    list_signature = [
        "    request: Request",
        "    response: Response",
        "    db: Session",
    ]
    if spec.auth_required:
        list_signature.append("    auth: AuthContext")
    if spec.tenant_scoped:
        list_signature.append("    tenant_ctx: TenantContext")
    list_signature.extend(
        [
            "    page: int",
            "    page_size: int",
            "    order_by: str",
            "    order_dir: str",
        ]
    )
    lines.append(f"def {list_name}(")
    lines.append(",\n".join(list_signature))
    lines.append(f") -> List[{model_class}]:")
    lines.append("    offset = (page - 1) * page_size")
    lines.append(f"    query = db.query({model_class})")
    if spec.tenant_scoped and spec.auth_required:
        lines.append("    if tenant_ctx.enabled and not tenant_ctx.cross_tenant_allowed:")
        lines.append(
            f"        query = filter_by_tenant(query, {model_class}, tenant_ctx.allowed_tenant_ids)"
        )
    lines.append("    calculate_next_and_last_pages(query, page_size, page, request, response)")
    lines.append(
        f"    query = order_by_parameter(order_by, order_dir, SORTABLE_FIELDS_{plural.upper()}, query)"
    )
    lines.append("    items = query.offset(offset).limit(page_size).all()")
    lines.append("    _get_logger().bind(action=\"list\").info(\"Retrieved records\")")
    lines.append("    return items")
    lines.append("")

    lines.append(f"def {get_name}(item_id: str, db: Session) -> {model_class}:")
    lines.append(f"    item = db.query({model_class}).filter({model_class}.id == item_id).first()")
    lines.append("    if not item:")
    lines.append("        raise HTTPException(status_code=404, detail=\"Not found\")")
    lines.append("    return item")
    lines.append("")

    lines.append(
        f"def {create_name}(payload: {base_name}Create, db: Session) -> {model_class}:"
    )
    lines.append(f"    item = {model_class}(**payload.model_dump())")
    lines.append("    db.add(item)")
    lines.append("    db.commit()")
    lines.append("    db.refresh(item)")
    lines.append("    _get_logger().bind(action=\"create\").info(\"Created record\")")
    lines.append("    return item")
    lines.append("")

    lines.append(
        f"def {update_name}(item_id: str, payload: {base_name}Update, db: Session) -> {model_class}:"
    )
    lines.append(f"    item = db.query({model_class}).filter({model_class}.id == item_id).first()")
    lines.append("    if not item:")
    lines.append("        raise HTTPException(status_code=404, detail=\"Not found\")")
    lines.append("    for key, value in payload.model_dump(exclude_unset=True).items():")
    lines.append("        setattr(item, key, value)")
    lines.append("    db.commit()")
    lines.append("    db.refresh(item)")
    lines.append("    _get_logger().bind(action=\"update\").info(\"Updated record\")")
    lines.append("    return item")
    lines.append("")

    lines.append(f"def {delete_name}(item_id: str, db: Session) -> None:")
    if spec.soft_delete:
        lines.append(f"    deleted = soft_delete_by_id(db, {model_class}, item_id)")
        lines.append("    if not deleted:")
        lines.append("        raise HTTPException(status_code=404, detail=\"Not found\")")
    else:
        lines.append(f"    item = db.query({model_class}).filter({model_class}.id == item_id).first()")
        lines.append("    if not item:")
        lines.append("        raise HTTPException(status_code=404, detail=\"Not found\")")
        lines.append("    db.delete(item)")
        lines.append("    db.commit()")
    lines.append("    _get_logger().bind(action=\"delete\").info(\"Deleted record\")")
    lines.append("")

    return "\n".join(lines)


def router_template(spec: ResourceSpec) -> str:
    base_name = spec.schema_base
    plural = spec.plural
    tag = spec.tags[0] if spec.tags else base_name
    list_name = f"list_{plural}"
    create_name = f"create_{spec.name}"
    update_name = f"update_{spec.name}"
    delete_name = f"delete_{spec.name}"
    get_name = f"get_{spec.name}"

    lines = [
        "from typing import List, Literal",
        "",
        "from fastapi import APIRouter, Depends, Query, Request, Response",
        "from sqlalchemy.orm import Session",
        "",
    ]
    if spec.auth_required:
        lines.append("from app.auth.context import AuthContext, get_auth_context")
    if spec.tenant_scoped:
        lines.append("from app.tenants.context import TenantContext, get_tenant_context")
    lines.extend(
        [
            "from app.database.database import get_db",
            f"from app.endpoints_logic.{spec.version}.{plural} import {list_name}, {create_name}, {update_name}, {delete_name}, {get_name}",
            f"from app.schemas.{plural}_schemas import Base{base_name}, {base_name}Create, {base_name}Update",
            "from app.routers.v1 import API_PREFIX",
            "",
            "router = APIRouter(",
            f"    prefix=f\"{{API_PREFIX}}/{plural}\",",
            f"    tags=[\"{tag}\"],",
            ")",
            "",
        ]
    )

    if spec.endpoints.list:
        lines.append(f"@router.get(\"\", response_model=List[Base{base_name}])")
        lines.append("async def get_items(")
        params = [
            "    request: Request",
            "    response: Response",
            "    db: Session = Depends(get_db)",
        ]
        if spec.auth_required:
            params.append("    auth: AuthContext = Depends(get_auth_context)")
        if spec.tenant_scoped:
            params.append("    tenant_ctx: TenantContext = Depends(get_tenant_context)")
        params.extend(
            [
                "    page: int = Query(1, ge=1)",
                "    page_size: int = Query(20, ge=1, le=100)",
                "    order_by: str = Query(\"created_at\")",
                "    order_dir: Literal[\"asc\", \"desc\"] = Query(\"desc\")",
            ]
        )
        lines.append(",\n".join(params))
        lines.append("):")
        call_args = [
            "        request=request",
            "        response=response",
            "        db=db",
        ]
        if spec.auth_required:
            call_args.append("        auth=auth")
        if spec.tenant_scoped:
            call_args.append("        tenant_ctx=tenant_ctx")
        call_args.extend(
            [
                "        page=page",
                "        page_size=page_size",
                "        order_by=order_by",
                "        order_dir=order_dir",
            ]
        )
        lines.append(f"    return {list_name}(")
        lines.append(",\n".join(call_args))
        lines.append("    )")
        lines.append("")

    if spec.endpoints.get:
        lines.append(f"@router.get(\"/{{item_id}}\", response_model=Base{base_name})")
        lines.append("async def get_item(")
        params = [
            "    item_id: str",
            "    db: Session = Depends(get_db)",
        ]
        if spec.auth_required:
            params.append("    auth: AuthContext = Depends(get_auth_context)")
        lines.append(",\n".join(params))
        lines.append("):")
        lines.append(f"    return {get_name}(item_id=item_id, db=db)")
        lines.append("")

    if spec.endpoints.create:
        lines.append(f"@router.post(\"\", response_model=Base{base_name}, status_code=201)")
        lines.append("async def post_item(")
        params = [
            f"    payload: {base_name}Create",
            "    db: Session = Depends(get_db)",
        ]
        if spec.auth_required:
            params.append("    auth: AuthContext = Depends(get_auth_context)")
        lines.append(",\n".join(params))
        lines.append("):")
        lines.append(f"    return {create_name}(payload=payload, db=db)")
        lines.append("")

    if spec.endpoints.update:
        lines.append(f"@router.put(\"/{{item_id}}\", response_model=Base{base_name})")
        lines.append("async def put_item(")
        params = [
            "    item_id: str",
            f"    payload: {base_name}Update",
            "    db: Session = Depends(get_db)",
        ]
        if spec.auth_required:
            params.append("    auth: AuthContext = Depends(get_auth_context)")
        lines.append(",\n".join(params))
        lines.append("):")
        lines.append(f"    return {update_name}(item_id=item_id, payload=payload, db=db)")
        lines.append("")

    if spec.endpoints.delete:
        lines.append("@router.delete(\"/{item_id}\", status_code=204)")
        lines.append("async def delete_item(")
        params = [
            "    item_id: str",
            "    db: Session = Depends(get_db)",
        ]
        if spec.auth_required:
            params.append("    auth: AuthContext = Depends(get_auth_context)")
        lines.append(",\n".join(params))
        lines.append("):")
        lines.append(f"    return {delete_name}(item_id=item_id, db=db)")
        lines.append("")

    return "\n".join(lines)


def test_template(spec: ResourceSpec) -> str:
    plural = spec.plural
    return (
        "import importlib\n"
        "import unittest\n\n"
        "class TestGeneratedModules(unittest.TestCase):\n"
        "    def test_modules_import(self):\n"
        f"        modules = [\n"
        f"            \"app.endpoints_logic.{spec.version}.{plural}\",\n"
        f"            \"app.routers.{spec.version}.{plural}\",\n"
        f"            \"app.schemas.{plural}_schemas\",\n"
        f"            \"app.database.models.{plural}_models\",\n"
        "        ]\n"
        "        for module in modules:\n"
        "            with self.subTest(module=module):\n"
        "                importlib.import_module(module)\n"
    )


def python_type(field_type: str) -> str:
    mapping = {
        "String": "str",
        "Boolean": "bool",
        "Integer": "int",
        "Float": "float",
        "DateTime": "datetime",
        "UUID": "UUID",
        "EmailStr": "EmailStr",
        "Decimal": "Decimal",
    }
    if field_type.startswith("List[") and field_type.endswith("]"):
        inner = field_type[5:-1].strip()
        return f"List[{python_type(inner)}]"
    return mapping.get(field_type, field_type)


def has_foreign_keys(spec: ResourceSpec) -> bool:
    return any(relation.type == "belongs_to" for relation in spec.relations)


def has_many_to_many(spec: ResourceSpec) -> bool:
    return any(relation.type == "many_to_many" for relation in spec.relations)


def default_fk_name(relation: RelationSpec) -> str:
    target = relation.target.rstrip("s")
    return f"{target}_id"


def default_target_fk(relation: RelationSpec) -> str:
    target = relation.target.rstrip("s")
    return f"{target}_id"


def default_source_fk(spec: ResourceSpec) -> str:
    source = spec.table_name.rstrip("s")
    return f"{source}_id"


def default_join_table(spec: ResourceSpec, relation: RelationSpec) -> str:
    return f"{spec.table_name}_{relation.target}"


def ondelete_clause(relation: RelationSpec) -> str:
    if not relation.on_delete:
        return ""
    value = relation.on_delete.strip().lower().replace(" ", "_")
    mapping = {
        "cascade": "CASCADE",
        "restrict": "RESTRICT",
        "set_null": "SET NULL",
        "no_action": "NO ACTION",
    }
    sql_value = mapping.get(value, relation.on_delete)
    return f", ondelete=\"{sql_value}\""


def build_relationship_line(spec: ResourceSpec, relation: RelationSpec) -> str | None:
    target_class = to_class_name(relation.target)
    back_populates = (
        f", back_populates=\"{relation.back_populates}\""
        if relation.back_populates
        else ""
    )
    info = ", info={\"soft_delete_cascade\": True}" if relation.soft_delete_cascade else ""

    if relation.type == "belongs_to":
        return f"    {relation.name} = relationship(\"{target_class}\"{back_populates}{info})"
    if relation.type == "has_many":
        return (
            f"    {relation.name}: Mapped[List[\"{target_class}\"]] = "
            f"relationship(\"{target_class}\"{back_populates}{info})"
        )
    if relation.type == "many_to_many":
        table_name = relation.through or default_join_table(spec, relation)
        return (
            f"    {relation.name}: Mapped[List[\"{target_class}\"]] = "
            f"relationship(\"{target_class}\", secondary={table_name}{back_populates}{info})"
        )
    return None


def build_schema_fields(spec: ResourceSpec) -> list[FieldSpec]:
    fields = list(spec.fields)
    existing = {field.name for field in fields}
    for relation in spec.relations:
        if relation.type != "belongs_to":
            continue
        fk_name = relation.foreign_key or default_fk_name(relation)
        if fk_name in existing:
            continue
        fields.append(
            FieldSpec(
                name=fk_name,
                type="String",
                nullable=relation.nullable,
                unique=False,
            )
        )
        existing.add(fk_name)
    return fields


def build_relation_schema_fields(
    spec: ResourceSpec,
    relations: list[SchemaRelationSpec],
) -> list[SchemaFieldSpec]:
    relation_map = {relation.name: relation for relation in spec.relations}
    fields: list[SchemaFieldSpec] = []
    for relation in relations:
        source = relation_map.get(relation.name)
        if source is None:
            continue
        if relation.mode != "embedded":
            continue
        target_base = schema_target_base(source.target)
        field_type = (
            f"List[Base{target_base}Core]"
            if source.type in {"has_many", "many_to_many"}
            else f"Base{target_base}Core"
        )
        fields.append(
            SchemaFieldSpec(
                name=source.name,
                type=field_type,
                required=False,
                default=None,
                description=None,
                example=None,
                constraints={},
                enabled=True,
            )
        )
    return fields


def build_relation_imports(
    spec: ResourceSpec,
    relations: list[SchemaRelationSpec],
) -> list[str]:
    relation_map = {relation.name: relation for relation in spec.relations}
    imports = []
    seen = set()
    for relation in relations:
        source = relation_map.get(relation.name)
        if source is None:
            continue
        if relation.mode != "embedded":
            continue
        target_base = schema_target_base(source.target)
        module = source.target
        key = (module, target_base)
        if key in seen:
            continue
        seen.add(key)
        imports.append(
            f"from app.schemas.{module}_schemas import Base{target_base}Core"
        )
    return imports


def schema_target_base(target: str) -> str:
    return to_class_name(target.rstrip("s"))


def gather_schema_imports(fields: list[SchemaFieldSpec]) -> dict[str, bool]:
    flags = {
        "optional": False,
        "list": False,
        "datetime": False,
        "uuid": False,
        "decimal": False,
        "email": False,
        "field": False,
    }
    for field in fields:
        field_type = python_type(field.type)
        if "List[" in field_type:
            flags["list"] = True
        if "Optional[" in field_type:
            flags["optional"] = True
        if field_type == "datetime":
            flags["datetime"] = True
        if field_type == "UUID":
            flags["uuid"] = True
        if field_type == "Decimal":
            flags["decimal"] = True
        if field_type == "EmailStr":
            flags["email"] = True
        constraints = field_constraints(field)
        if constraints or field.default is not None:
            flags["field"] = True
    if any(not field.required for field in fields):
        flags["optional"] = True
    return flags


def field_constraints(field: SchemaFieldSpec) -> dict[str, Any]:
    payload = {}
    for key in (
        "min_length",
        "max_length",
        "pattern",
        "ge",
        "le",
        "gt",
        "lt",
        "min_items",
        "max_items",
    ):
        value = field.constraints.get(key) if field.constraints else None
        if value is not None:
            payload[key] = value
    if field.description:
        payload["description"] = field.description
    if field.example is not None:
        payload["examples"] = [field.example]
    return payload


def render_schema_field(field: SchemaFieldSpec) -> str:
    annotation = python_type(field.type)
    is_required = field.required and field.default is None
    if not is_required:
        annotation = f"Optional[{annotation}]"
    constraints = field_constraints(field)
    needs_field = bool(constraints) or field.default is not None
    if needs_field:
        default_literal = "..." if is_required else python_literal(field.default)
        args = [default_literal]
        for key, value in constraints.items():
            args.append(f"{key}={python_literal(value)}")
        return f"{field.name}: {annotation} = Field({', '.join(args)})"
    if is_required:
        return f"{field.name}: {annotation}"
    return f"{field.name}: {annotation} = None"


def python_literal(value: Any) -> str:
    if value is None:
        return "None"
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return repr(value)
    if isinstance(value, list):
        return "[" + ", ".join(python_literal(item) for item in value) + "]"
    if isinstance(value, dict):
        items = ", ".join(
            f"{python_literal(key)}: {python_literal(val)}" for key, val in value.items()
        )
        return "{" + items + "}"
    return repr(value)


def build_custom_schema_blocks(custom: list[CustomSchemaSpec]) -> list[str]:
    blocks = []
    for schema in custom:
        blocks.append("")
        blocks.append(f"class {schema.name}(BaseModel):")
        enabled_fields = [field for field in schema.fields if field.enabled]
        for field in enabled_fields:
            blocks.append(f"    {render_schema_field(field)}")
        if not enabled_fields:
            blocks.append("    pass")
    if blocks:
        blocks.append("")
    return blocks
