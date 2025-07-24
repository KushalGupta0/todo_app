"""
Login window module.

This module provides the login and registration interface.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QPushButton, QLabel, QTabWidget,
    QScrollArea, QFrame, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPalette

from core.user import UserManager
from utils.validators import validate_username, validate_password, validate_email, ValidationError
from gui.todowindow import TodoWindow


class LoginWindow(QWidget):
    """Main login window with login and registration tabs."""
    
    # Signals
    login_successful = Signal(object)  # Emits User object
    
    def __init__(self, db_handler) -> None:
        """
        Initialize login window.
        
        Args:
            db_handler: Database handler instance
        """
        super().__init__()
        self.db_handler = db_handler
        self.user_manager = UserManager(db_handler)
        self.todo_window: Optional[TodoWindow] = None
        
        self.setup_ui()
        self.setup_styles()
        self.connect_signals()
    
    def setup_ui(self) -> None:
        """Set up the user interface."""
        self.setWindowTitle("To-Do List Manager - Login")
        self.setFixedSize(500, 600)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Title
        title_label = QLabel("To-Do List Manager")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        main_layout.addWidget(title_label)
        
        # Create scroll area for better layout management
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        # Content widget for scroll area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # Tab widget for login/register
        self.tab_widget = QTabWidget()
        self.tab_widget.setMinimumHeight(400)
        
        # Login tab
        self.login_tab = self.create_login_tab()
        self.tab_widget.addTab(self.login_tab, "Login")
        
        # Register tab
        self.register_tab = self.create_register_tab()
        self.tab_widget.addTab(self.register_tab, "Register")
        
        content_layout.addWidget(self.tab_widget)
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(40)
        main_layout.addWidget(self.status_label)
        
        # Center window on screen
        self.center_on_screen()
    
    def create_login_tab(self) -> QWidget:
        """
        Create the login tab.
        
        Returns:
            Login tab widget
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 30, 20, 20)
        layout.setSpacing(20)
        
        # Login form
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # Username field
        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText("Enter your username")
        self.login_username.setMinimumHeight(40)
        form_layout.addRow("Username:", self.login_username)
        
        # Password field
        self.login_password = QLineEdit()
        self.login_password.setEchoMode(QLineEdit.Password)
        self.login_password.setPlaceholderText("Enter your password")
        self.login_password.setMinimumHeight(40)
        form_layout.addRow("Password:", self.login_password)
        
        layout.addLayout(form_layout)
        layout.addSpacing(20)
        
        # Login button
        self.login_button = QPushButton("Login")
        self.login_button.setMinimumHeight(45)
        self.login_button.setDefault(True)
        layout.addWidget(self.login_button)
        
        layout.addStretch()
        
        return tab
    
    def create_register_tab(self) -> QWidget:
        """
        Create the registration tab.
        
        Returns:
            Registration tab widget
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 30, 20, 20)
        layout.setSpacing(20)
        
        # Registration form
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # Username field
        self.register_username = QLineEdit()
        self.register_username.setPlaceholderText("Choose a username (3-50 characters)")
        self.register_username.setMinimumHeight(40)
        form_layout.addRow("Username:", self.register_username)
        
        # Email field (optional)
        self.register_email = QLineEdit()
        self.register_email.setPlaceholderText("Email address (optional)")
        self.register_email.setMinimumHeight(40)
        form_layout.addRow("Email:", self.register_email)
        
        # Password field
        self.register_password = QLineEdit()
        self.register_password.setEchoMode(QLineEdit.Password)
        self.register_password.setPlaceholderText("Choose a password (min. 6 characters)")
        self.register_password.setMinimumHeight(40)
        form_layout.addRow("Password:", self.register_password)
        
        # Confirm password field
        self.register_confirm_password = QLineEdit()
        self.register_confirm_password.setEchoMode(QLineEdit.Password)
        self.register_confirm_password.setPlaceholderText("Confirm your password")
        self.register_confirm_password.setMinimumHeight(40)
        form_layout.addRow("Confirm Password:", self.register_confirm_password)
        
        layout.addLayout(form_layout)
        layout.addSpacing(20)
        
        # Register button
        self.register_button = QPushButton("Create Account")
        self.register_button.setMinimumHeight(45)
        layout.addWidget(self.register_button)
        
        layout.addStretch()
        
        return tab
    
    def setup_styles(self) -> None:
        """Set up widget styles."""
        # Main window style
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11pt;
            }
            
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                background-color: white;
                border-radius: 8px;
            }
            
            QTabWidget::tab-bar {
                alignment: center;
            }
            
            QTabBar::tab {
                background-color: #e9ecef;
                color: #495057;
                padding: 12px 24px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 500;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                color: #007bff;
                border-bottom: 2px solid #007bff;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #f8f9fa;
            }
            
            QLineEdit {
                padding: 10px 12px;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                background-color: white;
                font-size: 11pt;
            }
            
            QLineEdit:focus {
                border-color: #007bff;
                outline: none;
            }
            
            QLineEdit:hover {
                border-color: #adb5bd;
            }
            
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 12pt;
                font-weight: 600;
            }
            
            QPushButton:hover {
                background-color: #0056b3;
            }
            
            QPushButton:pressed {
                background-color: #004085;
            }
            
            QPushButton:disabled {
                background-color: #6c757d;
                color: #dee2e6;
            }
            
            QLabel {
                color: #495057;
            }
            
            QFormLayout QLabel {
                font-weight: 500;
                color: #343a40;
            }
        """)
    
    def connect_signals(self) -> None:
        """Connect widget signals to slots."""
        # Login
        self.login_button.clicked.connect(self.handle_login)
        self.login_username.returnPressed.connect(self.handle_login)
        self.login_password.returnPressed.connect(self.handle_login)
        
        # Registration
        self.register_button.clicked.connect(self.handle_registration)
        self.register_confirm_password.returnPressed.connect(self.handle_registration)
        
        # Tab changes
        self.tab_widget.currentChanged.connect(self.clear_status)
    
    def center_on_screen(self) -> None:
        """Center the window on the screen."""
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        window_geometry = self.frameGeometry()
        center_point = screen_geometry.center()
        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())
    
    def handle_login(self) -> None:
        """Handle login button click."""
        username = self.login_username.text().strip()
        password = self.login_password.text()
        
        if not username or not password:
            self.show_error("Please enter both username and password")
            return
        
        # Disable login button during authentication
        self.login_button.setEnabled(False)
        self.login_button.setText("Logging in...")
        
        try:
            user = self.user_manager.login_user(username, password)
            if user:
                self.show_success(f"Welcome back, {user.username}!")
                self.open_todo_window(user)
            else:
                self.show_error("Invalid username or password")
        except Exception as e:
            self.show_error(f"Login failed: {str(e)}")
        finally:
            self.login_button.setEnabled(True)
            self.login_button.setText("Login")
    
    def handle_registration(self) -> None:
        """Handle registration button click."""
        username = self.register_username.text().strip()
        email = self.register_email.text().strip()
        password = self.register_password.text()
        confirm_password = self.register_confirm_password.text()
        
        # Validate input
        try:
            if not username:
                raise ValidationError("Username is required")
            
            username = validate_username(username)
            
            if email:
                email = validate_email(email)
            
            if not password:
                raise ValidationError("Password is required")
            
            password = validate_password(password)
            
            if password != confirm_password:
                raise ValidationError("Passwords do not match")
        
        except ValidationError as e:
            self.show_error(str(e))
            return
        
        # Disable register button during registration
        self.register_button.setEnabled(False)
        self.register_button.setText("Creating Account...")
        
        try:
            user = self.user_manager.register_user(username, password, email or "")
            if user:
                self.show_success("Account created successfully! You can now log in.")
                # Switch to login tab and fill username
                self.tab_widget.setCurrentIndex(0)
                self.login_username.setText(username)
                self.login_password.setFocus()
                self.clear_register_form()
            else:
                self.show_error("Username already exists. Please choose a different username.")
        except ValidationError as e:
            self.show_error(str(e))
        except Exception as e:
            self.show_error(f"Registration failed: {str(e)}")
        finally:
            self.register_button.setEnabled(True)
            self.register_button.setText("Create Account")
    
    def open_todo_window(self, user) -> None:
        """
        Open the main to-do window.
        
        Args:
            user: Logged-in user
        """
        try:
            self.todo_window = TodoWindow(self.db_handler, user)
            self.todo_window.show()
            self.hide()
            
            # Connect to logout signal
            self.todo_window.logout_requested.connect(self.handle_logout)
            
        except Exception as e:
            self.show_error(f"Failed to open main window: {str(e)}")
    
    def handle_logout(self) -> None:
        """Handle logout from main window."""
        self.user_manager.logout_user()
        self.clear_login_form()
        self.clear_register_form()
        self.clear_status()
        
        if self.todo_window:
            self.todo_window.close()
            self.todo_window = None
        
        self.show()
        self.login_username.setFocus()
    
    def show_error(self, message: str) -> None:
        """
        Show error message.
        
        Args:
            message: Error message to display
        """
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: #dc3545; font-weight: 500;")
    
    def show_success(self, message: str) -> None:
        """
        Show success message.
        
        Args:
            message: Success message to display
        """
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: #28a745; font-weight: 500;")
    
    def clear_status(self) -> None:
        """Clear status message."""
        self.status_label.setText("")
    
    def clear_login_form(self) -> None:
        """Clear login form fields."""
        self.login_username.clear()
        self.login_password.clear()
    
    def clear_register_form(self) -> None:
        """Clear registration form fields."""
        self.register_username.clear()
        self.register_email.clear()
        self.register_password.clear()
        self.register_confirm_password.clear()
    
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        if self.todo_window:
            self.todo_window.close()
        event.accept()
