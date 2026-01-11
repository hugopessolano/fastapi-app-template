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
class RelationSpec:
    name: str
    type: str
    target: str
    foreign_key: str | None
    through: str | None
    back_populates: str | None
    nullable: bool
    on_delete: str | None
    soft_delete_cascade: bool


@dataclass(frozen=True)
class SchemaFieldSpec:
    name: str
    type: str
    required: bool
    default: Any | None
    description: str | None
    example: Any | None
    constraints: dict[str, Any]
    enabled: bool


@dataclass(frozen=True)
class SchemaRelationSpec:
    name: str
    mode: str


@dataclass(frozen=True)
class SchemaVariantSpec:
    fields: list[SchemaFieldSpec]
    relations: list[SchemaRelationSpec]


@dataclass(frozen=True)
class CustomSchemaSpec:
    name: str
    fields: list[SchemaFieldSpec]


@dataclass(frozen=True)
class SchemaSpec:
    create: SchemaVariantSpec
    update: SchemaVariantSpec
    response: SchemaVariantSpec
    custom: list[CustomSchemaSpec]


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
    relations: list[RelationSpec]
    schemas: SchemaSpec

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
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    validate_spec(data)
    fields = [
        FieldSpec(
            name=field["name"],
            type=field["type"],
            nullable=bool(field.get("nullable", True)),
            unique=bool(field.get("unique", False)),
        )
        for field in data.get("fields", [])
    ]
    relations = [
        RelationSpec(
            name=relation["name"],
            type=relation["type"],
            target=relation["target"],
            foreign_key=relation.get("foreign_key"),
            through=relation.get("through"),
            back_populates=relation.get("back_populates"),
            nullable=bool(relation.get("nullable", False)),
            on_delete=relation.get("on_delete"),
            soft_delete_cascade=bool(relation.get("soft_delete_cascade", False)),
        )
        for relation in data.get("relations", [])
    ]
    schemas = build_schema_spec(
        data.get("schemas"),
        fields=fields,
        relations=relations,
    )
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
        fields=fields,
        endpoints=EndpointSpec(
            list=bool(data["endpoints"].get("list", True)),
            get=bool(data["endpoints"].get("get", True)),
            create=bool(data["endpoints"].get("create", True)),
            update=bool(data["endpoints"].get("update", True)),
            delete=bool(data["endpoints"].get("delete", True)),
        ),
        tests=TestSpec(enabled=bool(data.get("tests", {}).get("enabled", True))),
        relations=relations,
        schemas=schemas,
    )


def validate_spec(data: dict[str, Any]) -> None:
    required = ["version", "name", "plural", "table_name", "tags", "fields", "endpoints"]
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"Spec missing required fields: {', '.join(missing)}")
    if data.get("tenant_scoped") and not data.get("auth_required", True):
        raise ValueError("tenant_scoped requires auth_required=true.")
    relations = data.get("relations", [])
    for relation in relations:
        relation_type = relation.get("type")
        if relation_type not in {"belongs_to", "has_many", "many_to_many"}:
            raise ValueError(f"Invalid relation type: {relation_type}")
        for key in ("name", "type", "target"):
            if not relation.get(key):
                raise ValueError(f"Relation missing required field: {key}")
        if relation_type == "many_to_many" and not relation.get("through"):
            continue

    schemas = data.get("schemas")
    if schemas is None:
        return
    if not isinstance(schemas, dict):
        raise ValueError("schemas must be an object.")
    for variant in ("create", "update", "response"):
        variant_data = schemas.get(variant, {})
        if not isinstance(variant_data, dict):
            raise ValueError(f"schemas.{variant} must be an object.")
        fields = variant_data.get("fields", [])
        if fields and not isinstance(fields, list):
            raise ValueError(f"schemas.{variant}.fields must be a list.")
        for field in fields:
            if not isinstance(field, dict):
                raise ValueError(f"schemas.{variant}.fields entries must be objects.")
            if not field.get("name") or not field.get("type"):
                raise ValueError(f"schemas.{variant}.fields entries need name and type.")
        relations_data = variant_data.get("relations", [])
        if relations_data and not isinstance(relations_data, list):
            raise ValueError(f"schemas.{variant}.relations must be a list.")
        for relation in relations_data:
            if not isinstance(relation, dict):
                raise ValueError(f"schemas.{variant}.relations entries must be objects.")
            if not relation.get("name"):
                raise ValueError(f"schemas.{variant}.relations entries need name.")
            mode = relation.get("mode", "ids")
            if mode not in {"embedded", "ids", "omit"}:
                raise ValueError(f"schemas.{variant}.relations has invalid mode: {mode}")
    custom = schemas.get("custom", [])
    if custom and not isinstance(custom, list):
        raise ValueError("schemas.custom must be a list.")
    for custom_schema in custom:
        if not isinstance(custom_schema, dict):
            raise ValueError("schemas.custom entries must be objects.")
        if not custom_schema.get("name"):
            raise ValueError("schemas.custom entries require name.")
        custom_fields = custom_schema.get("fields", [])
        if custom_fields and not isinstance(custom_fields, list):
            raise ValueError("schemas.custom.fields must be a list.")
        for field in custom_fields:
            if not isinstance(field, dict):
                raise ValueError("schemas.custom.fields entries must be objects.")
            if not field.get("name") or not field.get("type"):
                raise ValueError("schemas.custom.fields entries need name and type.")


