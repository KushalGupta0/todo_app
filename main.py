"""
Main entry point for the To-Do List Application.

This module initializes the application and shows the login window.
"""

import sys
from typing import Optional
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QDir

from gui.login import LoginWindow
from database.db_handler import DatabaseHandler


class TodoApplication:
    """Main application controller for the To-Do List app."""
    
    def __init__(self) -> None:
        """Initialize the application."""
        self.app: QApplication = QApplication(sys.argv)
        self.db_handler: DatabaseHandler = DatabaseHandler()
        self.login_window: Optional[LoginWindow] = None
        
        # Set application properties
        self.app.setApplicationName("To-Do List Manager")
        self.app.setApplicationVersion("1.0.0")
        self.app.setOrganizationName("Todo App Inc.")
        
    def run(self) -> int:
        """
        Run the application.
        
        Returns:
            int: Application exit code
        """
        try:
            # Initialize database
            self.db_handler.initialize_database()
            
            # Show login window
            self.login_window = LoginWindow(self.db_handler)
            self.login_window.show()
            
            return self.app.exec()
            
        except Exception as e:
            print(f"Application error: {e}")
            return 1


def main() -> int:
    """
    Main function to start the application.
    
    Returns:
        int: Application exit code
    """
    app = TodoApplication()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
