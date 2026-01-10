from sqlalchemy import Column, String
from .base_models import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List
import uuid

class Customers(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=False)
    email = Column(String, nullable=False, unique=True)
    phone = Column(String, nullable=True, unique=False)
    orders: Mapped[List["Orders"]] = relationship("Orders", back_populates="customer")
