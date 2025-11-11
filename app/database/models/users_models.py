from sqlalchemy import Column, ForeignKey, String, Boolean
from .base_models import Base
from sqlalchemy.orm import Mapped, relationship, mapped_column
from typing import List
import uuid

class UserStores(Base) :
    __tablename__ = "user_stores"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'))
    store_id = Column(String, ForeignKey('stores.id'))

    user = relationship("Users", back_populates="user_stores")
    store = relationship("Stores", back_populates="user_stores")

    def __repr__(self):
        return f'UserStores(id={self.id}, user_id={self.user_id}, store_id={self.store_id})'

class Users(Base):
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    cross_store_allowed = Column(Boolean, default=False)

    roles: Mapped[List['UserRoles']] = relationship('UserRoles', back_populates='user')
    user_stores: Mapped[List['UserStores']] = relationship('UserStores', back_populates='user')
    stores: Mapped[List['Stores']] = relationship('Stores', secondary='user_stores', back_populates='users')

    def __repr__(self):
        return f'Users(id={self.id}, name={self.name}, email={self.email}, password={self.password})'
    
class Roles(Base):
    __tablename__ = "roles"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    store_id = Column(String, ForeignKey('stores.id'))

    users: Mapped[List['UserRoles']] = relationship('UserRoles', back_populates='role')
    permissions: Mapped[List['RolePermissions']] = relationship('RolePermissions', back_populates='role')
    store = relationship("Stores", back_populates="roles")

    def __repr__(self):
        return f'Roles(id={self.id}, name={self.name}, store_id={self.store_id})'

class Permissions(Base):
    __tablename__ = "permissions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    state = Column(Boolean, nullable=False)
    description = Column(String, nullable=True)

    roles: Mapped[List['RolePermissions']] = relationship('RolePermissions', back_populates='permission')

    def __repr__(self):
        return f'Permissions(id={self.id}, name={self.name}, state={self.state}, description={self.description})'

class RolePermissions(Base):
    __tablename__ = "role_permissions"
    __table_args__ = {'extend_existing': True}
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    role_id = Column(String, ForeignKey('roles.id'))
    permission_id = Column(String, ForeignKey('permissions.id'))

    
    role = relationship("Roles", back_populates="permissions")
    permission = relationship("Permissions", back_populates="roles")

    def __repr__(self):
        return f'RolePermissions(id={self.id}, role_id={self.role_id}, permission_id={self.permission_id})'

class UserRoles(Base):
    __tablename__ = 'user_roles'
    __table_args__ = {'extend_existing': True}
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey('users.id'))
    role_id: Mapped[str] = mapped_column(String, ForeignKey('roles.id'))
    
    user = relationship("Users", back_populates="roles")
    role = relationship("Roles", back_populates="users")

    def __repr__(self):
        return f'UserRoles(id={self.id}, user_id={self.user_id}, role_id={self.role_id})'
