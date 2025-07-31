from datetime import datetime, timedelta
from typing import Optional, List
# Adicione esta linha no início do arquivo, junto com os outros imports
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
import json
import os
from pathlib import Path
from email_service import generate_auth_token, send_password_reset_email, send_temp_password_email, generate_temp_password, send_auth_email
from auth_token_manager import create_auth_token, verify_auth_token, mark_token_as_used, clean_expired_tokens
from external_id_manager import get_next_external_id, mark_external_id_as_deleted, reorganize_external_ids
from typing import Optional
from fastapi import Request

# Adicione esta linha para definir o router
router = APIRouter(prefix="/auth", tags=["authentication"])

# Security configuration
SECRET_KEY = os.getenv(
    "SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 180
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "webhook-secret-key")

# Database file paths
USERS_DB_FILE = Path(__file__).parent.parent / "data" / "users_db.json"
APPROVED_USERS_FILE = Path(__file__).parent.parent / \
    "data" / "approved_users.json"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


class Token(BaseModel):
    access_token: str
    token_type: str
    is_temporary_password: bool = False


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


class User(BaseModel):
    id: str
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: str
    disabled: Optional[bool] = False
    created_at: datetime
    updated_at: datetime
    external_id: Optional[str] = None  # ID from external platform
    approved: bool = True
    last_login: Optional[datetime] = None
    is_temporary_password: bool = False  # Adicionar este campo


class UserCreate(BaseModel):
    username: str
    # Alterado de Optional[EmailStr] para EmailStr (obrigatório)
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "student"
    external_id: Optional[str] = None
    approved: bool = True
    # Novo campo para indicar se deve gerar senha aleatória
    generate_password: bool = True


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    disabled: Optional[bool] = None
    approved: Optional[bool] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class PasswordReset(BaseModel):
    username: str
    new_password: str


class WebhookUser(BaseModel):
    external_id: str
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: str = "student"
    action: str  # "create", "update", "delete", "approve", "disable"


