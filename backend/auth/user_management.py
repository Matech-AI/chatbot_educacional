from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import List, Optional, Dict
import hashlib
import hmac
import json
from datetime import datetime, timedelta
from pydantic import BaseModel

from auth.auth import (
    User, UserCreate, UserUpdate, WebhookUser, PasswordChange, PasswordReset, Token,
    authenticate_user, create_access_token, get_current_user,
    create_user, update_user, delete_user, get_all_users, get_user,
    change_password, reset_password, is_user_approved,
    load_approved_users, save_approved_users, get_user_by_external_id,
    ACCESS_TOKEN_EXPIRE_MINUTES, WEBHOOK_SECRET, load_users_db, save_users_db,
    verify_password, update_last_login  # Adicionando estas duas funções
)
from .auth_token_manager import verify_auth_token, mark_token_as_used, clean_expired_tokens

router = APIRouter(prefix="/auth", tags=["authentication"])

# Modelo para verificação de token


class TokenVerification(BaseModel):
    token: str
    username: str


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint to get access token"""
    # Check user status before attempting to authenticate
    user_db = get_user(form_data.username)
    if not user_db:
        raise HTTPException(
            status_code=401,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verificar se o usuário está usando senha temporária
    users_db = load_users_db()
    is_temp_password = users_db[form_data.username].get(
        "is_temporary_password", False)

    # Se o usuário não está aprovado, mas está usando senha temporária, permitir o login
    if not user_db.approved and not is_temp_password:
        raise HTTPException(
            status_code=403, detail="Sua conta ainda não foi aprovada.")

    if user_db.disabled:
        raise HTTPException(
            status_code=403, detail="Sua conta está desativada.")

    # Now, authenticate the password
    if not verify_password(form_data.password, users_db[form_data.username]["hashed_password"]):
        raise HTTPException(
            status_code=401, detail="Usuário ou senha incorretos")

    # Atualizar último login
    update_last_login(form_data.username)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user_db.username,
            "role": user_db.role,
            "is_temp_password": is_temp_password  # Incluir informação na JWT
        },
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "is_temporary_password": is_temp_password  # Incluir na resposta
    }


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@router.post("/change-password")
async def change_user_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user)
):
    """Change current user's password"""
    success = change_password(
        current_user.username,
        password_data.current_password,
        password_data.new_password
    )

    if not success:
        raise HTTPException(
            status_code=400, detail="Current password is incorrect")

    return {"message": "Password changed successfully"}


