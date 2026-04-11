"""
Authentication module for CV Intelligence System
Provides user authentication and session management
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from flask_login import UserMixin
import bcrypt


class User(UserMixin):
    """User model for authentication"""
    
    def __init__(self, user_id: str, username: str, email: str, role: str = 'user'):
        self.id = user_id
        self.username = username
        self.email = email
        self.role = role
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role
        }
    
    @property
    def is_admin(self) -> bool:
        return self.role == 'admin'


class UserManager:
    """Manages user authentication with file-based storage"""
    
    def __init__(self, users_file: str = 'users.json'):
        self.users_file = Path(users_file)
        self._ensure_users_file()
    
    def _ensure_users_file(self):
        """Create users file with default admin if it doesn't exist"""
        if not self.users_file.exists():
            # Create default admin user
            default_password = os.getenv('ADMIN_PASSWORD', 'admin123')
            admin_user = {
                'id': '1',
                'username': 'admin',
                'email': 'admin@example.com',
                'password_hash': self._hash_password(default_password),
                'role': 'admin'
            }
            self._save_users({'1': admin_user})
            print(f"Created default admin user: admin / {default_password}")
            print("⚠️  IMPORTANT: Change the admin password immediately!")
    
    def _load_users(self) -> Dict[str, Dict[str, Any]]:
        """Load users from file"""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading users: {e}")
            return {}
    
    def _save_users(self, users: Dict[str, Dict[str, Any]]):
        """Save users to file"""
        with open(self.users_file, 'w') as f:
            json.dump(users, f, indent=2)
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user by username and password"""
        users = self._load_users()
        
        # Find user by username
        user_data = None
        for uid, data in users.items():
            if data.get('username') == username:
                user_data = data
                break
        
        if not user_data:
            return None
        
        # Verify password
        if not self._verify_password(password, user_data['password_hash']):
            return None
        
        # Return User object
        return User(
            user_id=user_data['id'],
            username=user_data['username'],
            email=user_data['email'],
            role=user_data.get('role', 'user')
        )
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        users = self._load_users()
        user_data = users.get(user_id)
        
        if not user_data:
            return None
        
        return User(
            user_id=user_data['id'],
            username=user_data['username'],
            email=user_data['email'],
            role=user_data.get('role', 'user')
        )
    
    def create_user(self, username: str, email: str, password: str, role: str = 'user') -> Optional[User]:
        """Create a new user"""
        users = self._load_users()
        
        # Check if username already exists
        for data in users.values():
            if data.get('username') == username:
                return None
        
        # Generate new user ID
        user_id = str(len(users) + 1)
        
        # Create user data
        user_data = {
            'id': user_id,
            'username': username,
            'email': email,
            'password_hash': self._hash_password(password),
            'role': role
        }
        
        # Save user
        users[user_id] = user_data
        self._save_users(users)
        
        return User(
            user_id=user_id,
            username=username,
            email=email,
            role=role
        )
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        users = self._load_users()
        user_data = users.get(user_id)
        
        if not user_data:
            return False
        
        # Verify old password
        if not self._verify_password(old_password, user_data['password_hash']):
            return False
        
        # Update password
        user_data['password_hash'] = self._hash_password(new_password)
        users[user_id] = user_data
        self._save_users(users)
        
        return True
    
    def list_users(self) -> list:
        """List all users (without password hashes)"""
        users = self._load_users()
        return [
            {
                'id': data['id'],
                'username': data['username'],
                'email': data['email'],
                'role': data.get('role', 'user')
            }
            for data in users.values()
        ]
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        users = self._load_users()
        
        if user_id not in users:
            return False
        
        # Don't allow deleting the last admin
        if users[user_id].get('role') == 'admin':
            admin_count = sum(1 for u in users.values() if u.get('role') == 'admin')
            if admin_count <= 1:
                return False
        
        del users[user_id]
        self._save_users(users)
        return True
