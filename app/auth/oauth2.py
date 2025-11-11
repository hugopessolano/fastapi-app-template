from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from app.schemas.token_schemas import TokenData, Token
from app.schemas.users_schemas import BasePermission
from fastapi import Depends, status, HTTPException, Request
from fastapi.routing import APIRoute
from fastapi.security import OAuth2PasswordBearer
from app.database.database import get_db
from app.database.models import Users
from sqlalchemy.orm import Session
from app.auth.auth_utils import extract_permissions, find_permission_by_name
from typing import List

from app.config import get_settings

settings = get_settings()
SECRET_KEY = settings.secret_key
ALGORITHM = settings.token_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_access_token(token:str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        id:str = payload.get("user_id")

        if not id:
            raise credentials_exception

        token_data = TokenData(id=id)
    except JWTError:
        raise credentials_exception
    
    return token_data

def perform_validations(user:Users, endpoint:str, endpoint_method:str, function_name:str):
    if len(user.roles)==0:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail='User has no roles assigned. Unable to operate')
    
    permissions:List[BasePermission] = extract_permissions(user)
    
    endpoint_permission = find_permission_by_name(permissions, endpoint)
    endpoint_method_permission = find_permission_by_name(permissions, endpoint_method)
    function_permission = find_permission_by_name(permissions, function_name)

    if not endpoint_permission and not endpoint_method_permission and not function_permission:    
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail='User has no permission for this endpoint, method or function.')
        
    

def get_current_user(request:Request,
                    token: str | None = Depends(oauth2_scheme), 
                     db:Session = Depends(get_db),
                     ) -> Users:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    token:TokenData = verify_access_token(token, credentials_exception)
    user = db.query(Users).filter(Users.id == token.id).first()
    
    route = request.scope.get("route")
    
    if isinstance(route, APIRoute):
        endpoint = route.tags[0] if route.tags else None
        endpoint_method = f"{endpoint.lower()}_{request.method.lower()}_method" if endpoint else None
        function_name = route.endpoint.__name__
    else:
        endpoint = endpoint_method = function_name = None  

    perform_validations(user, endpoint, endpoint_method, function_name)

    return user
