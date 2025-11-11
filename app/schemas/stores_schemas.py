from pydantic import BaseModel
from typing import Optional
from app.schemas.base_schema import BaseSchema

class BaseStore(BaseSchema):
    name: str
    address: str

class StoreCreate(BaseModel):
    name: str
    address: str

class StoreUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None

    class Config:
        orm_mode = True