from tools.scaffold.spec import FieldSpec, ResourceSpec


TYPE_MAP = {
    "String": "String",
    "Boolean": "Boolean",
    "Integer": "Integer",
    "Float": "Float",
    "DateTime": "DateTime",
}


def model_template(spec: ResourceSpec) -> str:
    type_imports = {TYPE_MAP[field.type] for field in spec.fields if field.type in TYPE_MAP}
    base_imports = {"Column", *type_imports}
    if spec.tenant_scoped:
        base_imports.add("ForeignKey")

    imports = ", ".join(sorted(base_imports))
    lines = [
        f"from sqlalchemy import {imports}",
        "from .base_models import Base",
        "from sqlalchemy.orm import Mapped, mapped_column",
        "import uuid",
        "",
        f"class {spec.model_class}(Base):",
        f"    __tablename__ = \"{spec.table_name}\"",
        "",
        "    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))",
    ]

    for field in spec.fields:
        type_name = TYPE_MAP.get(field.type, field.type)
        nullable = "True" if field.nullable else "False"
        unique = "True" if field.unique else "False"
        lines.append(
            f"    {field.name} = Column({type_name}, nullable={nullable}, unique={unique})"
        )

    if spec.tenant_scoped:
        lines.append("    tenant_id = Column(String, ForeignKey(\"tenants.id\"))")

    return "\n".join(lines) + "\n"


def schema_template(spec: ResourceSpec) -> str:
    base_name = spec.schema_base
    needs_datetime = any(field.type == "DateTime" for field in spec.fields)
    lines = [
        "from pydantic import BaseModel",
        "from typing import Optional",
        "from app.schemas.base_schema import BaseSchema",
    ]
    if needs_datetime:
        lines.append("from datetime import datetime")
    lines.extend(
        [
            "",
            f"class Base{base_name}(BaseSchema):",
        ]
    )
    for field in spec.fields:
        lines.append(f"    {field.name}: {python_type(field.type)}")
    lines.append("")
    lines.append(f"class {base_name}Create(BaseModel):")
    for field in spec.fields:
        lines.append(f"    {field.name}: {python_type(field.type)}")
    lines.append("")
    lines.append(f"class {base_name}Update(BaseModel):")
    for field in spec.fields:
        lines.append(f"    {field.name}: Optional[{python_type(field.type)}] = None")
    lines.append("")
    lines.append("    class Config:")
    lines.append("        orm_mode = True")
    lines.append("")
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
    }
    return mapping.get(field_type, "str")
