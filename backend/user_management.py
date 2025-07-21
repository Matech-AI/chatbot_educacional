from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from typing import List, Optional
import hashlib
import hmac
import json
from datetime import datetime, timedelta

from auth import (
    User, UserCreate, UserUpdate, WebhookUser, PasswordChange, PasswordReset, Token,
    authenticate_user, create_access_token, get_current_user,
    create_user, update_user, delete_user, get_all_users, get_user,
    change_password, reset_password, is_user_approved,
    load_approved_users, save_approved_users, get_user_by_external_id,
    ACCESS_TOKEN_EXPIRE_MINUTES, WEBHOOK_SECRET
)

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint - returns JWT token"""
    # Check user status before attempting to authenticate
    user_db = get_user(form_data.username)
    if not user_db:
        raise HTTPException(
            status_code=401,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user_db.disabled:
        raise HTTPException(status_code=403, detail="Sua conta está desativada.")
    
    if not user_db.approved:
        raise HTTPException(status_code=403, detail="Sua conta ainda não foi aprovada.")

    # Now, authenticate the password
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
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
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    return {"message": "Password changed successfully"}

@router.post("/reset-password")
async def reset_user_password(
    password_data: PasswordReset,
    current_user: User = Depends(get_current_user)
):
    """Reset user password (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    success = reset_password(password_data.username, password_data.new_password)
    
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "Password reset successfully"}

@router.get("/users", response_model=List[User])
async def list_users(current_user: User = Depends(get_current_user)):
    """List all users (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return get_all_users()

@router.post("/users", response_model=User)
async def create_new_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user)
):
    """Create new user (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        user = create_user(user_data)
        return user
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
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    success = delete_user(username)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully"}

@router.get("/approved-users")
async def get_approved_users(current_user: User = Depends(get_current_user)):
    """Get list of approved users (admin only)"""
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
    
    approved_users = load_approved_users()
    
    # Check if user already exists in approved list
    if any(u.get('username') == user_data.get('username') for u in approved_users):
        raise HTTPException(status_code=400, detail="User already in approved list")
    
    approved_users.append(user_data)
    save_approved_users(approved_users)
    
    return {"message": "User added to approved list"}

@router.delete("/approved-users/{username}")
async def remove_approved_user(
    username: str,
    current_user: User = Depends(get_current_user)
):
    """Remove user from approved list (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    approved_users = load_approved_users()
    approved_users = [u for u in approved_users if u.get('username') != username]
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
    signature = request.headers.get("X-Hub-Signature-256") or request.headers.get("X-Signature-256")
    
    if not signature:
        raise HTTPException(status_code=400, detail="Missing webhook signature")
    
    # Get raw payload
    payload = await request.body()
    
    # Verify signature
    if not verify_webhook_signature(payload, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    try:
        # Parse JSON payload
        data = json.loads(payload.decode())
        
        # Process webhook data in background
        background_tasks.add_task(process_webhook_user_data, data)
        
        return {"message": "Webhook received and processing"}
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {str(e)}")

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
        print(f"User with external_id {webhook_user.external_id} already exists")
        return
    
    # Create user data
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
        print(f"User with external_id {webhook_user.external_id} not found for update")
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
        print(f"User with external_id {webhook_user.external_id} not found for deletion")
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
        print(f"User with external_id {webhook_user.external_id} not found for disable")
        return
    
    try:
        user_update = UserUpdate(disabled=True, approved=False)
        update_user(existing_user.username, user_update)
        print(f"Disabled user: {existing_user.username}")
    except Exception as e:
        print(f"Error disabling user {existing_user.username}: {e}")