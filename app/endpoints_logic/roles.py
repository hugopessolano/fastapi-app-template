from __future__ import annotations

from typing import List, TYPE_CHECKING

from fastapi import HTTPException, Request, Response
from sqlalchemy.orm import Session, joinedload

from app.database.models import Permissions, RolePermissions, Roles
from app.database.soft_delete import soft_delete_by_id
from app.routers.utils import (
    calculate_next_and_last_pages,
    convert_role_to_baserole,
    filter_by_tenant,
    order_by_parameter,
    validate_ids,
)

_router_logger = None


def _get_logger():
    global _router_logger
    if _router_logger is None:
        from app.logging import child_logger

        _router_logger = child_logger.bind(router="roles")
    return _router_logger

SORTABLE_FIELDS_ROLES = {
    "name": Roles.name,
    "created_at": Roles.created_at,
    "updated_at": Roles.updated_at,
}

if TYPE_CHECKING:
    from app.auth.context import AuthContext
    from app.schemas.users_schemas import BaseRole, RoleCreate, RoleUpdate


def list_roles(
    request: Request,
    response: Response,
    db: Session,
    auth: AuthContext,
    page: int,
    page_size: int,
    order_by: str,
    order_dir: str,
) -> List[BaseRole]:
    offset = (page - 1) * page_size
    roles_query = db.query(Roles).options(
        joinedload(Roles.permissions).joinedload(RolePermissions.permission)
    )

    if not auth.cross_tenant_allowed:
        roles_query = filter_by_tenant(roles_query, Roles, auth.allowed_tenant_ids)

    calculate_next_and_last_pages(roles_query, page_size, page, request, response)
    roles_query = order_by_parameter(
        order_by,
        order_dir,
        SORTABLE_FIELDS_ROLES,
        roles_query,
    )

    roles = roles_query.offset(offset).limit(page_size).all()
    roles_with_permissions = [convert_role_to_baserole(role, db) for role in roles]

    _get_logger().bind(action="list", auth_mode=auth.mode).debug("Fetched roles")
    return roles_with_permissions


def get_role_detail(
    role_id: str,
    db: Session,
    auth: AuthContext,
) -> BaseRole:
    role_query = (
        db.query(Roles)
        .options(joinedload(Roles.permissions).joinedload(RolePermissions.permission))
        .filter(Roles.id == role_id)
    )

    if not auth.cross_tenant_allowed:
        role_query = filter_by_tenant(role_query, Roles, auth.allowed_tenant_ids)

    role = role_query.first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    _get_logger().bind(action="retrieve", role_id=role_id, auth_mode=auth.mode).debug(
        "Fetched role"
    )
    return convert_role_to_baserole(role, db)


def list_roles_by_tenant(
    request: Request,
    response: Response,
    tenant_id: str,
    db: Session,
    auth: AuthContext,
    page: int,
    page_size: int,
    order_by: str,
    order_dir: str,
) -> List[BaseRole]:
    offset = (page - 1) * page_size
    roles_query = (
        db.query(Roles)
        .options(joinedload(Roles.permissions).joinedload(RolePermissions.permission))
        .filter(Roles.tenant_id == tenant_id)
    )

    if not auth.cross_tenant_allowed:
        roles_query = filter_by_tenant(roles_query, Roles, auth.allowed_tenant_ids)

    calculate_next_and_last_pages(roles_query, page_size, page, request, response)
    roles_query = order_by_parameter(
        order_by,
        order_dir,
        SORTABLE_FIELDS_ROLES,
        roles_query,
    )

    roles = roles_query.offset(offset).limit(page_size).all()
    roles_with_permissions = [convert_role_to_baserole(role, db) for role in roles]

    _get_logger().bind(
        action="list_by_tenant", tenant_id=tenant_id, auth_mode=auth.mode
    ).debug("Fetched roles by tenant")
    return roles_with_permissions


def create_role(
    payload: RoleCreate,
    db: Session,
    auth: AuthContext,
) -> BaseRole:
    invalid_permissions = validate_ids(payload.role_permissions, Permissions, db)
    if invalid_permissions:
        raise HTTPException(
            status_code=404,
            detail=f"Permission with the following ids were not found: {invalid_permissions}",
        )

    if not auth.cross_tenant_allowed and payload.tenant_id not in auth.allowed_tenant_ids:
        raise HTTPException(
            status_code=403,
            detail=f"User is not allowed to create Roles in tenant {payload.tenant_id}",
        )

    new_role = Roles(**payload.model_dump(exclude="role_permissions"))
    permissions = []
    for role_permission in payload.role_permissions:
        new_permission = RolePermissions(
            role_id=new_role.id, permission_id=role_permission
        )
        db.add(new_permission)
        permissions.append(new_permission)
    new_role.permissions = permissions

    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    _get_logger().bind(
        action="create",
        role_id=new_role.id,
        tenant_id=new_role.tenant_id,
        auth_mode=auth.mode,
        user_id=getattr(auth.user, "id", None),
    ).info("Created role")
    return convert_role_to_baserole(new_role, db)


def update_role(
    role_id: str,
    payload: RoleUpdate,
    db: Session,
    auth: AuthContext,
) -> BaseRole:
    role_query = db.query(Roles).filter(Roles.id == role_id)
    if not auth.cross_tenant_allowed:
        role_query = filter_by_tenant(role_query, Roles, auth.allowed_tenant_ids)

    role_model = role_query.first()
    if not role_model:
        raise HTTPException(status_code=404, detail="Role not found")

    update_data = payload.model_dump(exclude_unset=True)
    if "role_permissions" in update_data and payload.role_permissions is not None:
        invalid_permissions = validate_ids(payload.role_permissions, Permissions, db)
        if invalid_permissions:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Permission with the following ids were not found: "
                    f"{invalid_permissions}"
                ),
            )

        db.query(RolePermissions).filter(RolePermissions.role_id == role_id).delete()

        permissions = []
        for role_permission in payload.role_permissions:
            new_permission = RolePermissions(
                role_id=role_id, permission_id=role_permission
            )
            db.add(new_permission)
            permissions.append(new_permission)
        role_model.permissions = permissions

    for key, value in update_data.items():
        if value is not None and key != "role_permissions":
            setattr(role_model, key, value)

    db.commit()
    db.refresh(role_model)
    _get_logger().bind(
        action="update",
        role_id=role_model.id,
        auth_mode=auth.mode,
        user_id=getattr(auth.user, "id", None),
    ).info("Updated role")
    return convert_role_to_baserole(role_model, db)


def delete_role(
    role_id: str,
    db: Session,
    auth: AuthContext,
) -> None:
    role_query = db.query(Roles).filter(Roles.id == role_id)
    if not auth.cross_tenant_allowed:
        role_query = filter_by_tenant(role_query, Roles, auth.allowed_tenant_ids)

    role = role_query.first()
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")

    deleted = soft_delete_by_id(db, Roles, role_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Role not found")
    _get_logger().bind(
        action="delete",
        role_id=role_id,
        auth_mode=auth.mode,
        user_id=getattr(auth.user, "id", None),
    ).info("Deleted role")
