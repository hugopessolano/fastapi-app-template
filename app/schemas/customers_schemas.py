from __future__ import annotations

from pydantic import BaseModel
from app.schemas.base_schema import BaseSchema
from typing import Optional

class BaseCustomerCore(BaseSchema):
    name: str
    email: str
    phone: Optional[str] = None

class BaseCustomer(BaseCustomerCore):
    pass

class CustomerCreateCore(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None

class CustomerCreate(CustomerCreateCore):
    pass

class CustomerUpdateCore(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

class CustomerUpdate(CustomerUpdateCore):
    pass

    class Config:
        orm_mode = True
