from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import Users
from app.auth.hashing import verify
from app.auth.oauth2 import create_access_token
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from app.logging import child_logger

router = APIRouter(
    prefix='/auth',
    tags=['Authentication']
)

router_logger = child_logger.bind(router="auth")

@router.post("/login")
async def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user_model = db.query(Users).filter(Users.email == user_credentials.username).first()
    if not user_model:
        router_logger.bind(username=user_credentials.username).warning("Login failed: user not found")
        raise HTTPException(status_code=403, detail="Invalid Credentials")
    
    try: 
        if not verify(user_credentials.password, user_model.password):
            router_logger.bind(username=user_credentials.username).warning("Login failed: wrong password")
            raise HTTPException(status_code=403, detail="Invalid Credentials")
    except Exception as exc:
        router_logger.bind(username=user_credentials.username, error=str(exc)).warning("Login failed: verification error")
        raise HTTPException(status_code=403, detail="Invalid Credentials")
    
    access_token = create_access_token({
        "user_id": user_model.id
    })
    router_logger.bind(user_id=user_model.id).info("Login successful")
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }   
    
    
    
    
