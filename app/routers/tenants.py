from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import Tenants, UserTenants
from app.database.soft_delete import soft_delete_by_id
from app.schemas.tenants_schemas import BaseTenant, TenantCreate, TenantUpdate
from app.routers.utils import filter_by_tenant, calculate_next_and_last_pages, order_by_parameter
from app.auth.context import AuthContext, get_auth_context
from app.logging import child_logger
from typing import List, Literal

router_logger = child_logger.bind(router="tenants")

router = APIRouter(
    prefix='/tenants',
    tags=['Tenants']
)

SORTABLE_FIELDS_TENANTS = {
    "name": Tenants.name,
    "address": Tenants.address,
    "created_at": Tenants.created_at,
    "updated_at": Tenants.updated_at,
}

@router.get("", response_model=List[BaseTenant])
async def get_tenants(
    request: Request,
    response: Response, 
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str = Query("created_at", description=f"Field to sort by. Allowed fields: {', '.join(SORTABLE_FIELDS_TENANTS.keys())}"), 
    order_dir: Literal['asc', 'desc'] = Query("desc", description="Sort direction (asc/desc)") 
):
    offset = (page - 1) * page_size
    tenants_query = db.query(Tenants)
    
    if not auth.cross_tenant_allowed:
        tenants_query = filter_by_tenant(tenants_query, Tenants, auth.allowed_tenant_ids, column_name="id")
    
    calculate_next_and_last_pages(tenants_query, page_size, page, request, response)
    tenants_query = order_by_parameter(order_by, order_dir, SORTABLE_FIELDS_TENANTS, tenants_query)

    tenants = tenants_query.offset(offset).limit(page_size).all()

    router_logger.bind(action="list", auth_mode=auth.mode).info(
        "Retrieved tenants",
    )
    return tenants

@router.post("", response_model=BaseTenant)
async def create_tenant(tenant: TenantCreate, 
                       db: Session = Depends(get_db),
                       auth: AuthContext = Depends(get_auth_context)
                       ):
    new_tenant = Tenants(**tenant.model_dump())
    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)
    # When authentication is enabled, link the creator to the new tenant for demo purposes.
    if auth.user:
        user_tenant = UserTenants(user_id=auth.user.id, tenant_id=new_tenant.id)
        db.add(user_tenant)
        db.commit()
    router_logger.bind(
        action="create",
        user_id=getattr(auth.user, "id", None),
        auth_mode=auth.mode,
        tenant_id=new_tenant.id,
    ).info("Created tenant")
    return new_tenant

@router.put("/{tenant_id}", response_model=BaseTenant)
async def update_tenant(tenant_id: str, 
                       tenant: TenantUpdate, 
                       db: Session = Depends(get_db),
                       auth: AuthContext = Depends(get_auth_context)
                       ):
    existing_tenant_query = db.query(Tenants).filter(Tenants.id == tenant_id)
    if not auth.cross_tenant_allowed:
        existing_tenant_query = filter_by_tenant(existing_tenant_query, Tenants, auth.allowed_tenant_ids, column_name="id")
        
    existing_tenant = existing_tenant_query.first()

    if not existing_tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    for key, value in tenant.model_dump(exclude_unset=True).items():
        setattr(existing_tenant, key, value)
    db.commit()
    db.refresh(existing_tenant)
    router_logger.bind(
        action="update",
        user_id=getattr(auth.user, "id", None),
        auth_mode=auth.mode,
        tenant_id=existing_tenant.id,
    ).info("Updated tenant")
    return existing_tenant

@router.delete("/{tenant_id}")
async def delete_tenant(tenant_id: str, 
                       db: Session = Depends(get_db),
                       auth: AuthContext = Depends(get_auth_context)
                       ):
    existing_tenant_query = db.query(Tenants).filter(Tenants.id == tenant_id)
    if not auth.cross_tenant_allowed:
        existing_tenant_query = filter_by_tenant(
            existing_tenant_query,
            Tenants,
            auth.allowed_tenant_ids,
            column_name="id",
        )

    existing_tenant = existing_tenant_query.first()
    if not existing_tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    deleted = soft_delete_by_id(db, Tenants, tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tenant not found")
    router_logger.bind(
        action="delete",
        user_id=getattr(auth.user, "id", None),
        auth_mode=auth.mode,
        tenant_id=tenant_id,
    ).info("Deleted tenant")
