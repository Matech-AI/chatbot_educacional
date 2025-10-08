from .auth import (
    User,
    get_current_user,
    get_current_active_user,
    get_current_admin_user,
    create_access_token,
    verify_password,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    Token,
    TokenData
)

# Define o router
router = APIRouter(prefix="/auth", tags=["authentication"])

# Re-export the JSON-based authentication functions and User model
__all__ = [
    "router",
    "get_current_user",
    "get_current_active_user",
    "get_current_admin_user",
    "User",
    "create_access_token",
    "verify_password",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "Token",
    "TokenData"
]
