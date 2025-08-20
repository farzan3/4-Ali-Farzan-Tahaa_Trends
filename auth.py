import streamlit as st
import hashlib
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import sqlite3
from pathlib import Path
from config import config

class AuthManager:
    def __init__(self):
        self.db_path = Path(config.BASE_DIR) / "users.db"
        self._init_db()
    
    def _init_db(self):
        """Initialize user database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                subscription_plan TEXT DEFAULT 'free',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # Create default admin user if not exists
        cursor.execute('SELECT COUNT(*) FROM users WHERE email = ?', ('admin@hunter.app',))
        if cursor.fetchone()[0] == 0:
            admin_password = self._hash_password('admin123')
            cursor.execute('''
                INSERT INTO users (email, hashed_password, role, subscription_plan)
                VALUES (?, ?, ?, ?)
            ''', ('admin@hunter.app', admin_password, 'admin', 'premium'))
        
        conn.commit()
        conn.close()
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user credentials"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            hashed_password = self._hash_password(password)
            
            cursor.execute('''
                SELECT id, email, role, subscription_plan, is_active
                FROM users 
                WHERE email = ? AND hashed_password = ? AND is_active = TRUE
            ''', (email, hashed_password))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return {
                    'id': user[0],
                    'email': user[1],
                    'role': user[2],
                    'subscription_plan': user[3],
                    'is_active': bool(user[4])
                }
            
            return None
            
        except Exception as e:
            st.error(f"Authentication error: {e}")
            return None
    
    def create_user(self, email: str, password: str, role: str = 'user') -> bool:
        """Create new user account"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            hashed_password = self._hash_password(password)
            
            cursor.execute('''
                INSERT INTO users (email, hashed_password, role)
                VALUES (?, ?, ?)
            ''', (email, hashed_password, role))
            
            conn.commit()
            conn.close()
            
            return True
            
        except sqlite3.IntegrityError:
            st.error("User with this email already exists")
            return False
        except Exception as e:
            st.error(f"Error creating user: {e}")
            return False
    
    def generate_token(self, user: Dict[str, Any]) -> str:
        """Generate JWT token for user"""
        payload = {
            'user_id': user['id'],
            'email': user['email'],
            'role': user['role'],
            'exp': datetime.utcnow() + timedelta(hours=config.JWT_EXPIRATION_HOURS)
        }
        
        return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def login_form(self) -> Optional[Dict[str, Any]]:
        """Display login form and handle authentication"""
        st.subheader("🔐 Login to Hunter Platform")
        
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="your.email@example.com")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login")
            
            if login_button:
                if email and password:
                    user = self.authenticate_user(email, password)
                    if user:
                        # Store user session
                        st.session_state.user = user
                        st.session_state.authenticated = True
                        st.success(f"Welcome back, {user['email']}!")
                        # Don't use rerun here to avoid infinite loops
                        return user
                    else:
                        st.error("Invalid credentials")
                else:
                    st.error("Please enter both email and password")
        
        # Registration section
        with st.expander("New user? Register here"):
            with st.form("register_form"):
                reg_email = st.text_input("Email", key="reg_email")
                reg_password = st.text_input("Password", type="password", key="reg_password")
                confirm_password = st.text_input("Confirm Password", type="password")
                register_button = st.form_submit_button("Register")
                
                if register_button:
                    if reg_email and reg_password and confirm_password:
                        if reg_password != confirm_password:
                            st.error("Passwords don't match")
                        elif len(reg_password) < 6:
                            st.error("Password must be at least 6 characters")
                        else:
                            if self.create_user(reg_email, reg_password):
                                st.success("Account created! Please login.")
                    else:
                        st.error("Please fill in all fields")
        
        return None
    
    def logout(self):
        """Logout current user"""
        if 'user' in st.session_state:
            del st.session_state.user
        if 'authenticated' in st.session_state:
            del st.session_state.authenticated
        # Don't use rerun here to avoid infinite loops
    
    def require_auth(self) -> Optional[Dict[str, Any]]:
        """Require authentication for protected pages"""
        if 'authenticated' not in st.session_state or not st.session_state.authenticated:
            return self.login_form()
        
        return st.session_state.get('user')
    
    def check_role(self, required_role: str) -> bool:
        """Check if current user has required role"""
        if 'user' not in st.session_state:
            return False
        
        user_role = st.session_state.user.get('role', 'user')
        
        role_hierarchy = {'admin': 3, 'premium': 2, 'user': 1}
        
        return role_hierarchy.get(user_role, 0) >= role_hierarchy.get(required_role, 0)

# Global auth manager instance
auth_manager = AuthManager()