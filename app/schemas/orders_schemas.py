from __future__ import annotations

from pydantic import BaseModel
from app.schemas.base_schema import BaseSchema
from typing import Optional
from typing import List
from app.schemas.customers_schemas import BaseCustomerCore
from app.schemas.order_items_schemas import BaseOrderItemCore
from app.schemas.order_items_schemas import OrderItemCreateCore
from app.schemas.order_items_schemas import OrderItemUpdateCore

class BaseOrderCore(BaseSchema):
    order_number: str
    status: str
    total: float
    customer_id: str

class BaseOrder(BaseOrderCore):
    customer: Optional[BaseCustomerCore] = None
    items: Optional[List[BaseOrderItemCore]] = None

class OrderCreateCore(BaseModel):
    order_number: str
    status: str
    total: float
    customer_id: str

class OrderCreate(OrderCreateCore):
    items: Optional[List[OrderItemCreateCore]] = None

class OrderUpdateCore(BaseModel):
    order_number: Optional[str] = None
    status: Optional[str] = None
    total: Optional[float] = None
    customer_id: Optional[str] = None

class OrderUpdate(OrderUpdateCore):
    items: Optional[List[OrderItemUpdateCore]] = None

    class Config:
        orm_mode = True
