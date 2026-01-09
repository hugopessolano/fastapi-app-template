from typing import List, Literal

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app.auth.context import AuthContext, get_auth_context
from app.database.database import get_db
from app.endpoints_logic.permissions import (
    create_permission,
    delete_permission,
    get_permission_detail,
    list_permissions,
    update_permission,
)
from app.schemas.users_schemas import BasePermission, PermissionCreate, PermissiontUpdate
from app.routers.v1 import API_PREFIX

router = APIRouter(
    prefix=f"{API_PREFIX}/permissions",
    tags=["Permissions"],
)


@router.get("", response_model=List[BasePermission])
async def get_permissions(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str = Query("created_at"),
    order_dir: Literal["asc", "desc"] = Query("desc"),
):
    return list_permissions(
        request=request,
        response=response,
        db=db,
        _auth=auth,
        page=page,
        page_size=page_size,
        order_by=order_by,
        order_dir=order_dir,
    )


@router.get("/{permission_id}", response_model=BasePermission)
async def get_permission(
    permission_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    return get_permission_detail(permission_id=permission_id, db=db, _auth=auth)


@router.post("", response_model=BasePermission)
async def post_permission(
    payload: PermissionCreate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    return create_permission(payload=payload, db=db, _auth=auth)


@router.put("/{permission_id}", response_model=BasePermission)
async def put_permission(
    permission_id: str,
    payload: PermissiontUpdate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    return update_permission(
        permission_id=permission_id, payload=payload, db=db, _auth=auth
    )


@router.delete("/{permission_id}")
async def delete_permission_endpoint(
    permission_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    return delete_permission(permission_id=permission_id, db=db, _auth=auth)
