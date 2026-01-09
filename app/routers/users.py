from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session, joinedload
from typing import List, Literal

from app.database.database import get_db
from app.database.models import Users, UserTenants, Tenants, Roles, UserRoles
from app.schemas.users_schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserRolePatch,
    UserTenantPatch,
)
from app.routers.utils import (
    validate_ids,
    convert_user_to_response,
    calculate_next_and_last_pages,
    order_by_parameter,
)
from app.auth.hashing import hash_string
from app.auth.context import AuthContext, get_auth_context
from app.database.soft_delete import soft_delete_by_id
from app.logging import child_logger

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)

router_logger = child_logger.bind(router="users")


def load_user_with_relationships(db: Session, user_id: str) -> Users | None:
    return (
        db.query(Users)
        .options(
            joinedload(Users.roles).joinedload(UserRoles.role),
            joinedload(Users.user_tenants).joinedload(UserTenants.tenant),
        )
        .filter(Users.id == user_id)
        .first()
    )

SORTABLE_FIELDS_USERS = {
    "name": Users.name,
    "email": Users.email,
    "cross_tenant_allowed": Users.cross_tenant_allowed,
    "created_at": Users.created_at,
    "updated_at": Users.updated_at,
}


def ensure_user_admin(auth: AuthContext):
    if not auth.cross_tenant_allowed:
        raise HTTPException(
            status_code=403,
            detail="User management requires cross-tenant privileges",
        )


@router.get("", response_model=List[UserResponse])
async def get_users(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str = Query(
        "created_at",
        description=f"Field to sort by. Allowed fields: {', '.join(SORTABLE_FIELDS_USERS.keys())}",
    ),
    order_dir: Literal["asc", "desc"] = Query(
        "desc", description="Sort direction (asc/desc)"
    ),
):
    ensure_user_admin(auth)
    offset = (page - 1) * page_size
    users_query = (
        db.query(Users)
        .options(
            joinedload(Users.roles).joinedload(UserRoles.role),
            joinedload(Users.user_tenants).joinedload(UserTenants.tenant),
        )
    )
    calculate_next_and_last_pages(users_query, page_size, page, request, response)
    users_query = order_by_parameter(order_by, order_dir, SORTABLE_FIELDS_USERS, users_query)

    users = users_query.offset(offset).limit(page_size).all()
    router_logger.bind(action="list", auth_mode=auth.mode).debug("Fetched users")
    return [convert_user_to_response(user, db) for user in users]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    user = load_user_with_relationships(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not auth.cross_tenant_allowed and auth.user and auth.user.id != user_id:
        raise HTTPException(status_code=403, detail="Not allowed to view this user")

    router_logger.bind(action="retrieve", target_user=user_id, auth_mode=auth.mode).debug(
        "Fetched user"
    )
    return convert_user_to_response(user, db)


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    ensure_user_admin(auth)
    invalid_tenants = validate_ids(payload.user_tenants, Tenants, db)
    if invalid_tenants:
        raise HTTPException(
            status_code=404,
            detail=f"Tenants not found: {invalid_tenants}",
        )
    invalid_roles = validate_ids(payload.user_roles, Roles, db)
    if invalid_roles:
        raise HTTPException(
            status_code=404,
            detail=f"Roles not found: {invalid_roles}",
        )

    hashed_password = hash_string(payload.password)
    new_user = Users(
        name=payload.name,
        email=payload.email,
        password=hashed_password,
        cross_tenant_allowed=payload.cross_tenant_allowed,
    )
    db.add(new_user)
    db.flush()

    for tenant_id in payload.user_tenants:
        db.add(UserTenants(user_id=new_user.id, tenant_id=tenant_id))

    for role_id in payload.user_roles:
        db.add(UserRoles(user_id=new_user.id, role_id=role_id))

    db.commit()
    user = load_user_with_relationships(db, new_user.id)
    router_logger.bind(action="create", target_user=new_user.id).info("Created user")
    return convert_user_to_response(user, db)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    ensure_user_admin(auth)
    user = load_user_with_relationships(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = payload.model_dump(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        update_data["password"] = hash_string(update_data["password"])

    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    user = load_user_with_relationships(db, user_id)
    router_logger.bind(action="update", target_user=user_id).info("Updated user")
    return convert_user_to_response(user, db)


@router.patch("/{user_id}/roles", response_model=UserResponse)
async def patch_user_roles(
    user_id: str,
    payload: UserRolePatch,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    ensure_user_admin(auth)
    user = load_user_with_relationships(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    invalid_roles = validate_ids(payload.user_roles, Roles, db)
    if invalid_roles:
        raise HTTPException(
            status_code=404,
            detail=f"Roles not found: {invalid_roles}",
        )

    existing_role_ids = {role.role_id for role in user.roles}
    requested = set(payload.user_roles)

    # Add new roles
    for role_id in requested - existing_role_ids:
        db.add(UserRoles(user_id=user.id, role_id=role_id))

    # Remove missing roles
    for role_id in existing_role_ids - requested:
        db.query(UserRoles).filter(
            UserRoles.user_id == user.id, UserRoles.role_id == role_id
        ).delete(synchronize_session=False)

    db.commit()
    db.refresh(user)
    user = load_user_with_relationships(db, user_id)
    router_logger.bind(action="patch_roles", target_user=user_id).info(
        "Updated user roles"
    )
    return convert_user_to_response(user, db)


@router.patch("/{user_id}/tenants", response_model=UserResponse)
async def patch_user_tenants(
    user_id: str,
    payload: UserTenantPatch,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    ensure_user_admin(auth)
    user = load_user_with_relationships(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    invalid_tenants = validate_ids(payload.user_tenants, Tenants, db)
    if invalid_tenants:
        raise HTTPException(
            status_code=404,
            detail=f"Tenants not found: {invalid_tenants}",
        )

    existing_tenant_ids = {tenant.tenant_id for tenant in user.user_tenants}
    requested = set(payload.user_tenants)

    for tenant_id in requested - existing_tenant_ids:
        db.add(UserTenants(user_id=user.id, tenant_id=tenant_id))

    for tenant_id in existing_tenant_ids - requested:
        db.query(UserTenants).filter(
            UserTenants.user_id == user.id, UserTenants.tenant_id == tenant_id
        ).delete(synchronize_session=False)

    db.commit()
    db.refresh(user)
    user = load_user_with_relationships(db, user_id)
    router_logger.bind(action="patch_tenants", target_user=user_id).info(
        "Updated user tenants"
    )

    return convert_user_to_response(user, db)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    ensure_user_admin(auth)
    deleted = soft_delete_by_id(db, Users, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")

    router_logger.bind(action="delete", target_user=user_id).info("Deleted user")
