"""
Main entry point for the To-Do List Application.

This module initializes the application and shows the login window.
"""

import sys
import os
import logging
from typing import Optional
from pathlib import Path

# Add the application directory to Python path
app_dir = Path(__file__).parent.absolute()
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))

# Change working directory to app directory for relative file operations
os.chdir(app_dir)

import time
import traceback
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QDir

from gui.login import LoginWindow
from database.db_handler import DatabaseHandler
from utils.logger import init_logging, get_logger, log_exception, log_performance


class TodoApplication:
    """Main application controller for the To-Do List app."""
    
    def __init__(self) -> None:
        """Initialize the application."""
        # Initialize logging first
        self.logger_system = init_logging("TodoApp")
        self.logger = get_logger(__name__)
        
        self.logger.info("=" * 80)
        self.logger.info("STARTING TO-DO LIST APPLICATION")
        self.logger.info("=" * 80)
        self.logger.info(f"Application directory: {app_dir}")
        self.logger.info(f"Working directory: {os.getcwd()}")
        
        start_time = time.time()
        
        try:
            self.app: QApplication = QApplication(sys.argv)
            self.db_handler: DatabaseHandler = DatabaseHandler()
            self.login_window: Optional[LoginWindow] = None
            
            # Set application properties
            self.app.setApplicationName("To-Do List Manager")
            self.app.setApplicationVersion("1.0.0")
            self.app.setOrganizationName("Todo App Inc.")
            
            self.logger.info("Application properties set")
            self.logger.info(f"PySide6 version: {self.app.applicationVersion()}")
            
            # Log system information
            self.logger.info(f"Python version: {sys.version}")
            self.logger.info(f"Platform: {sys.platform}")
            self.logger.info(f"Arguments: {sys.argv}")
            
            init_time = (time.time() - start_time) * 1000
            log_performance("Application initialization", init_time)
            
        except Exception as e:
            self.logger.error("Failed to initialize application")
            log_exception(e, "Application initialization")
            raise
        
    def run(self) -> int:
        """
        Run the application.
        
        Returns:
            int: Application exit code
        """
        try:
            self.logger.info("Starting application run sequence")
            
            # Initialize database
            start_time = time.time()
            self.logger.info("Initializing database...")
            self.db_handler.initialize_database()
            db_init_time = (time.time() - start_time) * 1000
            log_performance("Database initialization", db_init_time)
            self.logger.info("Database initialized successfully")
            
            # Show login window
            start_time = time.time()
            self.logger.info("Creating login window...")
            self.login_window = LoginWindow(self.db_handler)
            self.login_window.show()
            ui_init_time = (time.time() - start_time) * 1000
            log_performance("UI initialization", ui_init_time)
            self.logger.info("Login window displayed")
            
            self.logger.info("Application ready - entering main event loop")
            
            # Run the application
            exit_code = self.app.exec()
            
            self.logger.info(f"Application exiting with code: {exit_code}")
            return exit_code
            
        except Exception as e:
            self.logger.critical("Critical error during application run")
            log_exception(e, "Application run")
            return 1
        finally:
            self.logger.info("Application shutdown complete")
            self.logger.info("=" * 80)


def main() -> int:
    """
    Main function to start the application.
    
    Returns:
        int: Application exit code
    """
    try:
        app = TodoApplication()
        return app.run()
    except Exception as e:
        # Emergency logging if main logging system fails
        print(f"CRITICAL ERROR: Failed to start application: {e}")
        print(f"Traceback:\n{traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
