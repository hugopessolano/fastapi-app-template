from sqlalchemy import Column, Float, ForeignKey, Integer, String
from .base_models import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
import uuid

class OrderItems(Base):
    __tablename__ = "order_items"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    quantity = Column(Integer, nullable=False, unique=False)
    unit_price = Column(Float, nullable=False, unique=False)
    order_id = Column(String, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(String, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    order = relationship("Orders", back_populates="items")
    product = relationship("Products", back_populates="order_items")
