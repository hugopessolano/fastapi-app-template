from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_string(plain_string:str)->str:
    return pwd_context.hash(plain_string)

def verify(plain_string:str, hashed_string:str) -> bool:
    return pwd_context.verify(plain_string, hashed_string)