# Initialize database files
def initialize_database():
    """Initialize the user database files if they don't exist"""
    if not USERS_DB_FILE.exists():
        default_users = {
            "admin": {
                "id": "admin",
                "username": "admin",
                "email": "admin@dnadaforca.com",
                "full_name": "Administrator",
                "role": "admin",
                "hashed_password": pwd_context.hash("adminpass"),
                "disabled": False,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "external_id": None,
                "approved": True,
                "last_login": None
            },
            "instrutor": {
                "id": "instrutor",
                "username": "instrutor",
                "email": "instrutor@dnadaforca.com",
                "full_name": "Instrutor Padrão",
                "role": "instructor",
                "hashed_password": pwd_context.hash("instrutorpass"),
                "disabled": False,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "external_id": None,
                "approved": True,
                "last_login": None
            }
        }
        save_users_db(default_users)

    if not APPROVED_USERS_FILE.exists():
        # Initialize with some approved users list
        approved_users = [
            {
                "external_id": "ext_001",
                "username": "aluno1",
                "email": "aluno1@example.com",
                "full_name": "Aluno Um",
                "role": "student"
            },
            {
                "external_id": "ext_002",
                "username": "aluno2",
                "email": "aluno2@example.com",
                "full_name": "Aluno Dois",
                "role": "student"
            }
        ]
        with open(APPROVED_USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(approved_users, f, indent=2, ensure_ascii=False)

# Database operations


def load_users_db() -> dict:
    """Load users from database file"""
    try:
        with open(USERS_DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_users_db(users_db: dict):
    """Save users to database file"""
    with open(USERS_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(users_db, f, indent=2, ensure_ascii=False)


def load_approved_users() -> List[dict]:
    """Load approved users list"""
    try:
        with open(APPROVED_USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_approved_users(approved_users: List[dict]):
    """Save approved users list"""
    with open(APPROVED_USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(approved_users, f, indent=2, ensure_ascii=False)


# Initialize database on import
initialize_database()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(username: str) -> Optional[User]:
    """Get user by username"""
    users_db = load_users_db()
    if username in users_db:
        user_dict = users_db[username]
        # Convert datetime strings back to datetime objects
        if isinstance(user_dict.get('created_at'), str):
            user_dict['created_at'] = datetime.fromisoformat(
                user_dict['created_at'])
        if isinstance(user_dict.get('updated_at'), str):
            user_dict['updated_at'] = datetime.fromisoformat(
                user_dict['updated_at'])
        if user_dict.get('last_login') and isinstance(user_dict['last_login'], str):
            user_dict['last_login'] = datetime.fromisoformat(
                user_dict['last_login'])
        return User(**user_dict)
    return None


def get_user_by_id(user_id: str) -> Optional[User]:
    """Get user by ID"""
    users_db = load_users_db()
    for user_data in users_db.values():
        if user_data.get('id') == user_id:
            if isinstance(user_data.get('created_at'), str):
                user_data['created_at'] = datetime.fromisoformat(
                    user_data['created_at'])
            if isinstance(user_data.get('updated_at'), str):
                user_data['updated_at'] = datetime.fromisoformat(
                    user_data['updated_at'])
            if user_data.get('last_login') and isinstance(user_data['last_login'], str):
                user_data['last_login'] = datetime.fromisoformat(
                    user_data['last_login'])
            return User(**user_data)
    return None


def get_user_by_external_id(external_id: str) -> Optional[User]:
    """Get user by external platform ID"""
    users_db = load_users_db()
    for user_data in users_db.values():
        if user_data.get('external_id') == external_id:
            if isinstance(user_data.get('created_at'), str):
                user_data['created_at'] = datetime.fromisoformat(
                    user_data['created_at'])
            if isinstance(user_data.get('updated_at'), str):
                user_data['updated_at'] = datetime.fromisoformat(
                    user_data['updated_at'])
            if user_data.get('last_login') and isinstance(user_data['last_login'], str):
                user_data['last_login'] = datetime.fromisoformat(
                    user_data['last_login'])
            return User(**user_data)
    return None

# Modifique a função create_user para usar o ID externo automático


def create_user(user_data: UserCreate, password: str = None, send_email: bool = True) -> tuple[User, str]:
    """Create a new user and return the user and generated password"""
    users_db = load_users_db()

    # Check if username already exists
    if user_data.username in users_db:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Import here to avoid circular imports
    from email_service import generate_temp_password, send_temp_password_email, generate_auth_token, send_auth_email
    from auth_token_manager import create_auth_token

    # Generate a temporary password if not provided and generate_password is True
    generated_password = None
    if password is None and user_data.generate_password:
        generated_password = generate_temp_password()
        password = generated_password
    elif password is None:
        password = "changeme"  # Default password if not generating random one
    else:
        generated_password = password  # Store the provided password

    # Gerar ID externo automático se não for fornecido
    if not user_data.external_id:
        user_data.external_id = get_next_external_id()

    now = datetime.utcnow()
    # Na função create_user
    user_dict = {
        "id": user_data.username,  # Use username as ID for simplicity
        "username": user_data.username,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "role": user_data.role,
        "hashed_password": pwd_context.hash(password),
        "disabled": False,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "external_id": user_data.external_id,
        "approved": False,  # Inicialmente não aprovado até confirmação por e-mail
        "last_login": None,
        # Marcar como senha temporária
        "is_temporary_password": user_data.generate_password or password == "changeme"
    }

    users_db[user_data.username] = user_dict
    save_users_db(users_db)

    # Enviar e-mail de autenticação e senha temporária
    if send_email:
        # Gerar token de autenticação
        auth_token = generate_auth_token()
        create_auth_token(user_data.username, auth_token, user_data.email)

        # Enviar e-mail de autenticação
        send_auth_email(user_data.email, user_data.username, auth_token)

        # Enviar e-mail com senha temporária
        send_temp_password_email(user_data.email, user_data.username, password)

    # Convert back to datetime objects for return
    user_dict['created_at'] = now
    user_dict['updated_at'] = now
    return User(**user_dict), generated_password

# Modifique a função delete_user para marcar o ID externo como deletado


def delete_user(username: str) -> bool:
    """Delete a user"""
    users_db = load_users_db()

    if username in users_db:
        # Marcar o ID externo como deletado para reutilização
        external_id = users_db[username].get('external_id')
        if external_id:
            mark_external_id_as_deleted(external_id)

        del users_db[username]

        # Reorganizar os IDs externos
        users_db = reorganize_external_ids(users_db)

        save_users_db(users_db)
        return True
    return False


def update_user(username: str, user_update: UserUpdate) -> Optional[User]:
    """Update an existing user"""
    users_db = load_users_db()

    if username not in users_db:
        return None

    user_dict = users_db[username]

    # Update fields
    if user_update.email is not None:
        user_dict['email'] = user_update.email
    if user_update.full_name is not None:
        user_dict['full_name'] = user_update.full_name
    if user_update.role is not None:
        user_dict['role'] = user_update.role
    if user_update.disabled is not None:
        user_dict['disabled'] = user_update.disabled
    if user_update.approved is not None:
        user_dict['approved'] = user_update.approved

    user_dict['updated_at'] = datetime.utcnow().isoformat()

    users_db[username] = user_dict
    save_users_db(users_db)

    return get_user(username)


def delete_user(username: str) -> bool:
    """Delete a user"""
    users_db = load_users_db()

    if username in users_db:
        del users_db[username]
        save_users_db(users_db)
        return True
    return False


def update_last_login(username: str):
    """Update user's last login timestamp"""
    users_db = load_users_db()

    if username in users_db:
        users_db[username]['last_login'] = datetime.utcnow().isoformat()
        save_users_db(users_db)


def is_user_approved(username: str) -> bool:
    """Check if user is in approved users list"""
    user = get_user(username)
    if user:
        return user.approved and not user.disabled

    # Check approved users list
    approved_users = load_approved_users()
    return any(u.get('username') == username for u in approved_users)


def get_all_users() -> List[User]:
    """Get all users"""
    users_db = load_users_db()
    users = []
    for user_data in users_db.values():
        if isinstance(user_data.get('created_at'), str):
            user_data['created_at'] = datetime.fromisoformat(
                user_data['created_at'])
        if isinstance(user_data.get('updated_at'), str):
            user_data['updated_at'] = datetime.fromisoformat(
                user_data['updated_at'])
        if user_data.get('last_login') and isinstance(user_data['last_login'], str):
            user_data['last_login'] = datetime.fromisoformat(
                user_data['last_login'])
        users.append(User(**user_data))
    return users


def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate user with username and password"""
    user = get_user(username)
    if not user:
        return None

    # Check if user is approved and not disabled
    if not user.approved or user.disabled:
        return None

    users_db = load_users_db()
    if not verify_password(password, users_db[username]["hashed_password"]):
        return None

    # Update last login
    update_last_login(username)

    return user


def change_password(username: str, current_password: str, new_password: str) -> bool:
    """Change user password"""
    users_db = load_users_db()

    if username not in users_db:
        return False

    # Verify current password
    if not verify_password(current_password, users_db[username]["hashed_password"]):
        return False

    # Update password
    users_db[username]["hashed_password"] = pwd_context.hash(new_password)
    users_db[username]["updated_at"] = datetime.utcnow().isoformat()

    # Marcar como senha permanente
    was_temporary = users_db[username].get("is_temporary_password", False)
    users_db[username]["is_temporary_password"] = False

    # Aprovar automaticamente o usuário se estiver alterando a senha temporária
    if was_temporary:
        users_db[username]["approved"] = True
        print(
            f"✅ Usuário {username} aprovado automaticamente após alteração de senha temporária")

    save_users_db(users_db)

    return True


def reset_password(username: str, new_password: str, approve_user: bool = False) -> bool:
    """Reset user password (admin function)"""
    users_db = load_users_db()

    if username not in users_db:
        return False

    # Update password
    users_db[username]["hashed_password"] = pwd_context.hash(new_password)
    users_db[username]["updated_at"] = datetime.utcnow().isoformat()

    # Aprovar usuário se solicitado
    if approve_user:
        users_db[username]["approved"] = True

    save_users_db(users_db)

    return True


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
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
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


@router.post("/public/verify-token")
async def verify_auth_token(token_data: dict):
    """Verify authentication token and create user account"""
    from auth_token_manager import verify_auth_token, mark_token_as_used
    from email_service import generate_temp_password, send_temp_password_email

    token = token_data.get("token")
    username = token_data.get("username")

    if not token or not username:
        raise HTTPException(status_code=400, detail="Invalid token data")

    # Verificar token
    token_info = verify_auth_token(token)
    if not token_info or token_info.get("username") != username:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    # Marcar token como usado
    mark_token_as_used(token)

    # Verificar se o usuário já existe
    existing_user = get_user(username)
    if existing_user:
        # Atualizar status de aprovação
        user_update = UserUpdate(approved=True, disabled=False)
        update_user(username, user_update)
    else:
        # Buscar dados do usuário na lista de aprovados
        approved_users = load_approved_users()
        user_data = next(
            (u for u in approved_users if u.get('username') == username), None)

        if not user_data:
            raise HTTPException(
                status_code=404, detail="User not found in approved list")

        # Criar usuário com senha temporária
        temp_password = generate_temp_password()
        user_create = UserCreate(
            username=username,
            email=user_data.get('email'),
            full_name=user_data.get('full_name'),
            role=user_data.get('role', 'student'),
            external_id=user_data.get('external_id'),
            approved=True,
            generate_password=False  # Não gerar nova senha, usaremos a que criamos
        )

        # Criar usuário sem enviar email (enviaremos manualmente)
        create_user(user_create, temp_password, send_email=False)

        # Enviar email com senha temporária
        send_temp_password_email(user_data.get(
            'email'), username, temp_password)

    return {"message": "Account verified successfully. A temporary password has been sent to your email."}


class PasswordResetRequest(BaseModel):
    username: str


class PasswordResetConfirm(BaseModel):
    token: str
    username: str
    new_password: str


@router.post("/public/request-password-reset")
async def request_password_reset(request_data: PasswordResetRequest):
    """Request password reset (public route)"""
    from email_service import generate_auth_token
    from auth_token_manager import create_auth_token
    from email_service import send_password_reset_email

    username = request_data.username

    # Verificar se o usuário existe
    user = get_user(username)
    if not user:
        # Por segurança, não informamos se o usuário existe ou não
        return {"message": "Se o usuário existir, um email de redefinição de senha será enviado."}

    # Verificar se o usuário tem email
    if not user.email:
        # Por segurança, não informamos o motivo real
        return {"message": "Se o usuário existir, um email de redefinição de senha será enviado."}

    # Verificar se o usuário está aprovado
    if not user.approved or user.disabled:
        # Por segurança, não informamos o motivo real
        return {"message": "Se o usuário existir, um email de redefinição de senha será enviado."}

    # Gerar token de reset de senha
    reset_token = generate_auth_token()
    create_auth_token(username, reset_token, user.email)

    # Enviar email com link para reset de senha
    send_password_reset_email(user.email, username, reset_token)

    return {"message": "Se o usuário existir, um email de redefinição de senha será enviado."}


@router.post("/public/confirm-password-reset")
async def confirm_password_reset(reset_data: PasswordResetConfirm):
    """Confirm password reset with token (public route)"""
    from auth_token_manager import verify_auth_token, mark_token_as_used

    token = reset_data.token
    username = reset_data.username
    new_password = reset_data.new_password

    # Verificar token
    token_info = verify_auth_token(token)
    if not token_info or token_info.get("username") != username:
        raise HTTPException(
            status_code=400, detail="Token inválido ou expirado")

    # Verificar se o usuário existe
    user = get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Marcar token como usado
    mark_token_as_used(token)

    # Redefinir a senha
    success = reset_password(username, new_password)
    if not success:
        raise HTTPException(status_code=500, detail="Erro ao redefinir senha")

    # Atualizar o status da senha temporária para false e aprovar o usuário
    users_db = load_users_db()
    if username in users_db:
        users_db[username]["is_temporary_password"] = False
        # Aprovar automaticamente o usuário
        users_db[username]["approved"] = True
        save_users_db(users_db)

    return {"message": "Senha redefinida com sucesso"}

# Adicionar após a definição do oauth2_scheme existente


class OAuth2PasswordBearerOptional(OAuth2PasswordBearer):
    async def __call__(self, request: Request) -> Optional[str]:
        try:
            return await super().__call__(request)
        except HTTPException:
            return None


oauth2_scheme_optional = OAuth2PasswordBearerOptional(tokenUrl="/auth/token")

# Adicionar após a função get_current_user (linha 490)


async def get_optional_current_user(token: str = Depends(oauth2_scheme_optional)):
    """Similar ao get_current_user, mas não falha se o token não for fornecido"""
    if token is None:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        token_data = TokenData(username=username)
    except JWTError:
        return None

    user = get_user(username=token_data.username)
    return user
