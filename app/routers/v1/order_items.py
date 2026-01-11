from typing import List, Literal

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app.auth.context import AuthContext, get_auth_context
from app.database.database import get_db
from app.endpoints_logic.v1.order_items import list_order_items, create_order_item, update_order_item, delete_order_item, get_order_item
from app.schemas.order_items_schemas import BaseOrderItem, OrderItemCreate, OrderItemUpdate
from app.routers.v1 import API_PREFIX

router = APIRouter(
    prefix=f"{API_PREFIX}/order_items",
    tags=["Order Items"],
)

@router.get("", response_model=List[BaseOrderItem])
async def get_items(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str = Query("created_at", description='Field to sort by. Allowed fields: quantity, unit_price, created_at, updated_at'),
    order_dir: Literal["asc", "desc"] = Query("desc", description="Sort direction (asc/desc)")
):
    return list_order_items(
        request=request,
        response=response,
        db=db,
        auth=auth,
        page=page,
        page_size=page_size,
        order_by=order_by,
        order_dir=order_dir
    )

@router.get("/{item_id}", response_model=BaseOrderItem)
async def get_item(
    item_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context)
):
    return get_order_item(item_id=item_id, db=db)

@router.post("", response_model=BaseOrderItem, status_code=201)
async def post_item(
    payload: OrderItemCreate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context)
):
    return create_order_item(payload=payload, db=db)

@router.put("/{item_id}", response_model=BaseOrderItem)
async def put_item(
    item_id: str,
    payload: OrderItemUpdate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context)
):
    return update_order_item(item_id=item_id, payload=payload, db=db)

@router.delete("/{item_id}", status_code=204)
async def delete_item(
    item_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context)
):
    return delete_order_item(item_id=item_id, db=db)
