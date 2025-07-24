"""
User management module with comprehensive logging.

This module handles user authentication, registration, and user data management.
"""

from typing import Optional, List
import bcrypt
import time
from datetime import datetime

from utils.logger import get_logger, log_user_action, log_exception, log_performance


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
    """Manages users and provides authentication services with comprehensive logging."""
    
    def __init__(self, db_handler) -> None:
        """
        Initialize user manager.
        
        Args:
            db_handler: Database handler instance
        """
        self.db_handler = db_handler
        self.current_user: Optional[User] = None
        self.logger = get_logger(__name__)
        self.logger.info("UserManager initialized")
    
    def register_user(self, username: str, password: str, email: str = "") -> Optional[User]:
        """
        Register a new user with comprehensive logging.
        
        Args:
            username: Desired username
            password: Plain text password
            email: Email address
            
        Returns:
            User object if successful, None if username already exists
            
        Raises:
            ValueError: If username or password is invalid
        """
        start_time = time.time()
        self.logger.info(f"Registration attempt for username: {username}")
        
        try:
            # Validate input
            if not username.strip():
                raise ValueError("Username cannot be empty")
            
            if len(password) < 6:
                raise ValueError("Password must be at least 6 characters long")
            
            username = username.strip()
            
            # Check if user already exists
            if self.db_handler.user_exists(username):
                self.logger.warning(f"Registration failed for {username}: Username already exists")
                log_user_action(None, "REGISTRATION_FAILED", f"Username {username} already exists")
                return None
            
            # Create new user
            user = User(username, email.strip())
            user.set_password(password)
            
            # Save to database
            user_id = self.db_handler.save_user(user)
            if user_id:
                user.user_id = user_id
                
                duration = (time.time() - start_time) * 1000
                log_performance("User registration", duration)
                log_user_action(user_id, "REGISTRATION", f"New user registered: {username}")
                self.logger.info(f"User {username} registered successfully with ID: {user_id}")
                
                return user
            else:
                self.logger.error(f"Failed to save user {username} to database")
                log_user_action(None, "REGISTRATION_FAILED", f"Failed to save user {username} to database")
                
        except ValueError as e:
            duration = (time.time() - start_time) * 1000
            log_performance("User registration (validation error)", duration)
            self.logger.warning(f"Registration validation error for {username}: {e}")
            log_user_action(None, "REGISTRATION_FAILED", f"Validation error for {username}: {str(e)}")
            raise
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            log_performance("User registration (error)", duration)
            self.logger.error(f"Registration error for {username}: {e}")
            log_user_action(None, "REGISTRATION_FAILED", f"System error for {username}")
            log_exception(e, f"User registration for {username}")
        
        return None
    
    def login_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate and login a user with comprehensive logging.
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            User object if successful, None if authentication failed
        """
        start_time = time.time()
        self.logger.info(f"Login attempt for username: {username}")
        
        if not username.strip() or not password:
            self.logger.warning(f"Login failed for {username}: Empty credentials")
            log_user_action(None, "LOGIN_FAILED", f"Empty credentials for {username}")
            return None
        
        try:
            user = self.db_handler.load_user_by_username(username.strip())
            if user and user.check_password(password) and user.is_active:
                user.update_last_login()
                self.db_handler.update_user_last_login(user)
                self.current_user = user
                
                duration = (time.time() - start_time) * 1000
                log_performance("User login", duration)
                log_user_action(user.user_id, "LOGIN", f"Successful login from {username}")
                self.logger.info(f"User {username} logged in successfully")
                
                return user
            else:
                duration = (time.time() - start_time) * 1000
                log_performance("User login (failed)", duration)
                log_user_action(None, "LOGIN_FAILED", f"Failed login attempt for {username}")
                self.logger.warning(f"Login failed for {username}: Invalid credentials or inactive account")
                
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            log_performance("User login (error)", duration)
            self.logger.error(f"Login error for {username}: {e}")
            log_user_action(None, "LOGIN_ERROR", f"System error during login for {username}")
            log_exception(e, f"User login for {username}")
        
        return None
    
    def logout_user(self) -> None:
        """Logout the current user with logging."""
        if self.current_user:
            log_user_action(self.current_user.user_id, "LOGOUT", f"User {self.current_user.username} logged out")
            self.logger.info(f"User {self.current_user.username} logged out")
            self.current_user = None
        else:
            self.logger.debug("Logout called but no user was logged in")
    
    def get_current_user(self) -> Optional[User]:
        """
        Get the currently logged-in user.
        
        Returns:
            Current user or None if not logged in
        """
        return self.current_user
    
    def update_user(self, user: User) -> bool:
        """
        Update user information with logging.
        
        Args:
            user: User to update
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        self.logger.info(f"Updating user information for: {user.username}")
        
        try:
            success = self.db_handler.update_user(user)
            
            duration = (time.time() - start_time) * 1000
            log_performance("Update user", duration)
            
            if success:
                log_user_action(user.user_id, "USER_UPDATE", f"User information updated for {user.username}")
                self.logger.info(f"User {user.username} information updated successfully")
            else:
                log_user_action(user.user_id, "USER_UPDATE_FAILED", f"Failed to update user information for {user.username}")
                self.logger.warning(f"Failed to update user {user.username} information")
            
            return success
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            log_performance("Update user (error)", duration)
            self.logger.error(f"Error updating user {user.username}: {e}")
            log_user_action(user.user_id, "USER_UPDATE_ERROR", f"System error updating {user.username}")
            log_exception(e, f"Updating user {user.username}")
            return False
    
    def change_password(self, user: User, old_password: str, new_password: str) -> bool:
        """
        Change user password with logging.
        
        Args:
            user: User whose password to change
            old_password: Current password
            new_password: New password
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            ValueError: If new password is invalid
        """
        start_time = time.time()
        self.logger.info(f"Password change attempt for user: {user.username}")
        
        try:
            if not user.check_password(old_password):
                self.logger.warning(f"Password change failed for {user.username}: Incorrect old password")
                log_user_action(user.user_id, "PASSWORD_CHANGE_FAILED", f"Incorrect old password for {user.username}")
                return False
            
            if len(new_password) < 6:
                raise ValueError("New password must be at least 6 characters long")
            
            user.set_password(new_password)
            success = self.update_user(user)
            
            duration = (time.time() - start_time) * 1000
            log_performance("Change password", duration)
            
            if success:
                log_user_action(user.user_id, "PASSWORD_CHANGED", f"Password changed for {user.username}")
                self.logger.info(f"Password changed successfully for user: {user.username}")
            else:
                log_user_action(user.user_id, "PASSWORD_CHANGE_FAILED", f"Failed to save new password for {user.username}")
                self.logger.error(f"Failed to save new password for user: {user.username}")
            
            return success
            
        except ValueError as e:
            duration = (time.time() - start_time) * 1000
            log_performance("Change password (validation error)", duration)
            self.logger.warning(f"Password change validation error for {user.username}: {e}")
            log_user_action(user.user_id, "PASSWORD_CHANGE_FAILED", f"Validation error for {user.username}: {str(e)}")
            raise
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            log_performance("Change password (error)", duration)
            self.logger.error(f"Password change error for {user.username}: {e}")
            log_user_action(user.user_id, "PASSWORD_CHANGE_ERROR", f"System error for {user.username}")
            log_exception(e, f"Password change for {user.username}")
            return False
    
    def deactivate_user(self, user: User) -> bool:
        """
        Deactivate a user account with logging.
        
        Args:
            user: User to deactivate
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        self.logger.info(f"Deactivating user account: {user.username}")
        
        try:
            user.is_active = False
            success = self.update_user(user)
            
            duration = (time.time() - start_time) * 1000
            log_performance("Deactivate user", duration)
            
            if success:
                log_user_action(user.user_id, "USER_DEACTIVATED", f"User account deactivated: {user.username}")
                self.logger.info(f"User account deactivated: {user.username}")
                
                # Logout if this is the current user
                if self.current_user and self.current_user.user_id == user.user_id:
                    self.logout_user()
            else:
                log_user_action(user.user_id, "USER_DEACTIVATION_FAILED", f"Failed to deactivate user: {user.username}")
                self.logger.error(f"Failed to deactivate user: {user.username}")
            
            return success
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            log_performance("Deactivate user (error)", duration)
            self.logger.error(f"Error deactivating user {user.username}: {e}")
            log_user_action(user.user_id, "USER_DEACTIVATION_ERROR", f"System error deactivating {user.username}")
            log_exception(e, f"Deactivating user {user.username}")
            return False
    
    def activate_user(self, user: User) -> bool:
        """
        Activate a user account with logging.
        
        Args:
            user: User to activate
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        self.logger.info(f"Activating user account: {user.username}")
        
        try:
            user.is_active = True
            success = self.update_user(user)
            
            duration = (time.time() - start_time) * 1000
            log_performance("Activate user", duration)
            
            if success:
                log_user_action(user.user_id, "USER_ACTIVATED", f"User account activated: {user.username}")
                self.logger.info(f"User account activated: {user.username}")
            else:
                log_user_action(user.user_id, "USER_ACTIVATION_FAILED", f"Failed to activate user: {user.username}")
                self.logger.error(f"Failed to activate user: {user.username}")
            
            return success
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            log_performance("Activate user (error)", duration)
            self.logger.error(f"Error activating user {user.username}: {e}")
            log_user_action(user.user_id, "USER_ACTIVATION_ERROR", f"System error activating {user.username}")
            log_exception(e, f"Activating user {user.username}")
            return False
    
    def get_all_users(self) -> List[User]:
        """
        Get all users (admin function) with logging.
        
        Returns:
            List of all users
        """
        start_time = time.time()
        self.logger.info("Loading all users (admin function)")
        
        try:
            users = self.db_handler.load_all_users()
            
            duration = (time.time() - start_time) * 1000
            log_performance("Get all users", duration, f"Loaded {len(users)} users")
            
            current_user_id = self.current_user.user_id if self.current_user else None
            log_user_action(current_user_id, "ADMIN_VIEW_USERS", f"Loaded {len(users)} users")
            self.logger.info(f"Loaded {len(users)} users")
            
            return users
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            log_performance("Get all users (error)", duration)
            self.logger.error(f"Error loading all users: {e}")
            
            current_user_id = self.current_user.user_id if self.current_user else None
            log_user_action(current_user_id, "ADMIN_VIEW_USERS_ERROR", "System error loading users")
            log_exception(e, "Getting all users")
            
            return []
    
    def is_user_logged_in(self) -> bool:
        """
        Check if a user is currently logged in.
        
        Returns:
            True if user is logged in, False otherwise
        """
        return self.current_user is not None
    
    def get_user_session_info(self) -> dict:
        """
        Get current user session information.
        
        Returns:
            Dictionary with session information
        """
        if not self.current_user:
            return {"logged_in": False}
        
        return {
            "logged_in": True,
            "user_id": self.current_user.user_id,
            "username": self.current_user.username,
            "email": self.current_user.email,
            "last_login": self.current_user.last_login.isoformat() if self.current_user.last_login else None,
            "is_active": self.current_user.is_active
        }
