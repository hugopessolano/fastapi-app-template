from typing import List, Literal

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app.auth.context import AuthContext, get_auth_context
from app.database.database import get_db
from app.endpoints_logic.v1.orders import list_orders, create_order, update_order, delete_order, get_order
from app.schemas.orders_schemas import BaseOrder, OrderCreate, OrderUpdate
from app.routers.v1 import API_PREFIX

router = APIRouter(
    prefix=f"{API_PREFIX}/orders",
    tags=["Orders"],
)

@router.get("", response_model=List[BaseOrder])
async def get_items(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str = Query("created_at"),
    order_dir: Literal["asc", "desc"] = Query("desc")
):
    return list_orders(
        request=request,
        response=response,
        db=db,
        auth=auth,
        page=page,
        page_size=page_size,
        order_by=order_by,
        order_dir=order_dir
    )

@router.get("/{item_id}", response_model=BaseOrder)
async def get_item(
    item_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context)
):
    return get_order(item_id=item_id, db=db)

@router.post("", response_model=BaseOrder, status_code=201)
async def post_item(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context)
):
    return create_order(payload=payload, db=db)

@router.put("/{item_id}", response_model=BaseOrder)
async def put_item(
    item_id: str,
    payload: OrderUpdate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context)
):
    return update_order(item_id=item_id, payload=payload, db=db)

@router.delete("/{item_id}", status_code=204)
async def delete_item(
    item_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context)
):
    return delete_order(item_id=item_id, db=db)
