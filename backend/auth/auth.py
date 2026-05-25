from datetime import datetime, timedelta
from typing import Optional, List
from contextlib import contextmanager
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
import os
from pathlib import Path
from .email_service import generate_auth_token, send_password_reset_email, send_temp_password_email, generate_temp_password, send_auth_email
from .auth_token_manager import create_auth_token, verify_auth_token, mark_token_as_used, clean_expired_tokens
from .external_id_manager import get_next_external_id, mark_external_id_as_deleted
from fastapi import Request

router = APIRouter(tags=["authentication"])

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 180
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "webhook-secret-key")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


# ── Pydantic models (unchanged) ───────────────────────────────────────────────

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
    external_id: Optional[str] = None
    approved: bool = True
    last_login: Optional[datetime] = None
    is_temporary_password: bool = False
    instructor_username: Optional[str] = None


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "student"
    external_id: Optional[str] = None
    approved: bool = True
    generate_password: bool = True
    instructor_username: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    disabled: Optional[bool] = None
    approved: Optional[bool] = None
    instructor_username: Optional[str] = None


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


# ── Database session helper ───────────────────────────────────────────────────

def _get_db_session():
    """Import here to avoid circular imports at module load time."""
    from database.db import SessionLocal
    return SessionLocal()


@contextmanager
def _db():
    session = _get_db_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _row_to_user(row) -> User:
    """Convert a UserDB ORM row to the Pydantic User model."""
    return User(
        id=row.id,
        username=row.username,
        email=row.email,
        full_name=row.full_name,
        role=row.role,
        disabled=row.disabled or False,
        created_at=row.created_at,
        updated_at=row.updated_at,
        external_id=row.external_id,
        approved=row.approved,
        last_login=row.last_login,
        is_temporary_password=row.is_temporary_password,
        instructor_username=row.instructor_username,
    )


# ── Database initialisation ───────────────────────────────────────────────────

def initialize_database():
    """Create tables, seed approved-users list, and create default admin if needed."""
    from database.db import engine, Base
    from database.models import UserDB, ApprovedUserDB  # noqa: F401 — needed for metadata
    Base.metadata.create_all(bind=engine)

    # Seed approved_users table if empty
    with _db() as db:
        from database.models import ApprovedUserDB
        if db.query(ApprovedUserDB).count() == 0:
            seed = [
                ApprovedUserDB(external_id="ext_001", username="aluno1",
                               email="aluno1@example.com", full_name="Aluno Um", role="student"),
                ApprovedUserDB(external_id="ext_002", username="aluno2",
                               email="aluno2@example.com", full_name="Aluno Dois", role="student"),
            ]
            db.add_all(seed)

    # Create default admin user on first run if no users exist
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "")
    admin_email = os.getenv("ADMIN_EMAIL", "admin@iadnadaforca.com.br")

    if admin_password:
        from database.models import UserDB
        with _db() as db:
            if db.query(UserDB).count() == 0:
                now = datetime.utcnow()
                db.add(UserDB(
                    id=admin_username,
                    username=admin_username,
                    email=admin_email,
                    full_name="Administrador",
                    role="admin",
                    hashed_password=pwd_context.hash(admin_password),
                    disabled=False,
                    created_at=now,
                    updated_at=now,
                    external_id="ext_admin_001",
                    approved=True,
                    is_temporary_password=False,
                ))


initialize_database()


# ── Password helpers ──────────────────────────────────────────────────────────

def verify_password(plain_password, hashed_password):
    if len(plain_password.encode("utf-8")) > 72:
        plain_password = plain_password[:72]
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    if len(password.encode("utf-8")) > 72:
        password = password[:72]
    return pwd_context.hash(password)


# ── CRUD functions (SQLite/Postgres via SQLAlchemy) ───────────────────────────

def get_user(username: str) -> Optional[User]:
    from database.models import UserDB
    with _db() as db:
        row = db.query(UserDB).filter(UserDB.username == username).first()
        return _row_to_user(row) if row else None


def get_user_by_id(user_id: str) -> Optional[User]:
    from database.models import UserDB
    with _db() as db:
        row = db.query(UserDB).filter(UserDB.id == user_id).first()
        return _row_to_user(row) if row else None


def get_user_by_external_id(external_id: str) -> Optional[User]:
    from database.models import UserDB
    with _db() as db:
        row = db.query(UserDB).filter(UserDB.external_id == external_id).first()
        return _row_to_user(row) if row else None


