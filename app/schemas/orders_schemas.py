from pydantic import BaseModel
from typing import Optional
from app.schemas.base_schema import BaseSchema

class BaseOrder(BaseSchema):
    order_number: str
    status: str
    total: float
    customer_id: str

class OrderCreate(BaseModel):
    order_number: str
    status: str
    total: float
    customer_id: str

class OrderUpdate(BaseModel):
    order_number: Optional[str] = None
    status: Optional[str] = None
    total: Optional[float] = None
    customer_id: Optional[str] = None

    class Config:
        orm_mode = True
