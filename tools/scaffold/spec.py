import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FieldSpec:
    name: str
    type: str
    nullable: bool
    unique: bool


@dataclass(frozen=True)
class EndpointSpec:
    list: bool
    get: bool
    create: bool
    update: bool
    delete: bool


@dataclass(frozen=True)
class TestSpec:
    enabled: bool


@dataclass(frozen=True)
class ResourceSpec:
    version: str
    name: str
    plural: str
    table_name: str
    tags: list[str]
    auth_required: bool
    tenant_scoped: bool
    soft_delete: bool
    pagination: bool
    ordering: bool
    fields: list[FieldSpec]
    endpoints: EndpointSpec
    tests: TestSpec

    @property
    def model_class(self) -> str:
        return to_class_name(self.plural)

    @property
    def schema_base(self) -> str:
        return to_class_name(self.name)


def to_class_name(value: str) -> str:
    parts = value.replace("-", "_").split("_")
    return "".join(word.capitalize() for word in parts if word)


def load_spec(path: Path) -> ResourceSpec:
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_spec(data)
    return ResourceSpec(
        version=data["version"],
        name=data["name"],
        plural=data["plural"],
        table_name=data["table_name"],
        tags=data["tags"],
        auth_required=bool(data.get("auth_required", True)),
        tenant_scoped=bool(data.get("tenant_scoped", False)),
        soft_delete=bool(data.get("soft_delete", True)),
        pagination=bool(data.get("pagination", True)),
        ordering=bool(data.get("ordering", True)),
        fields=[
            FieldSpec(
                name=field["name"],
                type=field["type"],
                nullable=bool(field.get("nullable", True)),
                unique=bool(field.get("unique", False)),
            )
            for field in data.get("fields", [])
        ],
        endpoints=EndpointSpec(
            list=bool(data["endpoints"].get("list", True)),
            get=bool(data["endpoints"].get("get", True)),
            create=bool(data["endpoints"].get("create", True)),
            update=bool(data["endpoints"].get("update", True)),
            delete=bool(data["endpoints"].get("delete", True)),
        ),
        tests=TestSpec(enabled=bool(data.get("tests", {}).get("enabled", True))),
    )


def validate_spec(data: dict[str, Any]) -> None:
    required = ["version", "name", "plural", "table_name", "tags", "fields", "endpoints"]
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"Spec missing required fields: {', '.join(missing)}")
    if data.get("tenant_scoped") and not data.get("auth_required", True):
        raise ValueError("tenant_scoped requires auth_required=true.")