def get_all_users() -> List[User]:
    from database.models import UserDB
    with _db() as db:
        rows = db.query(UserDB).all()
        return [_row_to_user(r) for r in rows]


def _get_hashed_password(username: str) -> Optional[str]:
    from database.models import UserDB
    with _db() as db:
        row = db.query(UserDB).filter(UserDB.username == username).first()
        return row.hashed_password if row else None


def create_user(user_data: UserCreate, password: str = None, send_email: bool = True) -> tuple:
    """Create a new user and return (User, generated_password)."""
    from database.models import UserDB
    from .email_service import generate_temp_password, send_temp_password_email, generate_auth_token, send_auth_email
    from .auth_token_manager import create_auth_token

    with _db() as db:
        if db.query(UserDB).filter(UserDB.username == user_data.username).first():
            raise HTTPException(status_code=400, detail="Username already exists")

    generated_password = None
    if password is None and user_data.generate_password:
        generated_password = generate_temp_password()
        password = generated_password
    elif password is None:
        password = "changeme"
    else:
        generated_password = password

    if not user_data.external_id:
        user_data.external_id = get_next_external_id()

    now = datetime.utcnow()
    row = None
    from database.models import UserDB
    with _db() as db:
        row = UserDB(
            id=user_data.username,
            username=user_data.username,
            email=str(user_data.email) if user_data.email else None,
            full_name=user_data.full_name,
            role=user_data.role,
            hashed_password=pwd_context.hash(password),
            disabled=False,
            created_at=now,
            updated_at=now,
            external_id=user_data.external_id,
            approved=False,
            last_login=None,
            is_temporary_password=user_data.generate_password or password == "changeme",
            instructor_username=user_data.instructor_username,
        )
        db.add(row)

    if send_email and user_data.email:
        auth_token = generate_auth_token()
        create_auth_token(user_data.username, auth_token, str(user_data.email))
        send_auth_email(str(user_data.email), user_data.username, auth_token)
        send_temp_password_email(str(user_data.email), user_data.username, password)

    user = get_user(user_data.username)
    return user, generated_password


def update_user(username: str, user_update: UserUpdate) -> Optional[User]:
    from database.models import UserDB
    with _db() as db:
        row = db.query(UserDB).filter(UserDB.username == username).first()
        if not row:
            return None
        if user_update.email is not None:
            row.email = str(user_update.email)
        if user_update.full_name is not None:
            row.full_name = user_update.full_name
        if user_update.role is not None:
            row.role = user_update.role
        if user_update.disabled is not None:
            row.disabled = user_update.disabled
        if user_update.approved is not None:
            row.approved = user_update.approved
        if user_update.instructor_username is not None:
            row.instructor_username = user_update.instructor_username or None
        row.updated_at = datetime.utcnow()
    return get_user(username)


def delete_user(username: str) -> bool:
    from database.models import UserDB
    with _db() as db:
        row = db.query(UserDB).filter(UserDB.username == username).first()
        if not row:
            return False
        if row.external_id:
            mark_external_id_as_deleted(row.external_id)
        db.delete(row)
    return True


def update_last_login(username: str):
    from database.models import UserDB
    with _db() as db:
        row = db.query(UserDB).filter(UserDB.username == username).first()
        if row:
            row.last_login = datetime.utcnow()


def is_user_approved(username: str) -> bool:
    user = get_user(username)
    if user:
        return user.approved and not user.disabled
    return any(u.username == username for u in _load_approved_users_rows())


def authenticate_user(username: str, password: str) -> Optional[User]:
    user = get_user(username)
    if not user or not user.approved or user.disabled:
        return None
    hashed = _get_hashed_password(username)
    if not hashed or not verify_password(password, hashed):
        return None
    update_last_login(username)
    return user


def change_password(username: str, current_password: str, new_password: str) -> bool:
    from database.models import UserDB
    hashed = _get_hashed_password(username)
    if not hashed or not verify_password(current_password, hashed):
        return False
    with _db() as db:
        row = db.query(UserDB).filter(UserDB.username == username).first()
        if not row:
            return False
        was_temporary = row.is_temporary_password
        row.hashed_password = pwd_context.hash(new_password)
        row.is_temporary_password = False
        row.updated_at = datetime.utcnow()
        if was_temporary:
            row.approved = True
    return True


