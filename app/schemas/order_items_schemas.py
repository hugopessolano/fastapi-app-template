from __future__ import annotations

from pydantic import BaseModel, Field
from app.schemas.base_schema import BaseSchema
from typing import Optional

class BaseOrderItemCore(BaseSchema):
    quantity: int
    unit_price: float
    order_id: str
    product_id: str

class BaseOrderItem(BaseOrderItemCore):
    pass

class OrderItemCreateCore(BaseModel):
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., gt=0)
    order_id: str
    product_id: str

class OrderItemCreate(OrderItemCreateCore):
    pass

class OrderItemUpdateCore(BaseModel):
    quantity: Optional[int] = Field(None, gt=0)
    unit_price: Optional[float] = Field(None, gt=0)
    order_id: Optional[str] = None
    product_id: Optional[str] = None

class OrderItemUpdate(OrderItemUpdateCore):
    pass

    class Config:
        orm_mode = True
