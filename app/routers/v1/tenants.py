from typing import List, Literal

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app.auth.context import AuthContext, get_auth_context
from app.database.database import get_db
from app.endpoints_logic.tenants import (
    create_tenant,
    delete_tenant,
    list_tenants,
    update_tenant,
)
from app.schemas.tenants_schemas import BaseTenant, TenantCreate, TenantUpdate
from app.routers.v1 import API_PREFIX

router = APIRouter(
    prefix=f"{API_PREFIX}/tenants",
    tags=["Tenants"],
)


@router.get("", response_model=List[BaseTenant])
async def get_tenants(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str = Query("created_at"),
    order_dir: Literal["asc", "desc"] = Query("desc"),
):
    return list_tenants(
        request=request,
        response=response,
        db=db,
        auth=auth,
        page=page,
        page_size=page_size,
        order_by=order_by,
        order_dir=order_dir,
    )


@router.post("", response_model=BaseTenant)
async def post_tenant(
    payload: TenantCreate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    return create_tenant(payload=payload, db=db, auth=auth)


@router.put("/{tenant_id}", response_model=BaseTenant)
async def put_tenant(
    tenant_id: str,
    payload: TenantUpdate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    return update_tenant(tenant_id=tenant_id, payload=payload, db=db, auth=auth)


@router.delete("/{tenant_id}")
async def delete_tenant_endpoint(
    tenant_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    return delete_tenant(tenant_id=tenant_id, db=db, auth=auth)
