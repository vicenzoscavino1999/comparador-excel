"""
Authentication module with PostgreSQL/SQLite backend
- Closed registration (admin only can create users)
- JWT tokens with secure handling
"""
from datetime import datetime, timedelta
from typing import Optional
import os
import secrets
from passlib.context import CryptContext
from jose import JWTError, jwt

from database import get_user, get_user_by_email, create_user

# Configuration - SECRET_KEY must be set in production
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    # Check if we're in production (Render sets RENDER env var)
    if os.getenv("RENDER"):
        raise RuntimeError("SECRET_KEY environment variable must be set in production!")
    else:
        # Development mode - generate a random key (will change on restart)
        SECRET_KEY = secrets.token_hex(32)
        print("⚠️  WARNING: Using auto-generated SECRET_KEY. Set SECRET_KEY env var for production.")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Password hashing - using sha256 for better compatibility
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """Verify a JWT token and return the username"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None


def is_admin(username: str) -> bool:
    """Check if user is an admin"""
    user = get_user(username)
    return user is not None and user.get("is_admin", 0) == 1


def register_user(username: str, email: str, password: str, by_admin: str = None) -> dict:
    """
    Register a new user
    - If by_admin is provided, checks that they are admin
    - Otherwise registration is closed
    """
    # Check if registration is allowed
    if by_admin:
        if not is_admin(by_admin):
            return {"success": False, "error": "Solo administradores pueden crear usuarios"}
    else:
        # Public registration is disabled - for security
        # To enable, remove this block
        return {"success": False, "error": "El registro público está deshabilitado. Contacte al administrador."}
    
    # Check if username exists
    if get_user(username):
        return {"success": False, "error": "El usuario ya existe"}
    
    # Check if email exists
    if get_user_by_email(email):
        return {"success": False, "error": "El email ya está registrado"}
    
    # Create user
    password_hash = get_password_hash(password)
    if create_user(username, email, password_hash, is_admin=False):
        return {"success": True}
    else:
        return {"success": False, "error": "Error al crear usuario"}


def register_admin(username: str, email: str, password: str) -> dict:
    """Register an admin user (for initial setup only)"""
    if get_user(username):
        return {"success": False, "error": "El usuario ya existe"}
    
    if get_user_by_email(email):
        return {"success": False, "error": "El email ya está registrado"}
    
    password_hash = get_password_hash(password)
    if create_user(username, email, password_hash, is_admin=True):
        return {"success": True}
    else:
        return {"success": False, "error": "Error al crear admin"}


def authenticate_user(username: str, password: str) -> Optional[str]:
    """Authenticate a user and return a token"""
    user = get_user(username)
    
    if not user:
        return None
    
    if not verify_password(password, user["password_hash"]):
        return None
    
    # Create token with admin flag
    access_token = create_access_token(
        data={"sub": username, "is_admin": user.get("is_admin", 0) == 1},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return access_token
