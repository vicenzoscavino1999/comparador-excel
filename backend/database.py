"""
Database module - SQLite storage for users
Replaces the JSON-based storage for enterprise-level security
"""
import sqlite3
import os
from datetime import datetime
from typing import Optional, Dict, Any
from contextlib import contextmanager

# Database file path
DB_FILE = os.path.join(os.path.dirname(__file__), "database.db")


@contextmanager
def get_db():
    """Get database connection with context manager"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize the database with required tables"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Create users table
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
        
        # Create comparison_logs table for tracking usage
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


def get_user(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM users WHERE username = ?',
            (username,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM users WHERE email = ?',
            (email,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


def create_user(username: str, email: str, password_hash: str, is_admin: bool = False) -> bool:
    """Create a new user"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO users (username, email, password_hash, is_admin, created_at)
                   VALUES (?, ?, ?, ?, ?)''',
                (username, email, password_hash, 1 if is_admin else 0, datetime.utcnow().isoformat())
            )
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False


def get_all_users() -> list:
    """Get all users (admin only function)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email, is_admin, created_at FROM users')
        return [dict(row) for row in cursor.fetchall()]


def log_comparison(username: str, file1_name: str, file1_size: int, 
                   file2_name: str, file2_size: int, 
                   records_compared: int, differences_found: int):
    """Log a comparison operation"""
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


def migrate_from_json(json_file: str):
    """Migrate users from JSON file to SQLite (one-time migration)"""
    import json
    from passlib.context import CryptContext
    
    if not os.path.exists(json_file):
        return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        users = json.load(f)
    
    for username, data in users.items():
        # Check if user already exists
        if not get_user(username):
            with get_db() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        '''INSERT INTO users (username, email, password_hash, is_admin, created_at)
                           VALUES (?, ?, ?, ?, ?)''',
                        (username, data.get('email', ''), data.get('password', ''),
                         1 if username == 'admin' else 0, 
                         data.get('created_at', datetime.utcnow().isoformat()))
                    )
                    conn.commit()
                except sqlite3.IntegrityError:
                    pass


# Initialize database on import
init_db()
