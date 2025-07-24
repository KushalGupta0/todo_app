"""
User management module.

This module handles user authentication, registration, and user data management.
"""

from typing import Optional, List
import bcrypt
from datetime import datetime


class User:
    """Represents a user in the system."""
    
    def __init__(
        self,
        username: str,
        email: str = "",
        user_id: Optional[int] = None,
        password_hash: Optional[bytes] = None
    ) -> None:
        """
        Initialize a user.
        
        Args:
            username: User's username
            email: User's email address
            user_id: Unique user identifier
            password_hash: Hashed password (for loading from database)
        """
        self.user_id: Optional[int] = user_id
        self.username: str = username
        self.email: str = email
        self.password_hash: Optional[bytes] = password_hash
        self.created_at: datetime = datetime.now()
        self.last_login: Optional[datetime] = None
        self.is_active: bool = True
    
    def set_password(self, password: str) -> None:
        """
        Set user password (hashes the password).
        
        Args:
            password: Plain text password
        """
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    def check_password(self, password: str) -> bool:
        """
        Check if provided password matches user's password.
        
        Args:
            password: Plain text password to check
            
        Returns:
            True if password matches, False otherwise
        """
        if not self.password_hash:
            return False
        
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash)
    
    def update_last_login(self) -> None:
        """Update the last login timestamp."""
        self.last_login = datetime.now()
    
    def __str__(self) -> str:
        """Return string representation of the user."""
        return f"User({self.username})"
    
    def __repr__(self) -> str:
        """Return detailed string representation of the user."""
        return f"User(id={self.user_id}, username='{self.username}', email='{self.email}')"


class UserManager:
    """Manages users and provides authentication services."""
    
    def __init__(self, db_handler) -> None:
        """
        Initialize user manager.
        
        Args:
            db_handler: Database handler instance
        """
        self.db_handler = db_handler
        self.current_user: Optional[User] = None
    
    def register_user(self, username: str, password: str, email: str = "") -> Optional[User]:
        """
        Register a new user.
        
        Args:
            username: Desired username
            password: Plain text password
            email: Email address
            
        Returns:
            User object if successful, None if username already exists
            
        Raises:
            ValueError: If username or password is invalid
        """
        # Validate input
        if not username.strip():
            raise ValueError("Username cannot be empty")
        
        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")
        
        username = username.strip()
        
        # Check if user already exists
        if self.db_handler.user_exists(username):
            return None
        
        # Create new user
        user = User(username, email.strip())
        user.set_password(password)
        
        # Save to database
        user_id = self.db_handler.save_user(user)
        if user_id:
            user.user_id = user_id
            return user
        
        return None
    
    def login_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate and login a user.
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            User object if successful, None if authentication failed
        """
        if not username.strip() or not password:
            return None
        
        user = self.db_handler.load_user_by_username(username.strip())
        if user and user.check_password(password) and user.is_active:
            user.update_last_login()
            self.db_handler.update_user_last_login(user)
            self.current_user = user
            return user
        
        return None
    
    def logout_user(self) -> None:
        """Logout the current user."""
        self.current_user = None
    
    def get_current_user(self) -> Optional[User]:
        """
        Get the currently logged-in user.
        
        Returns:
            Current user or None if not logged in
        """
        return self.current_user
    
    def update_user(self, user: User) -> bool:
        """
        Update user information.
        
        Args:
            user: User to update
            
        Returns:
            True if successful, False otherwise
        """
        return self.db_handler.update_user(user)
    
    def change_password(self, user: User, old_password: str, new_password: str) -> bool:
        """
        Change user password.
        
        Args:
            user: User whose password to change
            old_password: Current password
            new_password: New password
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ValueError: If new password is invalid
        """
        if not user.check_password(old_password):
            return False
        
        if len(new_password) < 6:
            raise ValueError("New password must be at least 6 characters long")
        
        user.set_password(new_password)
        return self.update_user(user)
    
    def deactivate_user(self, user: User) -> bool:
        """
        Deactivate a user account.
        
        Args:
            user: User to deactivate
            
        Returns:
            True if successful, False otherwise
        """
        user.is_active = False
        return self.update_user(user)
    
    def get_all_users(self) -> List[User]:
        """
        Get all users (admin function).
        
        Returns:
            List of all users
        """
        return self.db_handler.load_all_users()
