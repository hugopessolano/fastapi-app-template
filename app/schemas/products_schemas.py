from pydantic import BaseModel
from typing import Optional
from app.schemas.base_schema import BaseSchema

class BaseProduct(BaseSchema):
    name: str
    sku: str
    price: float

class ProductCreate(BaseModel):
    name: str
    sku: str
    price: float

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    price: Optional[float] = None

    class Config:
        orm_mode = True