@router.post("/reset-password")
async def reset_user_password(
    password_data: PasswordReset,
    current_user: User = Depends(get_current_user)
):
    """Reset user password (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    success = reset_password(password_data.username,
                             password_data.new_password)

    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "Password reset successfully"}


@router.get("/users", response_model=List[User])
async def list_users(current_user: User = Depends(get_current_user)):
    """List all users (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return get_all_users()


@router.get("/users/count")
async def count_users_by_role(current_user: User = Depends(get_current_user)):
    """Count users by role (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    users = get_all_users()
    counts = {
        "admin": 0,
        "instructor": 0,
        "student": 0,
        "total": len(users)
    }

    for user in users:
        if user.role in counts:
            counts[user.role] += 1

    return counts


@router.get("/users-count")
async def count_users_by_role_alt(current_user: User = Depends(get_current_user)):
    """Count users by role (admin only) - Alternative endpoint"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    users = get_all_users()
    counts = {
        "admin": 0,
        "instructor": 0,
        "student": 0,
    }

    for user in users:
        if user.role in counts:
            counts[user.role] += 1

    counts["total"] = sum(counts.values())

    return counts

# @router.post("/public/verify-token")
# async def verify_authentication_token(token_data: TokenVerification):
#     """Verifica o token de autenticação enviado por e-mail (rota pública)"""
#     # Verificar token
#     token_info = verify_auth_token(token_data.token)

#     if not token_info:
#         raise HTTPException(status_code=400, detail="Token inválido ou expirado")

#     if token_info["username"] != token_data.username:
#         raise HTTPException(status_code=400, detail="Token não corresponde ao usuário")

#     # Marcar token como usado
#     mark_token_as_used(token_data.token)

#     # Atualizar status do usuário para aprovado
#     user = get_user(token_data.username)
#     if not user:
#         raise HTTPException(status_code=404, detail="Usuário não encontrado")

#     user_update = UserUpdate(approved=True)
#     updated_user = update_user(token_data.username, user_update)

#     if not updated_user:
#         raise HTTPException(status_code=500, detail="Erro ao atualizar usuário")

#     return {"message": "Usuário verificado com sucesso", "username": token_data.username}


class ResendVerificationEmail(BaseModel):
    username: str


@router.post("/resend-verification")
async def resend_verification_email(
    data: ResendVerificationEmail,
    current_user: User = Depends(get_current_user)
):
    """Reenvia o e-mail de verificação para um usuário (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Verificar se o usuário existe
    user = get_user(data.username)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Verificar se o usuário já está aprovado
    if user.approved:
        return {"message": "Usuário já está aprovado"}

    # Verificar se o usuário tem e-mail
    if not user.email:
        raise HTTPException(
            status_code=400, detail="Usuário não possui e-mail cadastrado")

    # Importar funções necessárias
    from .email_service import generate_auth_token, send_auth_email, generate_temp_password, send_temp_password_email
    from auth_token_manager import create_auth_token

    # Gerar novo token de autenticação
    auth_token = generate_auth_token()
    create_auth_token(user.username, auth_token, user.email)

    # Enviar e-mail de autenticação
    send_auth_email(user.email, user.username, auth_token)

    # Gerar nova senha temporária
    temp_password = generate_temp_password()
    reset_password(user.username, temp_password)

    # Enviar e-mail com senha temporária
    send_temp_password_email(user.email, user.username, temp_password)

    return {"message": "E-mail de verificação reenviado com sucesso"}

# Modelo para resposta de criação de usuário com senha


class UserWithPassword(BaseModel):
    user: User
    generated_password: Optional[str] = None


@router.post("/users", response_model=UserWithPassword)
async def create_new_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user)
):
    """Create new user (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Definir approved como False para forçar verificação por e-mail
    user_data.approved = False

    try:
        user, generated_password = create_user(user_data)
        return {"user": user, "generated_password": generated_password}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/users/{username}", response_model=User)
async def update_existing_user(
    username: str,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update user (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    user = update_user(username, user_update)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.delete("/users/{username}")
async def delete_existing_user(
    username: str,
    current_user: User = Depends(get_current_user)
):
    """Delete user (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    if username == current_user.username:
        raise HTTPException(
            status_code=400, detail="Cannot delete your own account")

    success = delete_user(username)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User deleted successfully"}


@router.get("/approved-users")
async def get_approved_users(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return load_approved_users()


@router.post("/approved-users")
async def add_approved_user(
    user_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Add user to approved list (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Verificar se o email foi fornecido
    if not user_data.get('email'):
        raise HTTPException(status_code=400, detail="Email is required")

    approved_users = load_approved_users()

    # Check if user already exists in approved list
    if any(u.get('username') == user_data.get('username') for u in approved_users):
        raise HTTPException(
            status_code=400, detail="User already in approved list")

    # Importar funções de email
    from .email_service import generate_auth_token, send_auth_email
    from .auth_token_manager import create_auth_token

    # Gerar token de autenticação
    auth_token = generate_auth_token()
    create_auth_token(user_data.get('username'),
                      auth_token, user_data.get('email'))

    # Enviar email de autenticação
    send_auth_email(user_data.get('email'),
                    user_data.get('username'), auth_token)

    approved_users.append(user_data)
    save_approved_users(approved_users)

    return {"message": "User added to approved list and authentication email sent"}


@router.delete("/approved-users/{username}")
async def remove_approved_user(
    username: str,
    current_user: User = Depends(get_current_user)
):
    """Remove user from approved list (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    approved_users = load_approved_users()
    approved_users = [
        u for u in approved_users if u.get('username') != username]
    save_approved_users(approved_users)

    return {"message": "User removed from approved list"}


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify webhook signature"""
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(f"sha256={expected_signature}", signature)


@router.post("/webhook/users")
async def webhook_user_sync(
    request: Request,
    background_tasks: BackgroundTasks
):
    """Webhook endpoint for user synchronization from external platform"""
    # Get signature from headers
    signature = request.headers.get(
        "X-Hub-Signature-256") or request.headers.get("X-Signature-256")

    if not signature:
        raise HTTPException(
            status_code=400, detail="Missing webhook signature")

    # Get raw payload
    payload = await request.body()

    # Verify signature
    if not verify_webhook_signature(payload, signature):
        raise HTTPException(
            status_code=401, detail="Invalid webhook signature")

    try:
        # Parse JSON payload
        data = json.loads(payload.decode())

        # Process webhook data in background
        background_tasks.add_task(process_webhook_user_data, data)

        return {"message": "Webhook received and processing"}

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Webhook processing error: {str(e)}")


async def process_webhook_user_data(data: dict):
    """Process webhook user data in background"""
    try:
        webhook_user = WebhookUser(**data)

        if webhook_user.action == "create":
            await handle_user_create(webhook_user)
        elif webhook_user.action == "update":
            await handle_user_update(webhook_user)
        elif webhook_user.action == "delete":
            await handle_user_delete(webhook_user)
        elif webhook_user.action == "approve":
            await handle_user_approve(webhook_user)
        elif webhook_user.action == "disable":
            await handle_user_disable(webhook_user)

    except Exception as e:
        print(f"Error processing webhook user data: {e}")


async def handle_user_create(webhook_user: WebhookUser):
    """Handle user creation from webhook"""
    # Check if user already exists
    existing_user = get_user_by_external_id(webhook_user.external_id)
    if existing_user:
        print(
            f"User with external_id {webhook_user.external_id} already exists")
        return

    # Create user data
    if not webhook_user.email:
        print(f"User {webhook_user.username} has no email, skipping creation.")
        return

    user_data = UserCreate(
        username=webhook_user.username,
        email=webhook_user.email,
        full_name=webhook_user.full_name,
        role=webhook_user.role,
        external_id=webhook_user.external_id,
        approved=True
    )

    try:
        # Create user with default password
        create_user(user_data, f"{webhook_user.username}123")
        print(f"Created user: {webhook_user.username}")
    except Exception as e:
        print(f"Error creating user {webhook_user.username}: {e}")


async def handle_user_update(webhook_user: WebhookUser):
    """Handle user update from webhook"""
    existing_user = get_user_by_external_id(webhook_user.external_id)
    if not existing_user:
        print(
            f"User with external_id {webhook_user.external_id} not found for update")
        return

    # Update user data
    user_update = UserUpdate(
        email=webhook_user.email,
        full_name=webhook_user.full_name,
        role=webhook_user.role
    )

    try:
        update_user(existing_user.username, user_update)
        print(f"Updated user: {existing_user.username}")
    except Exception as e:
        print(f"Error updating user {existing_user.username}: {e}")


async def handle_user_delete(webhook_user: WebhookUser):
    """Handle user deletion from webhook"""
    existing_user = get_user_by_external_id(webhook_user.external_id)
    if not existing_user:
        print(
            f"User with external_id {webhook_user.external_id} not found for deletion")
        return

    try:
        delete_user(existing_user.username)
        print(f"Deleted user: {existing_user.username}")
    except Exception as e:
        print(f"Error deleting user {existing_user.username}: {e}")


async def handle_user_approve(webhook_user: WebhookUser):
    """Handle user approval from webhook"""
    existing_user = get_user_by_external_id(webhook_user.external_id)
    if existing_user:
        # Update existing user
        user_update = UserUpdate(approved=True, disabled=False)
        update_user(existing_user.username, user_update)
        print(f"Approved existing user: {existing_user.username}")
    else:
        # Add to approved users list
        approved_users = load_approved_users()
        user_data = {
            "external_id": webhook_user.external_id,
            "username": webhook_user.username,
            "email": webhook_user.email,
            "full_name": webhook_user.full_name,
            "role": webhook_user.role
        }

        if not any(u.get('external_id') == webhook_user.external_id for u in approved_users):
            approved_users.append(user_data)
            save_approved_users(approved_users)
            print(f"Added to approved users: {webhook_user.username}")


async def handle_user_disable(webhook_user: WebhookUser):
    """Handle user disable from webhook"""
    existing_user = get_user_by_external_id(webhook_user.external_id)
    if not existing_user:
        print(
            f"User with external_id {webhook_user.external_id} not found for disable")
        return

    try:
        user_update = UserUpdate(disabled=True, approved=False)
        update_user(existing_user.username, user_update)
        print(f"Disabled user: {existing_user.username}")
    except Exception as e:
        print(f"Error disabling user {existing_user.username}: {e}")


@router.get("/users/{username}/password")
async def get_user_password(
    username: str,
    current_user: User = Depends(get_current_user)
):
    """Get user password info (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Verificar se o usuário existe
    user = get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Retornar informação sobre a senha
    return {
        "password": "As senhas são armazenadas com hash criptográfico e não podem ser recuperadas. "
        "Use a opção de redefinir senha se necessário.",
        "is_temporary_password": user.is_temporary_password
    }

    # Gerar uma nova senha temporária
    from email_service import generate_temp_password
    temp_password = generate_temp_password()

    # Atualizar a senha do usuário
    success = reset_password(username, temp_password)

    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    return {"password": temp_password}


@router.post("/restore-default-passwords")
async def restore_default_passwords(
    current_user: User = Depends(get_current_user)
):
    """🚨 SEGURANÇA: Esta funcionalidade foi removida por questões de segurança"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    raise HTTPException(
        status_code=410,
        detail="Funcionalidade removida por questões de segurança. "
               "Use o sistema de redefinição de senha padrão ou crie usuários manualmente."
    )
