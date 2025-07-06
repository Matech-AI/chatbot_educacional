import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")  # Change in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 180

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


class User(BaseModel):
    username: str
    role: str
    disabled: Optional[bool] = None


# Mock users database - Corrigido para sincronizar com o frontend
USERS_DB = {
    "admin": {
        "username": "admin",
        "role": "admin",
        "hashed_password": pwd_context.hash("adminpass"),
        "disabled": False
    },
    "instrutor": {
        "username": "instrutor",
        "role": "instructor",
        "hashed_password": pwd_context.hash("instrutorpass"),
        "disabled": False
    },
    "aluno": {
        "username": "aluno",
        "role": "student",
        "hashed_password": pwd_context.hash("alunopass"),
        "disabled": False
    }
}


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(username: str):
    if username in USERS_DB:
        user_dict = USERS_DB[username]
        return User(**user_dict)
    return None


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, USERS_DB[username]["hashed_password"]):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(request: Request):
    """
    Parses and validates a JWT token from the 'X-Auth-Token' header.
    Includes detailed logging for diagnostics.
    """
    token = request.headers.get("x-auth-token")
    logger.info(f"--- Auth Check ---")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Attempting to use token from 'x-auth-token': {token[:30] if token else 'None'}...")

    if not token:
        logger.error("❌ 'x-auth-token' header not found.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing in 'x-auth-token' header",
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        logger.info(f"✅ Token decoded successfully for subject: {username}")

        if not username or not isinstance(username, str):
            logger.error(f"❌ 'sub' claim is missing, invalid, or not a string in payload: {payload}")
            raise credentials_exception
            
    except JWTError as e:
        logger.error(f"❌ JWT decoding failed. Error: {e}. Token: {token}")
        raise credentials_exception

    user = get_user(username=username)
    if user is None:
        logger.error(f"❌ User '{username}' from token not found in database.")
        raise credentials_exception
    
    logger.info(f"✅ User '{username}' authenticated successfully.")
    return user
