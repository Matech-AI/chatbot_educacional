"""
Módulo de Autenticação e Gerenciamento de Usuários

Este módulo contém todas as funcionalidades relacionadas à autenticação,
gerenciamento de usuários, tokens e serviços de email.
"""

from .auth import (
    User, UserCreate, UserUpdate, Token, TokenData,
    get_current_user, get_optional_current_user,
    authenticate_user, create_user, update_user, delete_user,
    change_password, reset_password, is_user_approved
)

from .auth_token_manager import (
    create_auth_token, verify_auth_token, mark_token_as_used, clean_expired_tokens
)

from .user_management import router as user_management_router

from .external_id_manager import (
    get_next_external_id, mark_external_id_as_deleted, reorganize_external_ids
)

from .email_service import (
    generate_auth_token, send_password_reset_email, send_temp_password_email,
    generate_temp_password, send_auth_email
)

__all__ = [
    # Auth models
    'User', 'UserCreate', 'UserUpdate', 'Token', 'TokenData',

    # Auth functions
    'get_current_user', 'get_optional_current_user',
    'authenticate_user', 'create_user', 'update_user', 'delete_user',
    'change_password', 'reset_password', 'is_user_approved',

    # Token management
    'create_auth_token', 'verify_auth_token', 'mark_token_as_used', 'clean_expired_tokens',

    # User management
    'user_management_router',

    # External ID management
    'get_next_external_id', 'mark_external_id_as_deleted', 'reorganize_external_ids',

    # Email service
    'generate_auth_token', 'send_password_reset_email', 'send_temp_password_email',
    'generate_temp_password', 'send_auth_email'
]
