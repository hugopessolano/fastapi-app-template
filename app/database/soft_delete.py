from datetime import datetime, timezone
from typing import Iterable, TypeVar

from sqlalchemy import event
from sqlalchemy.orm import Session, with_loader_criteria

from app.database.models import (
    Stores,
    UserStores,
    Roles,
    RolePermissions,
    UserRoles,
    Users,
    Permissions,
)
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


def soft_delete_store(db: Session, store_id: str) -> bool:
    store = query_with_deleted(db, Stores).filter(Stores.id == store_id).first()
    if store is None or store.deleted_at is not None:
        return False

    deleted_at = _utcnow()
    store.deleted_at = deleted_at

    user_stores = query_with_deleted(db, UserStores).filter(UserStores.store_id == store_id).all()
    _mark_deleted(user_stores, deleted_at)

    roles = query_with_deleted(db, Roles).filter(Roles.store_id == store_id).all()
    role_ids = [role.id for role in roles]
    _mark_deleted(roles, deleted_at)

    if role_ids:
        role_permissions = query_with_deleted(db, RolePermissions).filter(
            RolePermissions.role_id.in_(role_ids)
        ).all()
        user_roles = query_with_deleted(db, UserRoles).filter(
            UserRoles.role_id.in_(role_ids)
        ).all()
        _mark_deleted(role_permissions, deleted_at)
        _mark_deleted(user_roles, deleted_at)

    db.commit()
    return True


def soft_delete_user(db: Session, user_id: str) -> bool:
    user = query_with_deleted(db, Users).filter(Users.id == user_id).first()
    if user is None or user.deleted_at is not None:
        return False

    deleted_at = _utcnow()
    user.deleted_at = deleted_at

    user_roles = query_with_deleted(db, UserRoles).filter(UserRoles.user_id == user_id).all()
    user_stores = query_with_deleted(db, UserStores).filter(UserStores.user_id == user_id).all()
    _mark_deleted(user_roles, deleted_at)
    _mark_deleted(user_stores, deleted_at)

    db.commit()
    return True


def soft_delete_role(db: Session, role_id: str) -> bool:
    role = query_with_deleted(db, Roles).filter(Roles.id == role_id).first()
    if role is None or role.deleted_at is not None:
        return False

    deleted_at = _utcnow()
    role.deleted_at = deleted_at

    role_permissions = query_with_deleted(db, RolePermissions).filter(
        RolePermissions.role_id == role_id
    ).all()
    user_roles = query_with_deleted(db, UserRoles).filter(UserRoles.role_id == role_id).all()
    _mark_deleted(role_permissions, deleted_at)
    _mark_deleted(user_roles, deleted_at)

    db.commit()
    return True


def soft_delete_permission(db: Session, permission_id: str) -> bool:
    permission = query_with_deleted(db, Permissions).filter(
        Permissions.id == permission_id
    ).first()
    if permission is None or permission.deleted_at is not None:
        return False

    deleted_at = _utcnow()
    permission.deleted_at = deleted_at

    role_permissions = query_with_deleted(db, RolePermissions).filter(
        RolePermissions.permission_id == permission_id
    ).all()
    _mark_deleted(role_permissions, deleted_at)

    db.commit()
    return True


def _mark_deleted(items: Iterable[object], deleted_at: datetime) -> None:
    for item in items:
        if getattr(item, "deleted_at", None) is None:
            item.deleted_at = deleted_at


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)
