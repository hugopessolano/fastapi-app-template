from sqlalchemy import Column, Float, String
from .base_models import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
import uuid

class Products(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=False)
    sku = Column(String, nullable=False, unique=True)
    price = Column(Float, nullable=False, unique=False)
    order_items: Mapped[List["OrderItems"]] = relationship("OrderItems", back_populates="product")
