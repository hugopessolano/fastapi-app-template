import unittest
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import (
    Base,
    Stores,
    Users,
    Roles,
    Permissions,
    UserStores,
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
        active_store = Stores(name="Active", address="A")
        deleted_store = Stores(
            name="Deleted",
            address="B",
            deleted_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        self.db.add_all([active_store, deleted_store])
        self.db.commit()

        stores = self.db.query(Stores).all()
        self.assertEqual(len(stores), 1)
        self.assertEqual(stores[0].name, "Active")

        all_stores = query_with_deleted(self.db, Stores).all()
        self.assertEqual(len(all_stores), 2)

    def test_soft_delete_store_cascades(self) -> None:
        store = Stores(name="Main", address="Address")
        role = Roles(name="Manager", store=store)
        permission = Permissions(name="stores", state=True)
        role_permission = RolePermissions(role=role, permission=permission)
        user = Users(name="User", email="user@example.com", password="pw")
        user_store = UserStores(user=user, store=store)
        user_role = UserRoles(user=user, role=role)

        self.db.add_all(
            [
                store,
                role,
                permission,
                role_permission,
                user,
                user_store,
                user_role,
            ]
        )
        self.db.commit()

        result = soft_delete_by_id(self.db, Stores, store.id)
        self.assertTrue(result)

        self.assertIsNone(self.db.query(Stores).filter(Stores.id == store.id).first())
        self.assertIsNone(self.db.query(UserStores).filter(UserStores.store_id == store.id).first())
        self.assertIsNone(self.db.query(Roles).filter(Roles.store_id == store.id).first())
        self.assertIsNone(self.db.query(RolePermissions).filter(RolePermissions.role_id == role.id).first())
        self.assertIsNone(self.db.query(UserRoles).filter(UserRoles.role_id == role.id).first())

        store_deleted = query_with_deleted(self.db, Stores).filter(Stores.id == store.id).first()
        user_store_deleted = query_with_deleted(self.db, UserStores).filter(
            UserStores.store_id == store.id
        ).first()
        role_deleted = query_with_deleted(self.db, Roles).filter(Roles.id == role.id).first()
        role_permission_deleted = query_with_deleted(self.db, RolePermissions).filter(
            RolePermissions.role_id == role.id
        ).first()
        user_role_deleted = query_with_deleted(self.db, UserRoles).filter(
            UserRoles.role_id == role.id
        ).first()

        self.assertIsNotNone(store_deleted.deleted_at)
        self.assertIsNotNone(user_store_deleted.deleted_at)
        self.assertIsNotNone(role_deleted.deleted_at)
        self.assertIsNotNone(role_permission_deleted.deleted_at)
        self.assertIsNotNone(user_role_deleted.deleted_at)

        self.assertIsNotNone(self.db.query(Permissions).filter(Permissions.id == permission.id).first())

    def test_soft_delete_user_does_not_delete_store(self) -> None:
        store = Stores(name="Keep", address="Address")
        user = Users(name="User", email="user2@example.com", password="pw")
        user_store = UserStores(user=user, store=store)

        self.db.add_all([store, user, user_store])
        self.db.commit()

        result = soft_delete_by_id(self.db, Users, user.id)
        self.assertTrue(result)

        store_active = self.db.query(Stores).filter(Stores.id == store.id).first()
        self.assertIsNotNone(store_active)

        user_store_deleted = query_with_deleted(self.db, UserStores).filter(
            UserStores.user_id == user.id
        ).first()
        self.assertIsNotNone(user_store_deleted.deleted_at)
