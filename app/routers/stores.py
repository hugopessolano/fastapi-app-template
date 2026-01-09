from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import Stores
from app.database.soft_delete import soft_delete_by_id
from app.schemas.stores_schemas import BaseStore, StoreCreate, StoreUpdate
from app.routers.utils import filter_by_store, calculate_next_and_last_pages, order_by_parameter
from app.auth.context import AuthContext, get_auth_context
from app.logging import child_logger
from typing import List, Literal

router_logger = child_logger.bind(router="stores")

router = APIRouter(
    prefix='/stores',
    tags=['Stores']
)

SORTABLE_FIELDS_STORES = {
    "name": Stores.name,
    "address": Stores.address,
    "created_at": Stores.created_at,
    "updated_at": Stores.updated_at,
}

@router.get("", response_model=List[BaseStore])
async def get_stores(
    request: Request,
    response: Response, 
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str = Query("created_at", description=f"Field to sort by. Allowed fields: {', '.join(SORTABLE_FIELDS_STORES.keys())}"), 
    order_dir: Literal['asc', 'desc'] = Query("desc", description="Sort direction (asc/desc)") 
):
    offset = (page - 1) * page_size
    stores_query = db.query(Stores)
    
    if not auth.cross_store_allowed:
        stores_query = filter_by_store(stores_query, Stores, auth.allowed_store_ids, column_name="id")
    
    calculate_next_and_last_pages(stores_query, page_size, page, request, response)
    stores_query = order_by_parameter(order_by, order_dir, SORTABLE_FIELDS_STORES, stores_query)

    stores = stores_query.offset(offset).limit(page_size).all()

    router_logger.bind(action="list", auth_mode=auth.mode).info(
        "Retrieved stores",
    )
    return stores

@router.post("", response_model=BaseStore)
async def create_store(store: StoreCreate, 
                       db: Session = Depends(get_db),
                       auth: AuthContext = Depends(get_auth_context)
                       ):
    new_store = Stores(**store.model_dump())
    db.add(new_store)
    db.commit()
    db.refresh(new_store)
    # When authentication is enabled, link the creator to the new store for demo purposes.
    if auth.user:
        user_store = UserStores(user_id=auth.user.id, store_id=new_store.id)
        db.add(user_store)
        db.commit()
    router_logger.bind(
        action="create",
        user_id=getattr(auth.user, "id", None),
        auth_mode=auth.mode,
        store_id=new_store.id,
    ).info("Created store")
    return new_store

@router.put("/{store_id}", response_model=BaseStore)
async def update_store(store_id: str, 
                       store: StoreUpdate, 
                       db: Session = Depends(get_db),
                       auth: AuthContext = Depends(get_auth_context)
                       ):
    existing_store_query = db.query(Stores).filter(Stores.id == store_id)
    if not auth.cross_store_allowed:
        existing_store_query = filter_by_store(existing_store_query, Stores, auth.allowed_store_ids, column_name="id")
        
    existing_store = existing_store_query.first()

    if not existing_store:
        raise HTTPException(status_code=404, detail="Store not found")
    for key, value in store.model_dump(exclude_unset=True).items():
        setattr(existing_store, key, value)
    db.commit()
    db.refresh(existing_store)
    router_logger.bind(
        action="update",
        user_id=getattr(auth.user, "id", None),
        auth_mode=auth.mode,
        store_id=existing_store.id,
    ).info("Updated store")
    return existing_store

@router.delete("/{store_id}")
async def delete_store(store_id: str, 
                       db: Session = Depends(get_db),
                       auth: AuthContext = Depends(get_auth_context)
                       ):
    existing_store_query = db.query(Stores).filter(Stores.id == store_id)
    if not auth.cross_store_allowed:
        existing_store_query = filter_by_store(
            existing_store_query,
            Stores,
            auth.allowed_store_ids,
            column_name="id",
        )

    existing_store = existing_store_query.first()
    if not existing_store:
        raise HTTPException(status_code=404, detail="Store not found")

    deleted = soft_delete_by_id(db, Stores, store_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Store not found")
    router_logger.bind(
        action="delete",
        user_id=getattr(auth.user, "id", None),
        auth_mode=auth.mode,
        store_id=store_id,
    ).info("Deleted store")
