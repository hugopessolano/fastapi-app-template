from pydantic import BaseModel, EmailStr
from typing import List, Optional
from app.schemas.base_schema import BaseSchema
from app.schemas.tenants_schemas import BaseTenant

class BasePermission(BaseSchema):
    name: str
    state: bool
    description: str|None = None
    
    class Config:
        orm_mode = True

class BaseRole(BaseSchema):
    name: str
    tenant_id: Optional[str] = None
    role_permissions: List[BasePermission] = []

    class Config:
        orm_mode = True

class PermissionCreate(BaseModel):
    name: str
    state: bool = True
    description: str|None = None

class RoleCreate(BaseModel):
    name: str
    tenant_id: str
    role_permissions: List[str] = []

class PermissiontUpdate(BaseModel):
    name: Optional[str|None] = None
    state: Optional[bool|None] = None
    description: Optional[str|None] = None

    class Config:
        orm_mode = True

class RoleUpdate(BaseModel):
    name: Optional[str|None] = None
    role_permissions: Optional[List[str]|None] = None

    class Config:
        orm_mode = True
    

class BaseUser(BaseSchema):
    name: str
    email: EmailStr
    cross_tenant_allowed: bool
    user_roles: List[BaseRole]
    user_tenants: List[BaseTenant]

    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    cross_tenant_allowed: bool = False
    user_tenants: List[str]
    user_roles: List[str] = []


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    cross_tenant_allowed: Optional[bool] = None


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    cross_tenant_allowed: bool
    user_roles: List[BaseRole]
    user_tenants: List[BaseTenant]

    class Config:
        orm_mode = True


class UserRolePatch(BaseModel):
    user_roles: List[str]


class UserTenantPatch(BaseModel):
    user_tenants: List[str]
