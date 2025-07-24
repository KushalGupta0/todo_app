"""
Input validation utilities.

This module provides validation functions for user input and data integrity.
"""

import re
from typing import Optional


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_username(username: str) -> str:
    """
    Validate username format and constraints.
    
    Args:
        username: Username to validate
        
    Returns:
        Cleaned username
        
    Raises:
        ValidationError: If username is invalid
    """
    if not username:
        raise ValidationError("Username cannot be empty")
    
    username = username.strip()
    
    if len(username) < 3:
        raise ValidationError("Username must be at least 3 characters long")
    
    if len(username) > 50:
        raise ValidationError("Username cannot be longer than 50 characters")
    
    # Check for valid characters (alphanumeric, underscore, hyphen)
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        raise ValidationError("Username can only contain letters, numbers, underscores, and hyphens")
    
    # Must start with a letter or number
    if not re.match(r'^[a-zA-Z0-9]', username):
        raise ValidationError("Username must start with a letter or number")
    
    return username


def validate_password(password: str) -> str:
    """
    Validate password strength and constraints.
    
    Args:
        password: Password to validate
        
    Returns:
        Password (unchanged)
        
    Raises:
        ValidationError: If password is invalid
    """
    if not password:
        raise ValidationError("Password cannot be empty")
    
    if len(password) < 6:
        raise ValidationError("Password must be at least 6 characters long")
    
    if len(password) > 128:
        raise ValidationError("Password cannot be longer than 128 characters")
    
    # Check for at least one letter and one number (basic strength)
    has_letter = bool(re.search(r'[a-zA-Z]', password))
    has_number = bool(re.search(r'\d', password))
    
    if not (has_letter and has_number):
        raise ValidationError("Password must contain at least one letter and one number")
    
    return password


def validate_email(email: str) -> Optional[str]:
    """
    Validate email format.
    
    Args:
        email: Email to validate
        
    Returns:
        Cleaned email or None if empty
        
    Raises:
        ValidationError: If email format is invalid
    """
    if not email:
        return None
    
    email = email.strip().lower()
    
    if len(email) > 254:
        raise ValidationError("Email address is too long")
    
    # Basic email validation regex
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        raise ValidationError("Invalid email format")
    
    return email


def validate_task_title(title: str) -> str:
    """
    Validate task title.
    
    Args:
        title: Task title to validate
        
    Returns:
        Cleaned title
        
    Raises:
        ValidationError: If title is invalid
    """
    if not title:
        raise ValidationError("Task title cannot be empty")
    
    title = title.strip()
    
    if len(title) > 200:
        raise ValidationError("Task title cannot be longer than 200 characters")
    
    return title


def validate_tag_name(name: str) -> str:
    """
    Validate tag name.
    
    Args:
        name: Tag name to validate
        
    Returns:
        Cleaned tag name
        
    Raises:
        ValidationError: If tag name is invalid
    """
    if not name:
        raise ValidationError("Tag name cannot be empty")
    
    name = name.strip()
    
    if len(name) > 50:
        raise ValidationError("Tag name cannot be longer than 50 characters")
    
    # Check for valid characters
    if not re.match(r'^[a-zA-Z0-9\s_-]+$', name):
        raise ValidationError("Tag name can only contain letters, numbers, spaces, underscores, and hyphens")
    
    return name


def validate_hex_color(color: str) -> str:
    """
    Validate hex color code.
    
    Args:
        color: Hex color code to validate
        
    Returns:
        Validated color code
        
    Raises:
        ValidationError: If color code is invalid
    """
    if not color:
        raise ValidationError("Color code cannot be empty")
    
    color = color.strip()
    
    # Ensure it starts with #
    if not color.startswith('#'):
        color = '#' + color
    
    # Validate hex format
    if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
        raise ValidationError("Invalid hex color format (use #RRGGBB)")
    
    return color.upper()


def sanitize_input(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize text input by removing potentially harmful characters.
    
    Args:
        text: Text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove control characters except newlines and tabs
    sanitized = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    
    # Limit length if specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()
