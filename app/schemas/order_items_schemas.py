from pydantic import BaseModel
from typing import Optional
from app.schemas.base_schema import BaseSchema

class BaseOrderItem(BaseSchema):
    quantity: int
    unit_price: float
    order_id: str
    product_id: str

class OrderItemCreate(BaseModel):
    quantity: int
    unit_price: float
    order_id: str
    product_id: str

class OrderItemUpdate(BaseModel):
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    order_id: Optional[str] = None
    product_id: Optional[str] = None

    class Config:
        orm_mode = True
