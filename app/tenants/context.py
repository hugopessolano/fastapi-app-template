from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING

from fastapi import Depends

from app.auth.context import AuthContext, get_auth_context
if TYPE_CHECKING:
    from app.config import Settings


@dataclass
class TenantContext:
    enabled: bool
    cross_tenant_allowed: bool
    allowed_tenant_ids: List[str] = field(default_factory=list)


def build_tenant_context(auth: AuthContext, settings: "Settings") -> TenantContext:
    if not settings.tenants_enabled:
        return TenantContext(
            enabled=False,
            cross_tenant_allowed=True,
            allowed_tenant_ids=[],
        )

    if auth.mode == "disabled":
        return TenantContext(
            enabled=True,
            cross_tenant_allowed=True,
            allowed_tenant_ids=[],
        )

    if not auth.user:
        return TenantContext(
            enabled=True,
            cross_tenant_allowed=False,
            allowed_tenant_ids=[],
        )

    tenant_ids = [tenant.id for tenant in auth.user.tenants]
    return TenantContext(
        enabled=True,
        cross_tenant_allowed=auth.cross_tenant_allowed,
        allowed_tenant_ids=tenant_ids,
    )


async def get_tenant_context(
    auth: AuthContext = Depends(get_auth_context),
) -> TenantContext:
    from app.config import get_settings

    settings = get_settings()
    return build_tenant_context(auth=auth, settings=settings)
