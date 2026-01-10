from pydantic import BaseModel
from typing import Optional
from app.schemas.base_schema import BaseSchema

class BaseCustomer(BaseSchema):
    name: str
    email: str
    phone: str

class CustomerCreate(BaseModel):
    name: str
    email: str
    phone: str

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

    class Config:
        orm_mode = True
