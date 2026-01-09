from typing import List, Literal

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app.auth.context import AuthContext, get_auth_context
from app.database.database import get_db
from app.endpoints_logic.v1.users import (
    create_user,
    delete_user,
    get_user_detail,
    list_users,
    patch_user_roles,
    patch_user_tenants,
    update_user,
)
from app.schemas.users_schemas import (
    UserCreate,
    UserResponse,
    UserRolePatch,
    UserTenantPatch,
    UserUpdate,
)
from app.routers.v1 import API_PREFIX

router = APIRouter(
    prefix=f"{API_PREFIX}/users",
    tags=["Users"],
)


@router.get("", response_model=List[UserResponse])
async def get_users(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str = Query("created_at"),
    order_dir: Literal["asc", "desc"] = Query("desc"),
):
    return list_users(
        request=request,
        response=response,
        db=db,
        auth=auth,
        page=page,
        page_size=page_size,
        order_by=order_by,
        order_dir=order_dir,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    return get_user_detail(user_id=user_id, db=db, auth=auth)


@router.post("", response_model=UserResponse, status_code=201)
async def post_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    return create_user(payload=payload, db=db, auth=auth)


@router.put("/{user_id}", response_model=UserResponse)
async def put_user(
    user_id: str,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    return update_user(user_id=user_id, payload=payload, db=db, auth=auth)


@router.patch("/{user_id}/roles", response_model=UserResponse)
async def patch_roles(
    user_id: str,
    payload: UserRolePatch,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    return patch_user_roles(user_id=user_id, payload=payload, db=db, auth=auth)


@router.patch("/{user_id}/tenants", response_model=UserResponse)
async def patch_tenants(
    user_id: str,
    payload: UserTenantPatch,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    return patch_user_tenants(user_id=user_id, payload=payload, db=db, auth=auth)


@router.delete("/{user_id}", status_code=204)
async def delete_user_endpoint(
    user_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    return delete_user(user_id=user_id, db=db, auth=auth)
