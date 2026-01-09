from sqlalchemy import Column, String
from .base_models import Base
from sqlalchemy.orm import Mapped, relationship, mapped_column
from typing import List
import uuid

class Tenants(Base):
    __tablename__ = "tenants"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)

    user_tenants: Mapped[List['UserTenants']] = relationship(
        'UserTenants',
        back_populates='tenant',
        info={"soft_delete_cascade": True},
    )
    users: Mapped[List['Users']] = relationship(
        'Users',
        secondary='user_tenants',
        back_populates='tenants',
    )
    roles = relationship(
        "Roles",
        back_populates="tenant",
        info={"soft_delete_cascade": True},
    )
    
