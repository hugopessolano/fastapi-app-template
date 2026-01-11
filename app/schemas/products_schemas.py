from __future__ import annotations

from pydantic import BaseModel
from app.schemas.base_schema import BaseSchema
from typing import Optional

class BaseProductCore(BaseSchema):
    name: str
    sku: str
    price: float

class BaseProduct(BaseProductCore):
    pass

class ProductCreateCore(BaseModel):
    name: str
    sku: str
    price: float

class ProductCreate(ProductCreateCore):
    pass

class ProductUpdateCore(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    price: Optional[float] = None

class ProductUpdate(ProductUpdateCore):
    pass

    class Config:
        orm_mode = True
