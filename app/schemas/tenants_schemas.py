from pydantic import BaseModel
from typing import Optional
from app.schemas.base_schema import BaseSchema

class BaseTenant(BaseSchema):
    name: str
    address: str

class TenantCreate(BaseModel):
    name: str
    address: str

class TenantUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None

    class Config:
        orm_mode = True