def build_schema_spec(
    data: dict[str, Any] | None,
    fields: list[FieldSpec],
    relations: list[RelationSpec],
) -> SchemaSpec:
    schema_fields = build_schema_fields(fields, relations)
    create_defaults = [
        SchemaFieldSpec(
            name=field.name,
            type=field.type,
            required=not field.nullable,
            default=None,
            description=None,
            example=None,
            constraints={},
            enabled=True,
        )
        for field in schema_fields
    ]
    update_defaults = [
        SchemaFieldSpec(
            name=field.name,
            type=field.type,
            required=False,
            default=None,
            description=None,
            example=None,
            constraints={},
            enabled=True,
        )
        for field in schema_fields
    ]
    response_defaults = [
        SchemaFieldSpec(
            name=field.name,
            type=field.type,
            required=not field.nullable,
            default=None,
            description=None,
            example=None,
            constraints={},
            enabled=True,
        )
        for field in schema_fields
    ]
    embed_defaults = data is not None
    create_data = data.get("create", {}) if data else {}
    update_data = data.get("update", {}) if data else {}
    response_data = data.get("response", {}) if data else {}
    return SchemaSpec(
        create=SchemaVariantSpec(
            fields=merge_schema_fields(create_defaults, create_data.get("fields", []), required_default=None),
            relations=build_variant_relations(create_data, relations, embed_defaults=False, include_defaults=False),
        ),
        update=SchemaVariantSpec(
            fields=merge_schema_fields(update_defaults, update_data.get("fields", []), required_default=False),
            relations=build_variant_relations(update_data, relations, embed_defaults=False, include_defaults=False),
        ),
        response=SchemaVariantSpec(
            fields=merge_schema_fields(response_defaults, response_data.get("fields", []), required_default=None),
            relations=build_variant_relations(response_data, relations, embed_defaults=embed_defaults, include_defaults=True),
        ),
        custom=build_custom_schemas(data.get("custom", []) if data else []),
    )


def build_schema_fields(
    fields: list[FieldSpec],
    relations: list[RelationSpec],
) -> list[FieldSpec]:
    merged = list(fields)
    existing = {field.name for field in merged}
    for relation in relations:
        if relation.type != "belongs_to":
            continue
        fk_name = relation.foreign_key or default_fk_name(relation)
        if fk_name in existing:
            continue
        merged.append(
            FieldSpec(
                name=fk_name,
                type="String",
                nullable=relation.nullable,
                unique=False,
            )
        )
        existing.add(fk_name)
    return merged


def default_fk_name(relation: RelationSpec) -> str:
    target = relation.target.rstrip("s")
    return f"{target}_id"


def merge_schema_fields(
    defaults: list[SchemaFieldSpec],
    overrides: list[dict[str, Any]],
    required_default: bool | None,
) -> list[SchemaFieldSpec]:
    override_map = {field.get("name"): field for field in overrides if field.get("name")}
    merged = []
    for field in defaults:
        override = override_map.pop(field.name, None)
        merged.append(parse_schema_field(field, override, required_default))
    for extra in override_map.values():
        merged.append(parse_schema_field(None, extra, required_default))
    return merged


def parse_schema_field(
    base: SchemaFieldSpec | None,
    data: dict[str, Any] | None,
    required_default: bool | None,
) -> SchemaFieldSpec:
    name = data.get("name") if data else base.name
    field_type = data.get("type") if data and data.get("type") else base.type
    if name is None or field_type is None:
        raise ValueError("Schema field requires name and type.")
    required_value = data.get("required") if data and "required" in data else None
    if required_value is None:
        if required_default is None:
            required_value = base.required if base else True
        else:
            required_value = required_default
    default_value = data.get("default") if data and "default" in data else (base.default if base else None)
    description = data.get("description") if data and "description" in data else (base.description if base else None)
    example = data.get("example") if data and "example" in data else (base.example if base else None)
    constraints = data.get("constraints") if data and "constraints" in data else (base.constraints if base else {})
    enabled = data.get("enabled") if data and "enabled" in data else (base.enabled if base else True)
    return SchemaFieldSpec(
        name=name,
        type=field_type,
        required=bool(required_value),
        default=default_value,
        description=description,
        example=example,
        constraints=constraints or {},
        enabled=bool(enabled),
    )


def build_variant_relations(
    data: dict[str, Any],
    relations: list[RelationSpec],
    embed_defaults: bool,
    include_defaults: bool,
) -> list[SchemaRelationSpec]:
    relations_data = data.get("relations", []) if data else []
    if not relations_data and not include_defaults:
        return []
    overrides = {item.get("name"): item for item in relations_data if item.get("name")}
    result = []
    for relation in relations:
        override = overrides.get(relation.name)
        if override:
            mode = override.get("mode", "ids")
        else:
            mode = default_relation_mode(relation, embed_defaults)
        result.append(SchemaRelationSpec(name=relation.name, mode=mode))
    return result


def default_relation_mode(relation: RelationSpec, embed_defaults: bool) -> str:
    if not embed_defaults:
        return "ids"
    if relation.type in {"has_many", "many_to_many"}:
        return "embedded"
    return "ids"


def build_custom_schemas(custom: list[dict[str, Any]]) -> list[CustomSchemaSpec]:
    result = []
    for entry in custom:
        fields = [
            parse_schema_field(
                None,
                field,
                required_default=True,
            )
            for field in entry.get("fields", [])
        ]
        result.append(CustomSchemaSpec(name=entry["name"], fields=fields))
    return result
