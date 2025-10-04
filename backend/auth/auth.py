from fastapi import APIRouter
import os
from ..supabase.supabase_client import get_current_user, get_optional_current_user, User

# Define o router
router = APIRouter(prefix="/auth", tags=["authentication"])

# Security configuration (still needed for JWT if any other part uses it, but local auth is removed)
SECRET_KEY = os.getenv(
    "SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 180
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "webhook-secret-key")

# Re-export Supabase authentication functions and User model
# This allows other modules to import from auth.auth as before, but now using Supabase
__all__ = ["router", "get_current_user", "get_optional_current_user", "User"]
