from app.logging import child_logger
from fastapi import Request
from starlette.responses import Response 
from app.auth.oauth2 import SECRET_KEY, ALGORITHM
from jose import jwt, JWTError

async def log_middleware(request:Request, call_next):
    log_dict = {"url": request.url.path,
                "method": request.method,
                "headers": dict(request.headers),
                "query_params": dict(request.query_params),
                "status_code": None,
                }
    child_logger.bind(**log_dict).debug(f'URL:{log_dict["url"]},  METHOD:{log_dict["method"]}')
    response:Response = await call_next(request)
    
    log_dict["status_code"] = response.status_code,
    log_dict["headers"] = dict(response.headers)
    child_logger.bind(**log_dict).debug(f'URL:{log_dict["url"]},  METHOD:{log_dict["method"]}. RESPONSE_CODE:{log_dict["status_code"]}')
    return response


async def add_headers_middleware(request: Request, call_next):
    user_id = None
    auth_header = request.headers.get("authorization")
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("user_id")
        except JWTError as e:
            child_logger.warning(f"Error decoding token in middleware: {e}")
            pass

    response: Response = await call_next(request)
    if user_id: 
        response.headers["X-User-ID"] = str(user_id)
    return response
