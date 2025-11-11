from sqlalchemy import Column, String
from .base_models import Base
from sqlalchemy.orm import Mapped, relationship, mapped_column
from typing import List
import uuid

class Stores(Base):
    __tablename__ = "stores"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)

    user_stores: Mapped[List['UserStores']] = relationship('UserStores', back_populates='store')
    users: Mapped[List['Users']] = relationship('Users', secondary='user_stores', back_populates='stores')
    roles = relationship("Roles", back_populates="store")
    
