from fastapi import APIRouter, Depends, HTTPException, status
import os
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr
from datetime import datetime

# Import the Supabase client's get_current_user function, aliasing it
from supabase.supabase_client import get_current_user as get_supabase_current_user

# Define o router
router = APIRouter(prefix="/auth", tags=["authentication"])

# Security configuration (still needed for JWT if any other part uses it, but local auth is removed)
SECRET_KEY = os.getenv(
    "SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 180
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "webhook-secret-key")

# Pydantic model for User
class User(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "student"
    avatar_url: Optional[str] = None
    is_active: bool = True
    created_at: datetime

# Helper function to get current user, handling optionality
def get_optional_current_user() -> Optional[User]:
    user_data = get_supabase_current_user()
    if user_data and user_data.get("user") and user_data.get("profile"):
        user_profile = user_data["profile"]
        user_auth = user_data["user"]
        return User(
            id=user_auth.id,
            email=user_auth.email,
            full_name=user_profile.get("full_name"),
            role=user_profile.get("role", "student"),
            avatar_url=user_profile.get("avatar_url"),
            is_active=user_profile.get("is_active", True),
            created_at=datetime.fromisoformat(user_profile["created_at"]) if isinstance(user_profile["created_at"], str) else user_profile["created_at"]
        )
    return None

# Dependency to get the current authenticated user
def get_current_user(current_user: User = Depends(get_optional_current_user)) -> User:
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user

# Re-export Supabase authentication functions and User model
# This allows other modules to import from auth.auth as before, but now using Supabase
__all__ = ["router", "get_current_user", "get_optional_current_user", "User"]
