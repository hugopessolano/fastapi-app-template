from app.database.models import Users, Roles, Permissions
from app.schemas.users_schemas import BasePermission
from typing import List
from sqlalchemy.inspection import inspect

def parse_permission_to_basepermission(permission:Permissions) -> BasePermission:
    permission_data:dict = {
        column.name: getattr(permission, column.name)
        for column in inspect(Permissions).c
    }
    return BasePermission(**permission_data)
    

def extract_permissions(user:Users) -> List[BasePermission]:
    roles:List[Roles] = [user_role.role for user_role in user.roles]
    role_permissions = list()
    [role_permissions.extend(role.permissions) for role in roles]

    permissions:List[Permissions] = list({role_permission.permission for role_permission in role_permissions})
    parsed_permissions:List[BasePermission] = [parse_permission_to_basepermission(permission) for permission in permissions]
    
    return parsed_permissions

def find_permission_by_name(permissions:List[BasePermission], name:str) -> BasePermission:
    found_permission = [permission for permission in permissions if permission.name == name and permission.state]
    return found_permission[0] if len(found_permission) > 0 else None

