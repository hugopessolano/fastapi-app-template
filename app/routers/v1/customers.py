from typing import List, Literal

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.endpoints_logic.v1.customers import list_customers, create_customer, update_customer, delete_customer, get_customer
from app.schemas.customers_schemas import BaseCustomer, CustomerCreate, CustomerUpdate
from app.routers.v1 import API_PREFIX

router = APIRouter(
    prefix=f"{API_PREFIX}/customers",
    tags=["Customers"],
)

@router.get("", response_model=List[BaseCustomer])
async def get_items(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order_by: str = Query("created_at", description='Field to sort by. Allowed fields: name, email, phone, created_at, updated_at'),
    order_dir: Literal["asc", "desc"] = Query("desc", description="Sort direction (asc/desc)")
):
    return list_customers(
        request=request,
        response=response,
        db=db,
        page=page,
        page_size=page_size,
        order_by=order_by,
        order_dir=order_dir
    )

@router.get("/{item_id}", response_model=BaseCustomer)
async def get_item(
    item_id: str,
    db: Session = Depends(get_db)
):
    return get_customer(item_id=item_id, db=db)

@router.post("", response_model=BaseCustomer, status_code=201)
async def post_item(
    payload: CustomerCreate,
    db: Session = Depends(get_db)
):
    return create_customer(payload=payload, db=db)

@router.put("/{item_id}", response_model=BaseCustomer)
async def put_item(
    item_id: str,
    payload: CustomerUpdate,
    db: Session = Depends(get_db)
):
    return update_customer(item_id=item_id, payload=payload, db=db)

@router.delete("/{item_id}", status_code=204)
async def delete_item(
    item_id: str,
    db: Session = Depends(get_db)
):
    return delete_customer(item_id=item_id, db=db)
