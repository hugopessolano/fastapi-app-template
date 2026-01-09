from sqlalchemy import Column, ForeignKey, String, Boolean
from .base_models import Base
from sqlalchemy.orm import Mapped, relationship, mapped_column
from typing import List
import uuid

class UserTenants(Base):
    __tablename__ = "user_tenants"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'))
    tenant_id = Column(String, ForeignKey('tenants.id'))

    user = relationship("Users", back_populates="user_tenants")
    tenant = relationship("Tenants", back_populates="user_tenants")

    def __repr__(self):
        return (
            f'UserTenants(id={self.id}, user_id={self.user_id}, '
            f'tenant_id={self.tenant_id})'
        )

class Users(Base):
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    cross_tenant_allowed = Column(Boolean, default=False)

    roles: Mapped[List['UserRoles']] = relationship(
        'UserRoles',
        back_populates='user',
        info={"soft_delete_cascade": True},
    )
    user_tenants: Mapped[List['UserTenants']] = relationship(
        'UserTenants',
        back_populates='user',
        info={"soft_delete_cascade": True},
    )
    tenants: Mapped[List['Tenants']] = relationship(
        'Tenants',
        secondary='user_tenants',
        back_populates='users',
    )

    def __repr__(self):
        return f'Users(id={self.id}, name={self.name}, email={self.email}, password={self.password})'
    
class Roles(Base):
    __tablename__ = "roles"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    tenant_id = Column(String, ForeignKey('tenants.id'))

    users: Mapped[List['UserRoles']] = relationship(
        'UserRoles',
        back_populates='role',
        info={"soft_delete_cascade": True},
    )
    permissions: Mapped[List['RolePermissions']] = relationship(
        'RolePermissions',
        back_populates='role',
        info={"soft_delete_cascade": True},
    )
    tenant = relationship("Tenants", back_populates="roles")

    def __repr__(self):
        return f'Roles(id={self.id}, name={self.name}, tenant_id={self.tenant_id})'

class Permissions(Base):
    __tablename__ = "permissions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    state = Column(Boolean, nullable=False)
    description = Column(String, nullable=True)

    roles: Mapped[List['RolePermissions']] = relationship(
        'RolePermissions',
        back_populates='permission',
        info={"soft_delete_cascade": True},
    )

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
