from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session, joinedload
from app.database.database import get_db
from app.database.models import Roles, Permissions, RolePermissions
from app.schemas.users_schemas import BaseRole, RoleCreate, RoleUpdate
from typing import List, Literal
from app.routers.utils import validate_ids, convert_role_to_baserole, filter_by_store, calculate_next_and_last_pages, order_by_parameter
from app.auth.context import AuthContext, get_auth_context
from app.logging import child_logger
from app.database.soft_delete import soft_delete_by_id


router = APIRouter(
    prefix='/roles',
    tags=['Roles']
)

router_logger = child_logger.bind(router="roles")


SORTABLE_FIELDS_ROLES = {
    "name": Roles.name,
    "created_at": Roles.created_at,
    "updated_at": Roles.updated_at,
}

@router.get("", response_model=List[BaseRole])
async def get_roles(
    request: Request,
    response: Response, 
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str = Query("created_at", description=f"Field to sort by. Allowed fields: {', '.join(SORTABLE_FIELDS_ROLES.keys())}"), 
    order_dir: Literal['asc', 'desc'] = Query("desc", description="Sort direction (asc/desc)") 
):
    offset = (page - 1) * page_size
    roles_query = db.query(Roles).options(joinedload(Roles.permissions).joinedload(RolePermissions.permission))

    if not auth.cross_store_allowed:
        roles_query = filter_by_store(roles_query, Roles, auth.allowed_store_ids)

    calculate_next_and_last_pages(roles_query, page_size, page, request, response)
    roles_query = order_by_parameter(order_by, order_dir, SORTABLE_FIELDS_ROLES, roles_query)

    roles = roles_query.offset(offset).limit(page_size).all()
    roles_with_permissions = [convert_role_to_baserole(role, db) for role in roles]

    router_logger.bind(action="list", auth_mode=auth.mode).debug("Fetched roles")
    return roles_with_permissions

@router.get("/{role_id}", response_model=BaseRole)
async def get_role(role_id: str, 
                   db: Session = Depends(get_db),
                   auth: AuthContext = Depends(get_auth_context)
                   ):
    role_query = db.query(Roles).options(joinedload(Roles.permissions).joinedload(RolePermissions.permission)).filter(Roles.id == role_id)

    if not auth.cross_store_allowed:
        role_query = filter_by_store(role_query, Roles, auth.allowed_store_ids)

    role = role_query.first()

    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    router_logger.bind(action="retrieve", role_id=role_id, auth_mode=auth.mode).debug("Fetched role")
    return convert_role_to_baserole(role, db)

@router.get("/store/{store_id}", response_model = List[BaseRole])
async def get_roles_by_store(
    request: Request,
    response: Response, 
    store_id: str, 
    db: Session = Depends(get_db), 
    auth: AuthContext = Depends(get_auth_context),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str = Query("created_at", description=f"Field to sort by. Allowed fields: {', '.join(SORTABLE_FIELDS_ROLES.keys())}"), 
    order_dir: Literal['asc', 'desc'] = Query("desc", description="Sort direction (asc/desc)") 
):
    offset = (page - 1) * page_size
    roles_query = db.query(Roles).options(joinedload(Roles.permissions).joinedload(RolePermissions.permission)).filter(Roles.store_id == store_id)

    if not auth.cross_store_allowed:
        roles_query = filter_by_store(roles_query, Roles, auth.allowed_store_ids)
    
    calculate_next_and_last_pages(roles_query, page_size, page, request, response)
    roles_query = order_by_parameter(order_by, order_dir, SORTABLE_FIELDS_ROLES, roles_query)

    roles = roles_query.offset(offset).limit(page_size).all()

    roles_with_permissions = [convert_role_to_baserole(role, db) for role in roles]
    
    router_logger.bind(action="list_by_store", store_id=store_id, auth_mode=auth.mode).debug("Fetched roles by store")
    return roles_with_permissions

@router.post("", response_model=BaseRole)
async def create_role(role: RoleCreate, 
                      db: Session = Depends(get_db),
                      auth: AuthContext = Depends(get_auth_context)
                      ):
    invalid_permissions = validate_ids(role.role_permissions,Permissions, db)
    if len(invalid_permissions) > 0:
        raise HTTPException(status_code=404, detail=f"Permission with the following ids were not found: {invalid_permissions}")

    if not auth.cross_store_allowed and role.store_id not in auth.allowed_store_ids:
        raise HTTPException(status_code=403, detail=f'User is not allowed to create Roles in store {role.store_id}')

    new_role = Roles(**role.model_dump(exclude='role_permissions'))
    permissions = list()
    for role_permission in role.role_permissions:
        new_permission = RolePermissions(role_id=new_role.id, permission_id=role_permission)
        db.add(new_permission)
        permissions.append(new_permission)
    new_role.permissions = permissions

    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    router_logger.bind(
        action="create",
        role_id=new_role.id,
        store_id=new_role.store_id,
        auth_mode=auth.mode,
        user_id=getattr(auth.user, "id", None),
    ).info("Created role")
    return convert_role_to_baserole(new_role, db)

@router.put("/{role_id}", response_model=BaseRole)
async def update_role(role_id: str, 
                      role: RoleUpdate, 
                      db: Session = Depends(get_db),
                      auth: AuthContext = Depends(get_auth_context)
                      ):
    role_query = db.query(Roles).filter(Roles.id == role_id)
    
    if not auth.cross_store_allowed:
        role_query = filter_by_store(role_query, Roles, auth.allowed_store_ids)
    
    role_model = role_query.first()

    if not role_model:
        raise HTTPException(status_code=404, detail="Role not found")
    
    if 'role_permissions' in role.model_dump(exclude_unset=True) and role.role_permissions is not None:
      invalid_permissions = validate_ids(role.role_permissions, Permissions, db)
      if len(invalid_permissions) > 0:
        raise HTTPException(status_code=404, detail=f"Permission with the following ids were not found: {invalid_permissions}")
      
      # Delete the previous permissions
      db.query(RolePermissions).filter(RolePermissions.role_id == role_id).delete()

      # Add the new ones
      permissions = list()
      for role_permission in role.role_permissions:
        new_permission = RolePermissions(role_id=role_id, permission_id=role_permission)
        db.add(new_permission)
        permissions.append(new_permission)
      role_model.permissions = permissions


    for key,value in role.model_dump(exclude_unset=True).items():
      if value is not None and key != 'role_permissions':
        setattr(role_model, key, value)
      

    db.commit()
    db.refresh(role_model)
    router_logger.bind(
        action="update",
        role_id=role_model.id,
        auth_mode=auth.mode,
        user_id=getattr(auth.user, "id", None),
    ).info("Updated role")
    return convert_role_to_baserole(role_model, db)


@router.delete("/{role_id}", status_code=204)
async def delete_role(role_id:str, 
                      db:Session = Depends(get_db),
                      auth: AuthContext = Depends(get_auth_context)
                      ):
    role_query = db.query(Roles).filter(Roles.id == role_id)
    if not auth.cross_store_allowed:
        role_query = filter_by_store(role_query, Roles, auth.allowed_store_ids)

    role = role_query.first()
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")

    deleted = soft_delete_by_id(db, Roles, role_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Role not found")
    router_logger.bind(
        action="delete",
        role_id=role_id,
        auth_mode=auth.mode,
        user_id=getattr(auth.user, "id", None),
    ).info("Deleted role")
    return
