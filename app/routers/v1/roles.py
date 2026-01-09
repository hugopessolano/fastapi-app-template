from typing import List, Literal

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app.auth.context import AuthContext, get_auth_context
from app.database.database import get_db
from app.endpoints_logic.v1.roles import (
    create_role,
    delete_role,
    get_role_detail,
    list_roles,
    list_roles_by_tenant,
    update_role,
)
from app.schemas.users_schemas import BaseRole, RoleCreate, RoleUpdate
from app.tenants.context import TenantContext, get_tenant_context
from app.routers.v1 import API_PREFIX

router = APIRouter(
    prefix=f"{API_PREFIX}/roles",
    tags=["Roles"],
)


@router.get("", response_model=List[BaseRole])
async def get_roles(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str = Query("created_at"),
    order_dir: Literal["asc", "desc"] = Query("desc"),
):
    return list_roles(
        request=request,
        response=response,
        db=db,
        auth=auth,
        tenant_ctx=tenant_ctx,
        page=page,
        page_size=page_size,
        order_by=order_by,
        order_dir=order_dir,
    )


@router.get("/{role_id}", response_model=BaseRole)
async def get_role(
    role_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    return get_role_detail(
        role_id=role_id,
        db=db,
        auth=auth,
        tenant_ctx=tenant_ctx,
    )


@router.get("/tenant/{tenant_id}", response_model=List[BaseRole])
async def get_roles_by_tenant(
    request: Request,
    response: Response,
    tenant_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str = Query("created_at"),
    order_dir: Literal["asc", "desc"] = Query("desc"),
):
    return list_roles_by_tenant(
        request=request,
        response=response,
        tenant_id=tenant_id,
        db=db,
        auth=auth,
        tenant_ctx=tenant_ctx,
        page=page,
        page_size=page_size,
        order_by=order_by,
        order_dir=order_dir,
    )


@router.post("", response_model=BaseRole)
async def post_role(
    payload: RoleCreate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    return create_role(payload=payload, db=db, auth=auth, tenant_ctx=tenant_ctx)


@router.put("/{role_id}", response_model=BaseRole)
async def put_role(
    role_id: str,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    return update_role(
        role_id=role_id,
        payload=payload,
        db=db,
        auth=auth,
        tenant_ctx=tenant_ctx,
    )


@router.delete("/{role_id}", status_code=204)
async def delete_role_endpoint(
    role_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
):
    return delete_role(
        role_id=role_id,
        db=db,
        auth=auth,
        tenant_ctx=tenant_ctx,
    )
