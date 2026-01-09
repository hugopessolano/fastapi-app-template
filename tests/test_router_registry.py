import unittest

from app.routers.registry import get_router_modules


class TestRouterRegistry(unittest.TestCase):
    def test_auth_disabled_includes_tenants_when_enabled(self) -> None:
        routers = get_router_modules("disabled", tenants_enabled=True)
        self.assertEqual(routers, ["app.routers.v1.tenants"])

    def test_auth_disabled_excludes_tenants_when_disabled(self) -> None:
        routers = get_router_modules("disabled", tenants_enabled=False)
        self.assertEqual(routers, [])

    def test_auth_enabled_includes_auth_routers(self) -> None:
        routers = get_router_modules("built_in", tenants_enabled=True)
        self.assertEqual(
            routers,
            [
                "app.routers.v1.tenants",
                "app.routers.v1.roles",
                "app.routers.v1.permissions",
                "app.routers.v1.users",
                "app.routers.v1.auth",
            ],
        )

    def test_auth_enabled_excludes_tenants_when_disabled(self) -> None:
        routers = get_router_modules("built_in", tenants_enabled=False)
        self.assertEqual(
            routers,
            [
                "app.routers.v1.roles",
                "app.routers.v1.permissions",
                "app.routers.v1.users",
                "app.routers.v1.auth",
            ],
        )
