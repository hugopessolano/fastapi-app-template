from fastapi import APIRouter, Depends
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.endpoints_logic.v1.auth import login_user
from app.routers.v1 import API_PREFIX

router = APIRouter(
    prefix=f"{API_PREFIX}/auth",
    tags=["Authentication"],
)


@router.post("/login")
async def login(
    user_credentials: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    return login_user(
        username=user_credentials.username,
        password=user_credentials.password,
        db=db,
    )
