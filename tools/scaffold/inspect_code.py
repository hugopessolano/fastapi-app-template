import re
from pathlib import Path

from tools.scaffold.spec import FieldSpec


COLUMN_PATTERN = re.compile(r"^\s*(\w+)\s*=\s*Column\((\w+)", re.MULTILINE)
NULLABLE_PATTERN = re.compile(r"nullable=(True|False)")
UNIQUE_PATTERN = re.compile(r"unique=(True|False)")


def parse_fields_from_model(path: Path, tenant_scoped: bool) -> list[FieldSpec]:
    content = path.read_text(encoding="utf-8")
    fields: list[FieldSpec] = []
    for match in COLUMN_PATTERN.finditer(content):
        name = match.group(1)
        if name in {"id", "created_at", "updated_at", "deleted_at"}:
            continue
        if tenant_scoped and name == "tenant_id":
            continue
        type_name = match.group(2)
        line = content[match.start() : content.find("\n", match.start())]
        nullable_match = NULLABLE_PATTERN.search(line)
        unique_match = UNIQUE_PATTERN.search(line)
        nullable = nullable_match.group(1) == "True" if nullable_match else True
        unique = unique_match.group(1) == "True" if unique_match else False
        fields.append(
            FieldSpec(
                name=name,
                type=type_name,
                nullable=nullable,
                unique=unique,
            )
        )
    return fields


def parse_endpoints_from_router(path: Path) -> dict:
    content = path.read_text(encoding="utf-8")
    endpoints = {
        "list": "@router.get(\"\"" in content,
        "get": "@router.get(\"/{item_id}\"" in content,
        "create": "@router.post(\"\"" in content,
        "update": "@router.put(\"/{item_id}\"" in content,
        "delete": "@router.delete(\"/{item_id}\"" in content,
    }
    return endpoints