def reset_password(username: str, new_password: str, approve_user: bool = False) -> bool:
    from database.models import UserDB
    with _db() as db:
        row = db.query(UserDB).filter(UserDB.username == username).first()
        if not row:
            return False
        row.hashed_password = pwd_context.hash(new_password)
        row.updated_at = datetime.utcnow()
        if approve_user:
            row.approved = True
    return True


# ── Approved users ────────────────────────────────────────────────────────────

def _load_approved_users_rows():
    from database.models import ApprovedUserDB
    with _db() as db:
        return db.query(ApprovedUserDB).all()


def load_approved_users() -> List[dict]:
    return [
        {"external_id": r.external_id, "username": r.username,
         "email": r.email, "full_name": r.full_name, "role": r.role}
        for r in _load_approved_users_rows()
    ]


def save_approved_users(approved_users: List[dict]):
    from database.models import ApprovedUserDB
    with _db() as db:
        db.query(ApprovedUserDB).delete()
        for u in approved_users:
            db.add(ApprovedUserDB(
                external_id=u.get("external_id", u.get("username")),
                username=u["username"],
                email=u.get("email"),
                full_name=u.get("full_name"),
                role=u.get("role", "student"),
            ))


# ── JWT helpers ───────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


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


class OAuth2PasswordBearerOptional(OAuth2PasswordBearer):
    async def __call__(self, request: Request) -> Optional[str]:
        try:
            return await super().__call__(request)
        except HTTPException:
            return None


oauth2_scheme_optional = OAuth2PasswordBearerOptional(tokenUrl="/auth/token")


async def get_optional_current_user(token: str = Depends(oauth2_scheme_optional)):
    if token is None:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    return get_user(username=username)


# ── Router endpoints (unchanged logic, updated DB calls) ──────────────────────

class PasswordResetRequest(BaseModel):
    username: str


class PasswordResetConfirm(BaseModel):
    token: str
    username: str
    new_password: str


@router.post("/public/verify-token")
async def verify_auth_token_endpoint(token_data: dict):
    """Verify authentication token and create user account."""
    from .auth_token_manager import verify_auth_token as _verify, mark_token_as_used as _mark_used
    from .email_service import generate_temp_password, send_temp_password_email

    token = token_data.get("token")
    username = token_data.get("username")

    if not token or not username:
        raise HTTPException(status_code=400, detail="Invalid token data")

    token_info = _verify(token)
    if not token_info or token_info.get("username") != username:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    _mark_used(token)

    existing_user = get_user(username)
    if existing_user:
        update_user(username, UserUpdate(approved=True, disabled=False))
    else:
        approved = load_approved_users()
        user_data = next((u for u in approved if u.get("username") == username), None)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found in approved list")

        temp_password = generate_temp_password()
        user_create = UserCreate(
            username=username,
            email=user_data.get("email"),
            full_name=user_data.get("full_name"),
            role=user_data.get("role", "student"),
            external_id=user_data.get("external_id"),
            approved=True,
            generate_password=False,
        )
        create_user(user_create, temp_password, send_email=False)
        send_temp_password_email(user_data.get("email"), username, temp_password)

    return {"message": "Account verified successfully. A temporary password has been sent to your email."}


@router.post("/public/request-password-reset")
async def request_password_reset(request_data: PasswordResetRequest):
    from .email_service import generate_auth_token as _gen_token, send_password_reset_email
    from .auth_token_manager import create_auth_token as _create_token

    user = get_user(request_data.username)
    _generic = {"message": "Se o usuário existir, um email de redefinição de senha será enviado."}
    if not user or not user.email or not user.approved or user.disabled:
        return _generic

    reset_token = _gen_token()
    _create_token(request_data.username, reset_token, user.email)
    send_password_reset_email(user.email, request_data.username, reset_token)
    return _generic


@router.post("/public/confirm-password-reset")
async def confirm_password_reset(reset_data: PasswordResetConfirm):
    from .auth_token_manager import verify_auth_token as _verify, mark_token_as_used as _mark_used
    from database.models import UserDB

    token_info = _verify(reset_data.token)
    if not token_info or token_info.get("username") != reset_data.username:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado")

    user = get_user(reset_data.username)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    _mark_used(reset_data.token)

    with _db() as db:
        row = db.query(UserDB).filter(UserDB.username == reset_data.username).first()
        if row:
            row.hashed_password = pwd_context.hash(reset_data.new_password)
            row.is_temporary_password = False
            row.approved = True
            row.updated_at = datetime.utcnow()

    return {"message": "Senha redefinida com sucesso"}
