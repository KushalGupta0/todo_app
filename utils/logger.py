"""
Logging configuration module.

This module sets up comprehensive logging for the To-Do List application.
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import sys
import traceback
from typing import Optional


class TodoLogger:
    """Centralized logging configuration for the application."""
    
    def __init__(self, app_name: str = "TodoApp") -> None:
        """
        Initialize the logging system.
        
        Args:
            app_name: Name of the application for log identification
        """
        self.app_name = app_name
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        
        # Create different loggers
        self.setup_loggers()
        
    def setup_loggers(self) -> None:
        """Set up all application loggers."""
        # Remove existing handlers to avoid duplicates
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s | Line:%(lineno)-4d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Set up root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # 1. Daily rotating file handler (all logs)
        daily_file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=self.logs_dir / f"{self.app_name}_app.log",
            when='midnight',
            interval=1,
            backupCount=30,  # Keep 30 days of logs
            encoding='utf-8'
        )
        daily_file_handler.setLevel(logging.DEBUG)
        daily_file_handler.setFormatter(detailed_formatter)
        daily_file_handler.suffix = "_%Y-%m-%d"
        root_logger.addHandler(daily_file_handler)
        
        # 2. Error-only file handler
        error_file_handler = logging.FileHandler(
            filename=self.logs_dir / "error.log",
            mode='a',
            encoding='utf-8'
        )
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_file_handler)
        
        # 3. Console handler (INFO and above)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)
        
        # 4. Create session log file
        session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_file_handler = logging.FileHandler(
            filename=self.logs_dir / f"session_{session_timestamp}.log",
            mode='w',
            encoding='utf-8'
        )
        session_file_handler.setLevel(logging.DEBUG)
        session_file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(session_file_handler)
        
        # Log the logging system initialization
        logging.info(f"Logging system initialized for {self.app_name}")
        logging.info(f"Log files location: {self.logs_dir.absolute()}")
        logging.info(f"Session log: session_{session_timestamp}.log")
        
    def log_exception(self, exception: Exception, context: str = "") -> None:
        """
        Log an exception with full traceback.
        
        Args:
            exception: The exception to log
            context: Additional context information
        """
        logger = logging.getLogger(__name__)
        logger.error(f"Exception occurred{' in ' + context if context else ''}: {str(exception)}")
        logger.error(f"Exception type: {type(exception).__name__}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        
    def log_user_action(self, user_id: Optional[int], action: str, details: str = "") -> None:
        """
        Log user actions for audit trail.
        
        Args:
            user_id: ID of the user performing the action
            action: Description of the action
            details: Additional details about the action
        """
        logger = logging.getLogger("user_actions")
        user_str = f"User {user_id}" if user_id else "Anonymous"
        logger.info(f"{user_str} | {action}{' | ' + details if details else ''}")
        
    def log_database_operation(self, operation: str, table: str, record_id: Optional[int] = None, success: bool = True) -> None:
        """
        Log database operations.
        
        Args:
            operation: Type of operation (CREATE, READ, UPDATE, DELETE)
            table: Database table name
            record_id: ID of the record (if applicable)
            success: Whether the operation was successful
        """
        logger = logging.getLogger("database")
        status = "SUCCESS" if success else "FAILED"
        record_str = f" (ID: {record_id})" if record_id else ""
        logger.info(f"{operation} {table}{record_str} - {status}")
        
    def log_performance(self, operation: str, duration_ms: float, details: str = "") -> None:
        """
        Log performance metrics.
        
        Args:
            operation: Name of the operation
            duration_ms: Duration in milliseconds
            details: Additional details
        """
        logger = logging.getLogger("performance")
        logger.info(f"{operation} took {duration_ms:.2f}ms{' | ' + details if details else ''}")


# Global logger instance
_todo_logger: Optional[TodoLogger] = None


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (uses calling module if None)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name or __name__)


def init_logging(app_name: str = "TodoApp") -> TodoLogger:
    """
    Initialize the logging system.
    
    Args:
        app_name: Application name
        
    Returns:
        TodoLogger instance
    """
    global _todo_logger
    _todo_logger = TodoLogger(app_name)
    return _todo_logger


def log_exception(exception: Exception, context: str = "") -> None:
    """
    Log an exception using the global logger.
    
    Args:
        exception: Exception to log
        context: Additional context
    """
    if _todo_logger:
        _todo_logger.log_exception(exception, context)
    else:
        logging.error(f"Exception: {exception} (logging not initialized)")


def log_user_action(user_id: Optional[int], action: str, details: str = "") -> None:
    """
    Log user action using the global logger.
    
    Args:
        user_id: User ID
        action: Action description
        details: Additional details
    """
    if _todo_logger:
        _todo_logger.log_user_action(user_id, action, details)


def log_database_operation(operation: str, table: str, record_id: Optional[int] = None, success: bool = True) -> None:
    """
    Log database operation using the global logger.
    
    Args:
        operation: Operation type
        table: Table name
        record_id: Record ID
        success: Success status
    """
    if _todo_logger:
        _todo_logger.log_database_operation(operation, table, record_id, success)


def log_performance(operation: str, duration_ms: float, details: str = "") -> None:
    """
    Log performance metric using the global logger.
    
    Args:
        operation: Operation name
        duration_ms: Duration in milliseconds
        details: Additional details
    """
    if _todo_logger:
        _todo_logger.log_performance(operation, duration_ms, details)
