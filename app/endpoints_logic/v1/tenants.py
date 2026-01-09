from __future__ import annotations

from typing import List, TYPE_CHECKING

from fastapi import HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.database.models import Tenants, UserTenants
from app.database.soft_delete import soft_delete_by_id
from app.routers.utils import (
    calculate_next_and_last_pages,
    filter_by_tenant,
    order_by_parameter,
)
from app.schemas.tenants_schemas import TenantCreate, TenantUpdate
from app.tenants.context import TenantContext

if TYPE_CHECKING:
    from app.auth.context import AuthContext

_router_logger = None


def _get_logger():
    global _router_logger
    if _router_logger is None:
        from app.logging import child_logger

        _router_logger = child_logger.bind(router="tenants")
    return _router_logger

SORTABLE_FIELDS_TENANTS = {
    "name": Tenants.name,
    "address": Tenants.address,
    "created_at": Tenants.created_at,
    "updated_at": Tenants.updated_at,
}


def list_tenants(
    request: Request,
    response: Response,
    db: Session,
    auth: AuthContext,
    tenant_ctx: TenantContext,
    page: int,
    page_size: int,
    order_by: str,
    order_dir: str,
) -> List[Tenants]:
    offset = (page - 1) * page_size
    tenants_query = db.query(Tenants)

    if tenant_ctx.enabled and not tenant_ctx.cross_tenant_allowed:
        tenants_query = filter_by_tenant(
            tenants_query,
            Tenants,
            tenant_ctx.allowed_tenant_ids,
            column_name="id",
        )

    calculate_next_and_last_pages(tenants_query, page_size, page, request, response)
    tenants_query = order_by_parameter(
        order_by,
        order_dir,
        SORTABLE_FIELDS_TENANTS,
        tenants_query,
    )

    tenants = tenants_query.offset(offset).limit(page_size).all()

    _get_logger().bind(action="list", auth_mode=auth.mode).info("Retrieved tenants")
    return tenants


def create_tenant(
    payload: TenantCreate,
    db: Session,
    auth: AuthContext,
) -> Tenants:
    new_tenant = Tenants(**payload.model_dump())
    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)
    if auth.user:
        user_tenant = UserTenants(user_id=auth.user.id, tenant_id=new_tenant.id)
        db.add(user_tenant)
        db.commit()
    _get_logger().bind(
        action="create",
        user_id=getattr(auth.user, "id", None),
        auth_mode=auth.mode,
        tenant_id=new_tenant.id,
    ).info("Created tenant")
    return new_tenant


def update_tenant(
    tenant_id: str,
    payload: TenantUpdate,
    db: Session,
    auth: AuthContext,
    tenant_ctx: TenantContext,
) -> Tenants:
    existing_tenant_query = db.query(Tenants).filter(Tenants.id == tenant_id)
    if tenant_ctx.enabled and not tenant_ctx.cross_tenant_allowed:
        existing_tenant_query = filter_by_tenant(
            existing_tenant_query,
            Tenants,
            tenant_ctx.allowed_tenant_ids,
            column_name="id",
        )

    existing_tenant = existing_tenant_query.first()
    if not existing_tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(existing_tenant, key, value)
    db.commit()
    db.refresh(existing_tenant)
    _get_logger().bind(
        action="update",
        user_id=getattr(auth.user, "id", None),
        auth_mode=auth.mode,
        tenant_id=existing_tenant.id,
    ).info("Updated tenant")
    return existing_tenant


def delete_tenant(
    tenant_id: str,
    db: Session,
    auth: AuthContext,
    tenant_ctx: TenantContext,
) -> None:
    existing_tenant_query = db.query(Tenants).filter(Tenants.id == tenant_id)
    if tenant_ctx.enabled and not tenant_ctx.cross_tenant_allowed:
        existing_tenant_query = filter_by_tenant(
            existing_tenant_query,
            Tenants,
            tenant_ctx.allowed_tenant_ids,
            column_name="id",
        )

    existing_tenant = existing_tenant_query.first()
    if not existing_tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    deleted = soft_delete_by_id(db, Tenants, tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tenant not found")
    _get_logger().bind(
        action="delete",
        user_id=getattr(auth.user, "id", None),
        auth_mode=auth.mode,
        tenant_id=tenant_id,
    ).info("Deleted tenant")
