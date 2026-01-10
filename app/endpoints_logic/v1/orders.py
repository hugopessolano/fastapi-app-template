from __future__ import annotations

from typing import List, TYPE_CHECKING

from fastapi import HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.database.models import Orders
from app.database.soft_delete import soft_delete_by_id
from app.routers.utils import calculate_next_and_last_pages, order_by_parameter, filter_by_tenant
from app.schemas.orders_schemas import OrderCreate, OrderUpdate

if TYPE_CHECKING:
    from app.auth.context import AuthContext

_router_logger = None

def _get_logger():
    global _router_logger
    if _router_logger is None:
        from app.logging import child_logger

        _router_logger = child_logger.bind(router="orders")
    return _router_logger

SORTABLE_FIELDS_ORDERS = {
    "order_number": Orders.order_number,
    "status": Orders.status,
    "total": Orders.total,
    "created_at": Orders.created_at,
    "updated_at": Orders.updated_at,
}

def list_orders(
    request: Request,
    response: Response,
    db: Session,
    auth: AuthContext,
    page: int,
    page_size: int,
    order_by: str,
    order_dir: str
) -> List[Orders]:
    offset = (page - 1) * page_size
    query = db.query(Orders)
    calculate_next_and_last_pages(query, page_size, page, request, response)
    query = order_by_parameter(order_by, order_dir, SORTABLE_FIELDS_ORDERS, query)
    items = query.offset(offset).limit(page_size).all()
    _get_logger().bind(action="list").info("Retrieved records")
    return items

def get_order(item_id: str, db: Session) -> Orders:
    item = db.query(Orders).filter(Orders.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item

def create_order(payload: OrderCreate, db: Session) -> Orders:
    item = Orders(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    _get_logger().bind(action="create").info("Created record")
    return item

def update_order(item_id: str, payload: OrderUpdate, db: Session) -> Orders:
    item = db.query(Orders).filter(Orders.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    _get_logger().bind(action="update").info("Updated record")
    return item

def delete_order(item_id: str, db: Session) -> None:
    deleted = soft_delete_by_id(db, Orders, item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Not found")
    _get_logger().bind(action="delete").info("Deleted record")
