from sqlalchemy import Column, Float, ForeignKey, String
from .base_models import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
import uuid

class Orders(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_number = Column(String, nullable=False, unique=True)
    status = Column(String, nullable=False, unique=False)
    total = Column(Float, nullable=False, unique=False)
    customer_id = Column(String, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False)
    customer = relationship("Customers", back_populates="orders")
    items: Mapped[List["OrderItems"]] = relationship("OrderItems", back_populates="order", info={"soft_delete_cascade": True})
