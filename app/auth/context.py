from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database.models import Users


@dataclass
class AuthContext:
    mode: str
    user: Optional[Users]
    is_authenticated: bool
    cross_tenant_allowed: bool

    @property
    def has_user(self) -> bool:
        return self.user is not None


async def _get_token(request: Request) -> str | None:
    from app.auth.oauth2 import oauth2_scheme

    return await oauth2_scheme(request)


def _get_db():
    from app.database.database import get_db

    yield from get_db()


async def get_auth_context(
    request: Request,
    token: str | None = Depends(_get_token),
    db: Session = Depends(_get_db),
) -> AuthContext:
    from app.config import get_settings

    settings = get_settings()
    mode = settings.normalized_auth_mode

    if mode == "disabled":
        return AuthContext(
            mode=mode,
            user=None,
            is_authenticated=False,
            cross_tenant_allowed=True,
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

    from app.auth.oauth2 import get_current_user

    user = get_current_user(request, token=token, db=db)

    return AuthContext(
        mode=mode,
        user=user,
        is_authenticated=True,
        cross_tenant_allowed=user.cross_tenant_allowed,
    )
