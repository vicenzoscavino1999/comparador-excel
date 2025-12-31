"""
Database module - PostgreSQL/SQLite hybrid storage
Uses PostgreSQL if DATABASE_URL is set, otherwise falls back to SQLite
"""
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

# Check if PostgreSQL URL is provided
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Use PostgreSQL
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    def get_db():
        """Get PostgreSQL connection"""
        # Render uses postgres:// but psycopg2 needs postgresql://
        url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        conn = psycopg2.connect(url, cursor_factory=RealDictCursor)
        return conn
    
    def init_db():
        """Initialize PostgreSQL tables"""
        conn = get_db()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create comparison_logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comparison_logs (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) NOT NULL,
                file1_name VARCHAR(255),
                file1_size INTEGER,
                file2_name VARCHAR(255),
                file2_size INTEGER,
                records_compared INTEGER,
                differences_found INTEGER,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ PostgreSQL database initialized")

else:
    # Fallback to SQLite
    import sqlite3
    
    DB_FILE = os.path.join(os.path.dirname(__file__), "database.db")
    
    @contextmanager
    def get_db():
        """Get SQLite connection"""
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def init_db():
        """Initialize SQLite tables"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_admin INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS comparison_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    file1_name TEXT,
                    file1_size INTEGER,
                    file2_name TEXT,
                    file2_size INTEGER,
                    records_compared INTEGER,
                    differences_found INTEGER,
                    created_at TEXT NOT NULL
                )
            ''')
            
            conn.commit()
        print("✅ SQLite database initialized")


# ============== Common Functions ==============

def get_user(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username"""
    if DATABASE_URL:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return dict(row) if row else None
    else:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            return dict(row) if row else None


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email"""
    if DATABASE_URL:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return dict(row) if row else None
    else:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            row = cursor.fetchone()
            return dict(row) if row else None


def create_user(username: str, email: str, password_hash: str, is_admin: bool = False) -> bool:
    """Create a new user"""
    try:
        if DATABASE_URL:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO users (username, email, password_hash, is_admin, created_at)
                   VALUES (%s, %s, %s, %s, %s)''',
                (username, email, password_hash, is_admin, datetime.utcnow())
            )
            conn.commit()
            cursor.close()
            conn.close()
        else:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''INSERT INTO users (username, email, password_hash, is_admin, created_at)
                       VALUES (?, ?, ?, ?, ?)''',
                    (username, email, password_hash, 1 if is_admin else 0, datetime.utcnow().isoformat())
                )
                conn.commit()
        return True
    except Exception as e:
        print(f"Error creating user: {e}")
        return False


def get_all_users() -> List[Dict[str, Any]]:
    """Get all users"""
    if DATABASE_URL:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email, is_admin, created_at FROM users')
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(row) for row in rows]
    else:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, email, is_admin, created_at FROM users')
            return [dict(row) for row in cursor.fetchall()]


def log_comparison(username: str, file1_name: str, file1_size: int,
                   file2_name: str, file2_size: int,
                   records_compared: int, differences_found: int):
    """Log a comparison operation"""
    try:
        if DATABASE_URL:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO comparison_logs 
                   (username, file1_name, file1_size, file2_name, file2_size, 
                    records_compared, differences_found, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                (username, file1_name, file1_size, file2_name, file2_size,
                 records_compared, differences_found, datetime.utcnow())
            )
            conn.commit()
            cursor.close()
            conn.close()
        else:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''INSERT INTO comparison_logs 
                       (username, file1_name, file1_size, file2_name, file2_size, 
                        records_compared, differences_found, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                    (username, file1_name, file1_size, file2_name, file2_size,
                     records_compared, differences_found, datetime.utcnow().isoformat())
                )
                conn.commit()
    except Exception as e:
        print(f"Error logging comparison: {e}")


def ensure_default_admin():
    """Create default admin from environment variables if no users exist"""
    from passlib.context import CryptContext
    
    # Check if any users exist
    if DATABASE_URL:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM users')
        count = cursor.fetchone()['count']
        cursor.close()
        conn.close()
    else:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users')
            count = cursor.fetchone()[0]
    
    if count == 0:
        admin_user = os.getenv("ADMIN_USER", "admin")
        admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        admin_password = os.getenv("ADMIN_PASSWORD")
        
        if admin_password:
            pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
            password_hash = pwd_context.hash(admin_password)
            
            if create_user(admin_user, admin_email, password_hash, is_admin=True):
                print(f"✅ Default admin '{admin_user}' created")
            else:
                print("⚠️ Could not create admin")
        else:
            print("ℹ️ Set ADMIN_PASSWORD env var to auto-create admin")


# Initialize on import
init_db()
ensure_default_admin()
