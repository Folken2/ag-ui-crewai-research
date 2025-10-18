#!/usr/bin/env python
"""
Token-based authentication for FastAPI backend
Secure authentication using JWT tokens and environment variables
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from decouple import config

# Configuration from environment variables
SECRET_KEY = config("SECRET_KEY", default="your-secret-key-change-this-in-production")
ALGORITHM = config("ALGORITHM", default="HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = config("ACCESS_TOKEN_EXPIRE_MINUTES", default="", cast=str)
ACCESS_TOKEN_EXPIRE_MINUTES = int(ACCESS_TOKEN_EXPIRE_MINUTES) if ACCESS_TOKEN_EXPIRE_MINUTES else None

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Pydantic models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

# In-memory user database (replace with real database in production)
# WARNING: Change these passwords in production!
# For production, use environment variables for user credentials
def get_users_from_env():
    """Get users from environment variables for production security"""
    users = {}
    
    # Admin user from environment
    admin_username = config("ADMIN_USERNAME", default="admin")
    admin_password_hash = config("ADMIN_PASSWORD_HASH", default=None)
    admin_email = config("ADMIN_EMAIL", default="admin@example.com")
    admin_full_name = config("ADMIN_FULL_NAME", default="Administrator")
    
    if admin_password_hash:
        users[admin_username] = {
            "username": admin_username,
            "email": admin_email,
            "full_name": admin_full_name,
            "hashed_password": admin_password_hash,
            "disabled": False,
        }
    
    # Regular user from environment
    user_username = config("USER_USERNAME", default="user")
    user_password_hash = config("USER_PASSWORD_HASH", default=None)
    user_email = config("USER_EMAIL", default="user@example.com")
    user_full_name = config("USER_FULL_NAME", default="Regular User")
    
    if user_password_hash:
        users[user_username] = {
            "username": user_username,
            "email": user_email,
            "full_name": user_full_name,
            "hashed_password": user_password_hash,
            "disabled": False,
        }
    
    # Fallback to default users if no environment variables set
    if not users:
        users = {
            "admin": {
                "username": "admin",
                "email": "admin@example.com",
                "full_name": "Administrator",
                "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # password: secret
                "disabled": False,
            },
            "user": {
                "username": "user",
                "email": "user@example.com", 
                "full_name": "Regular User",
                "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # password: secret
                "disabled": False,
            }
        }
    
    return users

# Get users from environment or fallback to defaults
fake_users_db = get_users_from_env()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    # bcrypt passwords cannot be longer than 72 bytes
    return pwd_context.verify(plain_password[:72], hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    # bcrypt passwords cannot be longer than 72 bytes
    return pwd_context.hash(password[:72])

def get_user(db: dict, username: str) -> Optional[UserInDB]:
    """Get user from database"""
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)
    return None

def authenticate_user(fake_db: dict, username: str, password: str) -> Optional[UserInDB]:
    """Authenticate user with username and password"""
    user = get_user(fake_db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token - no expiration if expires_delta is None"""
    to_encode = data.copy()
    if expires_delta is not None:
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire})
    # If expires_delta is None, don't add exp claim = token never expires
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get current authenticated user from token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user (not disabled)"""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def generate_password_hash(password: str) -> str:
    """Generate password hash for new users"""
    return get_password_hash(password)

# Utility function to create a new user (for admin purposes)
def create_user(username: str, password: str, email: str = None, full_name: str = None) -> Dict[str, Any]:
    """Create a new user in the fake database"""
    hashed_password = get_password_hash(password)
    user_data = {
        "username": username,
        "email": email,
        "full_name": full_name,
        "hashed_password": hashed_password,
        "disabled": False,
    }
    fake_users_db[username] = user_data
    return user_data
