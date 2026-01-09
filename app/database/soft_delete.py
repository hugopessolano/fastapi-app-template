from datetime import datetime, timezone
from typing import TypeVar

from sqlalchemy import event
from sqlalchemy import inspect
from sqlalchemy.orm import Session, with_loader_criteria

from app.database.models.base_models import SoftDeleteMixin

_INCLUDE_DELETED_OPTION = "include_deleted"
_TSoftDelete = TypeVar("_TSoftDelete")


def apply_soft_delete_filter(session_class: type[Session] | object) -> None:
    target = getattr(session_class, "class_", session_class)
    if getattr(target, "_soft_delete_filter_applied", False):
        return

    @event.listens_for(target, "do_orm_execute")
    def _add_soft_delete_criteria(execute_state) -> None:
        if not execute_state.is_select:
            return
        if execute_state.execution_options.get(_INCLUDE_DELETED_OPTION, False):
            return
        execute_state.statement = execute_state.statement.options(
            with_loader_criteria(
                SoftDeleteMixin,
                lambda cls: cls.deleted_at.is_(None),
                include_aliases=True,
            )
        )

    target._soft_delete_filter_applied = True


def query_with_deleted(db: Session, model: type[_TSoftDelete]):
    return db.query(model).execution_options(**{_INCLUDE_DELETED_OPTION: True})


def soft_delete_by_id(db: Session, model: type[_TSoftDelete], item_id: str) -> bool:
    instance = query_with_deleted(db, model).filter(model.id == item_id).first()
    if instance is None or instance.deleted_at is not None:
        return False

    deleted_at = _utcnow()
    _soft_delete_recursive(instance, deleted_at, set())
    db.commit()
    return True


def _soft_delete_recursive(item: SoftDeleteMixin, deleted_at: datetime, visited: set[object]) -> None:
    identity = inspect(item).identity_key
    if identity in visited:
        return
    visited.add(identity)

    if item.deleted_at is None:
        item.deleted_at = deleted_at

    mapper = inspect(item).mapper
    for relationship in mapper.relationships:
        if not relationship.info.get("soft_delete_cascade"):
            continue
        value = getattr(item, relationship.key)
        if value is None:
            continue
        if relationship.uselist:
            for child in list(value):
                _soft_delete_recursive(child, deleted_at, visited)
        else:
            _soft_delete_recursive(value, deleted_at, visited)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)
