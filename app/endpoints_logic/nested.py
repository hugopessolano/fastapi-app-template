from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class NestedRelationConfig:
    name: str
    relation_type: str
    target_model: type


def apply_nested_relations(
    instance: Any,
    payloads: dict[str, Any],
    relations: list[NestedRelationConfig],
    db: Session,
    *,
    mode: str,
) -> None:
    for relation in relations:
        value = payloads.get(relation.name)
        if value is None or value == [] or value == {}:
            continue
        if relation.relation_type == "belongs_to":
            related = _resolve_related_instance(relation.target_model, value, db)
            setattr(instance, relation.name, related)
            continue

        if not isinstance(value, list):
            raise HTTPException(
                status_code=400,
                detail=f"Relation '{relation.name}' expects a list of objects.",
            )
        related_items = [
            _resolve_related_instance(relation.target_model, item, db) for item in value
        ]
        if mode == "update":
            current = getattr(instance, relation.name, None)
            if current is None:
                setattr(instance, relation.name, related_items)
            else:
                current.extend(related_items)
            continue
        setattr(instance, relation.name, related_items)


def _resolve_related_instance(model: type, data: Any, db: Session) -> Any:
    if isinstance(data, str):
        instance = db.query(model).filter(model.id == data).first()
        if instance is None:
            raise HTTPException(
                status_code=404,
                detail=f"{model.__name__} with id '{data}' not found.",
            )
        return instance
    if isinstance(data, dict):
        item_id = data.get("id")
        if item_id:
            instance = db.query(model).filter(model.id == item_id).first()
            if instance is not None:
                for key, value in data.items():
                    if key == "id":
                        continue
                    setattr(instance, key, value)
                return instance
        return model(**data)
    raise HTTPException(
        status_code=400,
        detail=f"Invalid payload for relation target {model.__name__}.",
    )
