from sqlalchemy.orm import Session
from sqlalchemy.orm.query import Query
from app.database.models import Permissions, Roles, Base, Users
from typing import List
from app.schemas.users_schemas import BaseRole, BasePermission, UserResponse
from app.schemas.stores_schemas import BaseStore
from sqlalchemy.inspection import inspect
import math
from fastapi import Request, Response, HTTPException
from app.logging import child_logger

utils_logger = child_logger.bind(module="router_utils")

def validate_ids(ids_list: List[str|None], model: Base, db: Session)-> list[str|None]:
    invalid_ids = list()
    for id in ids_list:
        item = db.query(model).filter(model.id == id).first()
        if not item:
            invalid_ids.append(id)
    
    if invalid_ids:
        utils_logger.bind(model=getattr(model, "__tablename__", str(model))).warning(
            f"Invalid ids detected: {invalid_ids}"
        )
    return invalid_ids


def convert_role_to_baserole(role: Roles, db: Session) -> BaseRole:
    permissions_list = []
    for rp in role.permissions:  # Assuming 'permissions' is the backref from RolePermissions
        permission = db.query(Permissions).filter(Permissions.id == rp.permission_id).first()
        if permission:
            permission_data = {
                column.name: getattr(permission, column.name)
                for column in inspect(Permissions).c
            }
            permissions_list.append(BasePermission(**permission_data))

    return BaseRole(
        id=role.id,
        name=role.name,
        store_id=role.store_id,
        role_permissions=permissions_list,
        created_at=role.created_at,
        updated_at=role.updated_at
    )


def convert_store_to_basestore(store):
    return BaseStore(
        id=store.id,
        created_at=store.created_at,
        updated_at=store.updated_at,
        name=store.name,
        address=store.address,
    )


def convert_user_to_response(user: Users, db: Session) -> UserResponse:
    roles_list = [convert_role_to_baserole(user_role.role, db) for user_role in user.roles]
    stores_list = [convert_store_to_basestore(user_store.store) for user_store in user.user_stores]
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        cross_store_allowed=user.cross_store_allowed,
        user_roles=roles_list,
        user_stores=stores_list,
    )

def filter_by_store(
    db_query: Query,
    model: Base,
    allowed_store_ids: List[str],
    column_name: str = "store_id",
):
    if allowed_store_ids is None:
        return db_query
    if len(allowed_store_ids) == 0:
        utils_logger.warning("User attempted to access stores without assignments.")
        raise HTTPException(status_code=403, detail="User is not assigned to any store.")

    column = getattr(model, column_name, None)
    if column is None:
        raise HTTPException(
            status_code=400,
            detail=f"Model {getattr(model, '__tablename__', str(model))} lacks column '{column_name}'",
        )
    utils_logger.bind(
        model=getattr(model, "__tablename__", str(model)),
        column=column_name,
    ).debug("Filtering query by allowed stores")
    return db_query.filter(column.in_(allowed_store_ids))

def calculate_next_and_last_pages(query:Query, page_size:int, page:int, request:Request, response:Response):
    total_elements = query.count() 
    
    if total_elements > 0:
        last_page_num = math.ceil(total_elements / page_size)
    else:
        last_page_num = 1
    
    base_url = request.url.remove_query_params('page')

    last_page_url = str(base_url.replace_query_params(page=last_page_num))
    response.headers["x-Last-Page"] = last_page_url 

    if page < last_page_num:
        next_page_num = page + 1
        next_page_url = str(base_url.replace_query_params(page=next_page_num))
        response.headers["x-Next-Page"] = next_page_url

def order_by_parameter(order_by:str, order_dir:str, sortable_fields:list, query:Query):
    if order_by not in sortable_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid order_by field: {order_by}. Allowed fields are: {', '.join(sortable_fields.keys())}"
        )

    sort_column = sortable_fields[order_by]

    if order_dir == "desc":
        query = query.order_by(sort_column.desc())
    else: # 'asc'
        query = query.order_by(sort_column.asc())

    return query
