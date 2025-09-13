"""
Módulo de autenticação integrado com Supabase
Substitui o sistema de autenticação local por um mais seguro
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
import os
from datetime import datetime
import sys
import os

# Adicionar o diretório supabase ao path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'supabase'))
from supabase_client import (
    sign_up_user, sign_in_user, sign_out_user, get_current_user,
    update_user_password, reset_password, update_user_profile,
    admin_create_user, admin_delete_user, admin_list_users, admin_update_user_role
)

router = APIRouter(prefix="/auth/supabase", tags=["supabase-auth"])
security = HTTPBearer()

# ---------------------------
# Modelos Pydantic
# ---------------------------

class UserSignUp(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "student"

class UserSignIn(BaseModel):
    email: EmailStr
    password: str

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str

class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "student"

class UserRoleUpdate(BaseModel):
    role: str

# ---------------------------
# Funções auxiliares
# ---------------------------

def get_user_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Extrai e valida usuário do token JWT do Supabase
    """
    try:
        # O token JWT do Supabase já é validado automaticamente
        # pelo cliente Supabase, então só precisamos buscar o usuário atual
        user_data = get_current_user()
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido ou expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Erro na autenticação",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_admin_role(current_user: Dict[str, Any] = Depends(get_user_from_token)) -> Dict[str, Any]:
    """
    Verifica se o usuário atual é administrador
    """
    if current_user["profile"]["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Apenas administradores podem realizar esta ação."
        )
    return current_user

# ---------------------------
# Endpoints de Autenticação
# ---------------------------

@router.post("/signup")
async def signup(user_data: UserSignUp):
    """
    Registra um novo usuário
    """
    try:
        result = sign_up_user(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            role=user_data.role
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return {
            "message": "Usuário criado com sucesso",
            "user_id": result["user_id"],
            "email": result["email"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar usuário: {str(e)}"
        )

@router.post("/signin")
async def signin(user_data: UserSignIn):
    """
    Autentica um usuário
    """
    try:
        result = sign_in_user(
            email=user_data.email,
            password=user_data.password
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result["error"]
            )
        
        return {
            "message": "Login realizado com sucesso",
            "user": {
                "id": result["user"].id,
                "email": result["user"].email,
                "role": result["profile"]["role"],
                "full_name": result["profile"]["full_name"]
            },
            "session": {
                "access_token": result["session"].access_token,
                "refresh_token": result["session"].refresh_token,
                "expires_at": result["session"].expires_at
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao autenticar usuário: {str(e)}"
        )

@router.post("/signout")
async def signout():
    """
    Desconecta o usuário atual
    """
    try:
        success = sign_out_user()
        if success:
            return {"message": "Logout realizado com sucesso"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao realizar logout"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao desconectar: {str(e)}"
        )

@router.get("/me")
async def get_me(current_user: Dict[str, Any] = Depends(get_user_from_token)):
    """
    Retorna dados do usuário atual
    """
    return {
        "user": {
            "id": current_user["user"].id,
            "email": current_user["user"].email,
            "role": current_user["profile"]["role"],
            "full_name": current_user["profile"]["full_name"],
            "avatar_url": current_user["profile"].get("avatar_url"),
            "is_active": current_user["profile"]["is_active"],
            "created_at": current_user["profile"]["created_at"]
        }
    }

@router.put("/profile")
async def update_profile(
    profile_update: UserProfileUpdate,
    current_user: Dict[str, Any] = Depends(get_user_from_token)
):
    """
    Atualiza perfil do usuário atual
    """
    try:
        updates = profile_update.dict(exclude_unset=True)
        result = update_user_profile(updates)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return {
            "message": "Perfil atualizado com sucesso",
            "profile": result["profile"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar perfil: {str(e)}"
        )

@router.put("/password")
async def update_password(
    password_data: PasswordUpdate,
    current_user: Dict[str, Any] = Depends(get_user_from_token)
):
    """
    Atualiza senha do usuário atual
    """
    try:
        result = update_user_password(
            current_password=password_data.current_password,
            new_password=password_data.new_password
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return {"message": result["message"]}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar senha: {str(e)}"
        )

@router.post("/reset-password")
async def reset_password_endpoint(email: EmailStr):
    """
    Envia email de reset de senha
    """
    try:
        result = reset_password(email)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return {"message": result["message"]}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao enviar email de reset: {str(e)}"
        )

# ---------------------------
# Endpoints Administrativos
# ---------------------------

@router.post("/admin/users")
async def admin_create_user_endpoint(
    user_data: AdminUserCreate,
    current_user: Dict[str, Any] = Depends(require_admin_role)
):
    """
    Cria usuário (apenas administradores)
    """
    try:
        result = admin_create_user(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            role=user_data.role
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return {
            "message": "Usuário criado com sucesso",
            "user_id": result["user_id"],
            "profile": result["profile"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar usuário: {str(e)}"
        )

@router.get("/admin/users")
async def admin_list_users_endpoint(
    current_user: Dict[str, Any] = Depends(require_admin_role)
):
    """
    Lista todos os usuários (apenas administradores)
    """
    try:
        result = admin_list_users()
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return {
            "users": result["users"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar usuários: {str(e)}"
        )

@router.put("/admin/users/{user_id}/role")
async def admin_update_user_role_endpoint(
    user_id: str,
    role_data: UserRoleUpdate,
    current_user: Dict[str, Any] = Depends(require_admin_role)
):
    """
    Atualiza role do usuário (apenas administradores)
    """
    try:
        result = admin_update_user_role(user_id, role_data.role)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return {
            "message": "Role do usuário atualizada com sucesso",
            "profile": result["profile"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar role: {str(e)}"
        )

@router.delete("/admin/users/{user_id}")
async def admin_delete_user_endpoint(
    user_id: str,
    current_user: Dict[str, Any] = Depends(require_admin_role)
):
    """
    Remove usuário (apenas administradores)
    """
    try:
        result = admin_delete_user(user_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return {"message": result["message"]}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao remover usuário: {str(e)}"
        )
