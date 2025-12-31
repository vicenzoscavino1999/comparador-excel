from datetime import datetime, timedelta
from typing import Optional
import json
import os
from passlib.context import CryptContext
from jose import JWTError, jwt

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "tu-clave-secreta-cambiar-en-produccion-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Password hashing - using sha256 for better compatibility
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

# Users file path
USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")


def load_users() -> dict:
    """Load users from JSON file"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_users(users: dict):
    """Save users to JSON file"""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


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


def register_user(username: str, email: str, password: str) -> dict:
    """Register a new user"""
    users = load_users()
    
    # Check if username exists
    if username in users:
        return {"success": False, "error": "El usuario ya existe"}
    
    # Check if email exists
    for user_data in users.values():
        if user_data.get("email") == email:
            return {"success": False, "error": "El email ya está registrado"}
    
    # Create user
    users[username] = {
        "email": email,
        "password": get_password_hash(password),
        "created_at": datetime.utcnow().isoformat()
    }
    save_users(users)
    
    return {"success": True}


def authenticate_user(username: str, password: str) -> Optional[str]:
    """Authenticate a user and return a token"""
    users = load_users()
    
    if username not in users:
        return None
    
    user = users[username]
    if not verify_password(password, user["password"]):
        return None
    
    # Create token
    access_token = create_access_token(
        data={"sub": username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return access_token
