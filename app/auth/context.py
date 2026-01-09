from dataclasses import dataclass, field
from typing import List, Optional

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.auth.oauth2 import get_current_user, oauth2_scheme
from app.config import get_settings
from app.database.database import get_db
from app.database.models import Users


@dataclass
class AuthContext:
    mode: str
    user: Optional[Users]
    is_authenticated: bool
    cross_tenant_allowed: bool
    allowed_tenant_ids: List[str] = field(default_factory=list)

    @property
    def has_user(self) -> bool:
        return self.user is not None


async def get_auth_context(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> AuthContext:
    settings = get_settings()
    mode = settings.normalized_auth_mode

    if mode == "disabled":
        return AuthContext(
            mode=mode,
            user=None,
            is_authenticated=False,
            cross_tenant_allowed=True,
            allowed_tenant_ids=[],
        )

    if mode == "custom":
        raise HTTPException(
            status_code=501,
            detail=(
                "AUTH_MODE is set to 'custom'. "
                "Provide your own dependency that returns an AuthContext-compatible object."
            ),
        )

    if not token:
        raise HTTPException(status_code=401, detail="Missing credentials")

    user = get_current_user(request, token=token, db=db)
    tenant_ids = [tenant.id for tenant in user.tenants]

    return AuthContext(
        mode=mode,
        user=user,
        is_authenticated=True,
        cross_tenant_allowed=user.cross_tenant_allowed,
        allowed_tenant_ids=tenant_ids,
    )
