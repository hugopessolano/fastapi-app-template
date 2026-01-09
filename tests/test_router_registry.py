import unittest

from app.routers.registry import get_router_modules


class TestRouterRegistry(unittest.TestCase):
    def test_auth_disabled_only_includes_public_routers(self) -> None:
        routers = get_router_modules("disabled")
        self.assertEqual(routers, ["app.routers.v1.tenants"])

    def test_auth_enabled_includes_auth_routers(self) -> None:
        routers = get_router_modules("built_in")
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
