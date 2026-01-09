import unittest

from app.routers.registry import get_router_modules


class TestRouterRegistry(unittest.TestCase):
    def test_auth_disabled_only_includes_public_routers(self) -> None:
        routers = get_router_modules("disabled")
        self.assertEqual(routers, ["app.routers.tenants"])

    def test_auth_enabled_includes_auth_routers(self) -> None:
        routers = get_router_modules("built_in")
        self.assertEqual(
            routers,
            [
                "app.routers.tenants",
                "app.routers.roles",
                "app.routers.permissions",
                "app.routers.users",
                "app.routers.auth",
            ],
        )
