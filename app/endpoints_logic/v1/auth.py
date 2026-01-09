from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.database.models import Users

_router_logger = None


def _get_logger():
    global _router_logger
    if _router_logger is None:
        from app.logging import child_logger

        _router_logger = child_logger.bind(router="auth")
    return _router_logger


def login_user(username: str, password: str, db: Session) -> dict:
    user_model = db.query(Users).filter(Users.email == username).first()
    if not user_model:
        _get_logger().bind(username=username).warning("Login failed: user not found")
        raise HTTPException(status_code=403, detail="Invalid Credentials")

    try:
        from app.auth.hashing import verify

        if not verify(password, user_model.password):
            _get_logger().bind(username=username).warning("Login failed: wrong password")
            raise HTTPException(status_code=403, detail="Invalid Credentials")
    except Exception as exc:
        _get_logger().bind(username=username, error=str(exc)).warning(
            "Login failed: verification error"
        )
        raise HTTPException(status_code=403, detail="Invalid Credentials")

    from app.auth.oauth2 import create_access_token

    access_token = create_access_token({"user_id": user_model.id})
    _get_logger().bind(user_id=user_model.id).info("Login successful")

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
