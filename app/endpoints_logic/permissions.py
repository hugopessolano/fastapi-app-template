from __future__ import annotations

from typing import List, TYPE_CHECKING

from fastapi import HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.database.models import Permissions
from app.database.soft_delete import soft_delete_by_id
from app.routers.utils import calculate_next_and_last_pages, order_by_parameter

_router_logger = None


def _get_logger():
    global _router_logger
    if _router_logger is None:
        from app.logging import child_logger

        _router_logger = child_logger.bind(router="permissions")
    return _router_logger

SORTABLE_FIELDS_PERMISSIONS = {
    "name": Permissions.name,
    "created_at": Permissions.created_at,
    "updated_at": Permissions.updated_at,
}

if TYPE_CHECKING:
    from app.auth.context import AuthContext
    from app.schemas.users_schemas import BasePermission, PermissionCreate, PermissiontUpdate


def list_permissions(
    request: Request,
    response: Response,
    db: Session,
    _auth: AuthContext,
    page: int,
    page_size: int,
    order_by: str,
    order_dir: str,
) -> List[BasePermission]:
    offset = (page - 1) * page_size
    permissions_query = db.query(Permissions)

    calculate_next_and_last_pages(permissions_query, page_size, page, request, response)
    permissions_query = order_by_parameter(
        order_by,
        order_dir,
        SORTABLE_FIELDS_PERMISSIONS,
        permissions_query,
    )

    permissions = permissions_query.offset(offset).limit(page_size).all()
    _get_logger().bind(action="list").debug("Fetched permissions")
    return permissions


def get_permission_detail(
    permission_id: str,
    db: Session,
    _auth: AuthContext,
) -> BasePermission:
    permission = db.query(Permissions).filter(Permissions.id == permission_id).first()
    _get_logger().bind(action="retrieve", permission_id=permission_id).debug(
        "Fetched permission"
    )
    return permission


def create_permission(
    payload: PermissionCreate,
    db: Session,
    _auth: AuthContext,
) -> BasePermission:
    new_permission = Permissions(**payload.model_dump())
    db.add(new_permission)
    db.commit()
    db.refresh(new_permission)
    _get_logger().bind(
        action="create",
        permission_id=new_permission.id,
        name=new_permission.name,
    ).info("Created permission")
    return new_permission


def update_permission(
    permission_id: str,
    payload: PermissiontUpdate,
    db: Session,
    _auth: AuthContext,
) -> BasePermission:
    existing_permission = (
        db.query(Permissions).filter(Permissions.id == permission_id).first()
    )
    if not existing_permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(existing_permission, key, value)
    db.commit()
    db.refresh(existing_permission)
    _get_logger().bind(
        action="update",
        permission_id=permission_id,
    ).info("Updated permission")
    return existing_permission


def delete_permission(
    permission_id: str,
    db: Session,
    _auth: AuthContext,
) -> None:
    deleted = soft_delete_by_id(db, Permissions, permission_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Permission not found")
    _get_logger().bind(
        action="delete",
        permission_id=permission_id,
    ).info("Deleted permission")
