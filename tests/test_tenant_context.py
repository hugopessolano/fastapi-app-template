import unittest

from app.auth.context import AuthContext
from app.tenants.context import build_tenant_context


class DummyTenant:
    def __init__(self, tenant_id: str) -> None:
        self.id = tenant_id


class DummyUser:
    def __init__(self, tenants: list[DummyTenant]) -> None:
        self.tenants = tenants


class DummySettings:
    def __init__(self, tenants_enabled: bool) -> None:
        self.tenants_enabled = tenants_enabled


class TestTenantContext(unittest.TestCase):
    def test_tenants_disabled_returns_disabled_context(self) -> None:
        auth = AuthContext(
            mode="built_in",
            user=None,
            is_authenticated=False,
            cross_tenant_allowed=False,
        )
        settings = DummySettings(tenants_enabled=False)

        context = build_tenant_context(auth=auth, settings=settings)

        self.assertFalse(context.enabled)
        self.assertTrue(context.cross_tenant_allowed)
        self.assertEqual(context.allowed_tenant_ids, [])

    def test_auth_disabled_returns_permissive_context(self) -> None:
        auth = AuthContext(
            mode="disabled",
            user=None,
            is_authenticated=False,
            cross_tenant_allowed=False,
        )
        settings = DummySettings(tenants_enabled=True)

        context = build_tenant_context(auth=auth, settings=settings)

        self.assertTrue(context.enabled)
        self.assertTrue(context.cross_tenant_allowed)
        self.assertEqual(context.allowed_tenant_ids, [])

    def test_tenants_enabled_uses_user_assignments(self) -> None:
        user = DummyUser([DummyTenant("tenant-1"), DummyTenant("tenant-2")])
        auth = AuthContext(
            mode="built_in",
            user=user,
            is_authenticated=True,
            cross_tenant_allowed=False,
        )
        settings = DummySettings(tenants_enabled=True)

        context = build_tenant_context(auth=auth, settings=settings)

        self.assertTrue(context.enabled)
        self.assertFalse(context.cross_tenant_allowed)
        self.assertEqual(context.allowed_tenant_ids, ["tenant-1", "tenant-2"])
