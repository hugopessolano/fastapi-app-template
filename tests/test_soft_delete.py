import unittest
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import (
    Base,
    Tenants,
    Users,
    Roles,
    Permissions,
    UserTenants,
    UserRoles,
    RolePermissions,
)
from app.database.soft_delete import (
    apply_soft_delete_filter,
    soft_delete_by_id,
    query_with_deleted,
)


class TestSoftDelete(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        apply_soft_delete_filter(self.SessionLocal)
        self.db = self.SessionLocal()

    def tearDown(self) -> None:
        self.db.close()

    def test_default_query_excludes_deleted(self) -> None:
        active_tenant = Tenants(name="Active", address="A")
        deleted_tenant = Tenants(
            name="Deleted",
            address="B",
            deleted_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        self.db.add_all([active_tenant, deleted_tenant])
        self.db.commit()

        tenants = self.db.query(Tenants).all()
        self.assertEqual(len(tenants), 1)
        self.assertEqual(tenants[0].name, "Active")

        all_tenants = query_with_deleted(self.db, Tenants).all()
        self.assertEqual(len(all_tenants), 2)

    def test_soft_delete_tenant_cascades(self) -> None:
        tenant = Tenants(name="Main", address="Address")
        role = Roles(name="Manager", tenant=tenant)
        permission = Permissions(name="tenants", state=True)
        role_permission = RolePermissions(role=role, permission=permission)
        user = Users(name="User", email="user@example.com", password="pw")
        user_tenant = UserTenants(user=user, tenant=tenant)
        user_role = UserRoles(user=user, role=role)

        self.db.add_all(
            [
                tenant,
                role,
                permission,
                role_permission,
                user,
                user_tenant,
                user_role,
            ]
        )
        self.db.commit()

        result = soft_delete_by_id(self.db, Tenants, tenant.id)
        self.assertTrue(result)

        self.assertIsNone(self.db.query(Tenants).filter(Tenants.id == tenant.id).first())
        self.assertIsNone(self.db.query(UserTenants).filter(UserTenants.tenant_id == tenant.id).first())
        self.assertIsNone(self.db.query(Roles).filter(Roles.tenant_id == tenant.id).first())
        self.assertIsNone(self.db.query(RolePermissions).filter(RolePermissions.role_id == role.id).first())
        self.assertIsNone(self.db.query(UserRoles).filter(UserRoles.role_id == role.id).first())

        tenant_deleted = query_with_deleted(self.db, Tenants).filter(Tenants.id == tenant.id).first()
        user_tenant_deleted = query_with_deleted(self.db, UserTenants).filter(
            UserTenants.tenant_id == tenant.id
        ).first()
        role_deleted = query_with_deleted(self.db, Roles).filter(Roles.id == role.id).first()
        role_permission_deleted = query_with_deleted(self.db, RolePermissions).filter(
            RolePermissions.role_id == role.id
        ).first()
        user_role_deleted = query_with_deleted(self.db, UserRoles).filter(
            UserRoles.role_id == role.id
        ).first()

        self.assertIsNotNone(tenant_deleted.deleted_at)
        self.assertIsNotNone(user_tenant_deleted.deleted_at)
        self.assertIsNotNone(role_deleted.deleted_at)
        self.assertIsNotNone(role_permission_deleted.deleted_at)
        self.assertIsNotNone(user_role_deleted.deleted_at)

        self.assertIsNotNone(self.db.query(Permissions).filter(Permissions.id == permission.id).first())

    def test_soft_delete_user_does_not_delete_tenant(self) -> None:
        tenant = Tenants(name="Keep", address="Address")
        user = Users(name="User", email="user2@example.com", password="pw")
        user_tenant = UserTenants(user=user, tenant=tenant)

        self.db.add_all([tenant, user, user_tenant])
        self.db.commit()

        result = soft_delete_by_id(self.db, Users, user.id)
        self.assertTrue(result)

        tenant_active = self.db.query(Tenants).filter(Tenants.id == tenant.id).first()
        self.assertIsNotNone(tenant_active)

        user_tenant_deleted = query_with_deleted(self.db, UserTenants).filter(
            UserTenants.user_id == user.id
        ).first()
        self.assertIsNotNone(user_tenant_deleted.deleted_at)
