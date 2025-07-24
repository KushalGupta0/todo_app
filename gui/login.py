"""
Login window module with comprehensive logging.

This module provides the login and registration interface with detailed logging.
"""

from typing import Optional
import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLineEdit, QPushButton, QLabel, QTabWidget,
    QScrollArea, QFrame, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPalette

from core.user import UserManager
from utils.validators import validate_username, validate_password, validate_email, ValidationError
from utils.logger import get_logger, log_user_action, log_exception, log_performance
from gui.todowindow import TodoWindow


class LoginWindow(QWidget):
    """Main login window with login and registration tabs with comprehensive logging."""
    
    # Signals
    login_successful = Signal(object)  # Emits User object
    
    def __init__(self, db_handler) -> None:
        """
        Initialize login window with logging.
        
        Args:
            db_handler: Database handler instance
        """
        super().__init__()
        self.db_handler = db_handler
        self.user_manager = UserManager(db_handler)
        self.todo_window: Optional[TodoWindow] = None
        self.logger = get_logger(__name__)
        
        self.logger.info("Login window initializing")
        start_time = time.time()
        
        try:
            self.setup_ui()
            self.setup_styles()
            self.connect_signals()
            
            init_time = (time.time() - start_time) * 1000
            log_performance("Login window initialization", init_time)
            self.logger.info("Login window initialized successfully")
            
        except Exception as e:
            self.logger.error("Failed to initialize login window")
            log_exception(e, "Login window initialization")
            raise
    
    def setup_ui(self) -> None:
        """Set up the user interface with logging."""
        self.logger.debug("Setting up login window UI")
        
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
        
        # CREATE STATUS LABEL FIRST (before tab widget)
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(40)
        
        # Tab widget for login/register
        self.tab_widget = QTabWidget()
        self.tab_widget.setMinimumHeight(400)
        # DON'T connect the signal here yet
        
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
        
        # Add status label at the bottom
        main_layout.addWidget(self.status_label)
        
        # Center window on screen
        self.center_on_screen()
        
        self.logger.debug("Login window UI setup completed")

    
    def create_login_tab(self) -> QWidget:
        """
        Create the login tab with logging.
        
        Returns:
            Login tab widget
        """
        self.logger.debug("Creating login tab")
        
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
        self.login_username.textChanged.connect(self.on_login_field_changed)
        form_layout.addRow("Username:", self.login_username)
        
        # Password field
        self.login_password = QLineEdit()
        self.login_password.setEchoMode(QLineEdit.Password)
        self.login_password.setPlaceholderText("Enter your password")
        self.login_password.setMinimumHeight(40)
        self.login_password.textChanged.connect(self.on_login_field_changed)
        form_layout.addRow("Password:", self.login_password)
        
        layout.addLayout(form_layout)
        layout.addSpacing(20)
        
        # Login button
        self.login_button = QPushButton("Login")
        self.login_button.setMinimumHeight(45)
        self.login_button.setDefault(True)
        layout.addWidget(self.login_button)
        
        layout.addStretch()
        
        self.logger.debug("Login tab created successfully")
        return tab
    
    def create_register_tab(self) -> QWidget:
        """
        Create the registration tab with logging.
        
        Returns:
            Registration tab widget
        """
        self.logger.debug("Creating registration tab")
        
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
        self.register_username.textChanged.connect(self.on_register_field_changed)
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
        self.register_password.textChanged.connect(self.on_register_field_changed)
        form_layout.addRow("Password:", self.register_password)
        
        # Confirm password field
        self.register_confirm_password = QLineEdit()
        self.register_confirm_password.setEchoMode(QLineEdit.Password)
        self.register_confirm_password.setPlaceholderText("Confirm your password")
        self.register_confirm_password.setMinimumHeight(40)
        self.register_confirm_password.textChanged.connect(self.on_register_field_changed)
        form_layout.addRow("Confirm Password:", self.register_confirm_password)
        
        layout.addLayout(form_layout)
        layout.addSpacing(20)
        
        # Register button
        self.register_button = QPushButton("Create Account")
        self.register_button.setMinimumHeight(45)
        layout.addWidget(self.register_button)
        
        # Password requirements instructions
        password_instructions = QLabel("""
    Password Requirements:
    • At least 6 characters long
    • Must contain at least one letter
    • Must contain at least one number
    • Avoid common passwords for better security
        """.strip())
        password_instructions.setStyleSheet("""
            color: #6c757d;
            font-size: 9pt;
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 10px;
            margin-top: 10px;
        """)
        password_instructions.setWordWrap(True)
        layout.addWidget(password_instructions)
        
        layout.addStretch()
        
        self.logger.debug("Registration tab created successfully")
        return tab

    
    def setup_styles(self) -> None:
        """Set up widget styles."""
        self.logger.debug("Setting up login window styles")
        
        # Main window style
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11pt;
                color: black;
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
                color: black;
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
                color: black;
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
                color: black;
            }
            
            QFormLayout QLabel {
                font-weight: 500;
                color: black;
            }
        """)
        
        self.logger.debug("Login window styles applied")

    
    def connect_signals(self) -> None:
        """Connect widget signals to slots with logging."""
        self.logger.debug("Connecting login window signals")
        
        # Login
        self.login_button.clicked.connect(self.handle_login)
        self.login_username.returnPressed.connect(self.handle_login)
        self.login_password.returnPressed.connect(self.handle_login)
        
        # Registration
        self.register_button.clicked.connect(self.handle_registration)
        self.register_confirm_password.returnPressed.connect(self.handle_registration)
        
        # Tab changes - CONNECT AFTER UI IS FULLY INITIALIZED
        self.tab_widget.currentChanged.connect(self.clear_status)
        
        self.logger.debug("Login window signals connected")
    
    def center_on_screen(self) -> None:
        """Center the window on the screen."""
        self.logger.debug("Centering login window on screen")
        
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        window_geometry = self.frameGeometry()
        center_point = screen_geometry.center()
        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())
    
    def on_tab_changed(self, index: int) -> None:
        """Handle tab change with logging."""
        tab_names = ["Login", "Register"]
        tab_name = tab_names[index] if index < len(tab_names) else f"Tab {index}"
        
        self.logger.debug(f"User switched to {tab_name} tab")
        log_user_action(None, "TAB_SWITCH", f"Switched to {tab_name} tab")
        self.clear_status()
    
    def on_login_field_changed(self) -> None:
        """Handle login field changes."""
        # Clear status when user starts typing
        if self.status_label.text():
            self.clear_status()
    
    def on_register_field_changed(self) -> None:
        """Handle registration field changes."""
        # Clear status when user starts typing
        if self.status_label.text():
            self.clear_status()
    
    def handle_login(self) -> None:
        """Handle login button click with comprehensive logging."""
        start_time = time.time()
        username = self.login_username.text().strip()
        password = self.login_password.text()
        
        self.logger.info(f"Login attempt initiated for username: {username}")
        log_user_action(None, "LOGIN_ATTEMPT", f"Login attempt for username: {username}")
        
        if not username or not password:
            self.show_error("Please enter both username and password")
            self.logger.warning("Login attempt with empty credentials")
            log_user_action(None, "LOGIN_FAILED", "Empty credentials provided")
            return
        
        # Disable login button during authentication
        self.login_button.setEnabled(False)
        self.login_button.setText("Logging in...")
        self.logger.debug("Login button disabled during authentication")
        
        try:
            user = self.user_manager.login_user(username, password)
            if user:
                login_time = (time.time() - start_time) * 1000
                log_performance("Login process", login_time)
                
                self.show_success(f"Welcome back, {user.username}!")
                self.logger.info(f"Login successful for user: {username}")
                log_user_action(user.user_id, "LOGIN_SUCCESS", f"Successful login for {username}")
                
                self.open_todo_window(user)
            else:
                login_time = (time.time() - start_time) * 1000
                log_performance("Login process (failed)", login_time)
                
                self.show_error("Invalid username or password")
                self.logger.warning(f"Login failed for user: {username}")
                log_user_action(None, "LOGIN_FAILED", f"Invalid credentials for {username}")
                
        except Exception as e:
            login_time = (time.time() - start_time) * 1000
            log_performance("Login process (error)", login_time)
            
            self.show_error(f"Login failed: {str(e)}")
            self.logger.error(f"Login error for user {username}")
            log_user_action(None, "LOGIN_ERROR", f"System error during login for {username}")
            log_exception(e, f"Login for user {username}")
        finally:
            self.login_button.setEnabled(True)
            self.login_button.setText("Login")
            self.logger.debug("Login button re-enabled")
    
    def handle_registration(self) -> None:
        """Handle registration button click with comprehensive logging."""
        start_time = time.time()
        username = self.register_username.text().strip()
        email = self.register_email.text().strip()
        password = self.register_password.text()
        confirm_password = self.register_confirm_password.text()
        
        self.logger.info(f"Registration attempt initiated for username: {username}")
        log_user_action(None, "REGISTRATION_ATTEMPT", f"Registration attempt for username: {username}")
        
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
            validation_time = (time.time() - start_time) * 1000
            log_performance("Registration validation (failed)", validation_time)
            
            self.show_error(str(e))
            self.logger.warning(f"Registration validation failed for {username}: {str(e)}")
            log_user_action(None, "REGISTRATION_VALIDATION_FAILED", f"Validation failed for {username}: {str(e)}")
            return
        
        # Disable register button during registration
        self.register_button.setEnabled(False)
        self.register_button.setText("Creating Account...")
        self.logger.debug("Registration button disabled during account creation")
        
        try:
            user = self.user_manager.register_user(username, password, email or "")
            if user:
                registration_time = (time.time() - start_time) * 1000
                log_performance("Registration process", registration_time)
                
                self.show_success("Account created successfully! You can now log in.")
                self.logger.info(f"Registration successful for user: {username}")
                log_user_action(user.user_id, "REGISTRATION_SUCCESS", f"Account created for {username}")
                
                # Switch to login tab and fill username
                self.tab_widget.setCurrentIndex(0)
                self.login_username.setText(username)
                self.login_password.setFocus()
                self.clear_register_form()
                
                self.logger.debug(f"Switched to login tab and pre-filled username for {username}")
            else:
                registration_time = (time.time() - start_time) * 1000
                log_performance("Registration process (failed)", registration_time)
                
                self.show_error("Username already exists. Please choose a different username.")
                self.logger.warning(f"Registration failed for {username}: Username already exists")
                log_user_action(None, "REGISTRATION_FAILED", f"Username {username} already exists")
                
        except ValidationError as e:
            registration_time = (time.time() - start_time) * 1000
            log_performance("Registration process (validation error)", registration_time)
            
            self.show_error(str(e))
            self.logger.warning(f"Registration validation error for {username}: {str(e)}")
            log_user_action(None, "REGISTRATION_VALIDATION_ERROR", f"Validation error for {username}: {str(e)}")
        except Exception as e:
            registration_time = (time.time() - start_time) * 1000
            log_performance("Registration process (error)", registration_time)
            
            self.show_error(f"Registration failed: {str(e)}")
            self.logger.error(f"Registration error for {username}")
            log_user_action(None, "REGISTRATION_ERROR", f"System error during registration for {username}")
            log_exception(e, f"Registration for {username}")
        finally:
            self.register_button.setEnabled(True)
            self.register_button.setText("Create Account")
            self.logger.debug("Registration button re-enabled")
    
    def open_todo_window(self, user) -> None:
        """
        Open the main to-do window with comprehensive logging.
        
        Args:
            user: Logged-in user
        """
        start_time = time.time()
        self.logger.info(f"Opening main window for user: {user.username}")
        
        try:
            self.todo_window = TodoWindow(self.db_handler, user)
            self.todo_window.show()
            self.hide()
            
            # Connect to logout signal
            self.todo_window.logout_requested.connect(self.handle_logout)
            
            window_open_time = (time.time() - start_time) * 1000
            log_performance("Open main window", window_open_time)
            
            self.logger.info(f"Main window opened successfully for user: {user.username}")
            log_user_action(user.user_id, "MAIN_WINDOW_OPENED", f"Main application window opened for {user.username}")
            
        except Exception as e:
            window_open_time = (time.time() - start_time) * 1000
            log_performance("Open main window (error)", window_open_time)
            
            self.show_error(f"Failed to open main window: {str(e)}")
            self.logger.error(f"Failed to open main window for user: {user.username}")
            log_user_action(user.user_id, "MAIN_WINDOW_ERROR", f"Failed to open main window for {user.username}")
            log_exception(e, f"Opening main window for {user.username}")
    
    def handle_logout(self) -> None:
        """Handle logout from main window with logging."""
        current_user = self.user_manager.get_current_user()
        if current_user:
            self.logger.info(f"Handling logout for user: {current_user.username}")
            log_user_action(current_user.user_id, "LOGOUT_INITIATED", f"Logout initiated for {current_user.username}")
        
        self.user_manager.logout_user()
        self.clear_login_form()
        self.clear_register_form()
        self.clear_status()
        
        if self.todo_window:
            self.todo_window.close()
            self.todo_window = None
            self.logger.debug("Main window closed during logout")
        
        self.show()
        self.login_username.setFocus()
        
        self.logger.info("Logout completed, returned to login window")
        log_user_action(None, "LOGOUT_COMPLETED", "User returned to login window")
    
    def show_error(self, message: str) -> None:
        """
        Show error message with logging.
        
        Args:
            message: Error message to display
        """
        self.logger.debug(f"Displaying error message: {message}")
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: #dc3545; font-weight: 500;")
    
    def show_success(self, message: str) -> None:
        """
        Show success message with logging.
        
        Args:
            message: Success message to display
        """
        self.logger.debug(f"Displaying success message: {message}")
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: #28a745; font-weight: 500;")
    
    def clear_status(self) -> None:
        """Clear status message."""
        self.status_label.setText("")
        self.logger.debug("Status message cleared")
    
    def clear_login_form(self) -> None:
        """Clear login form fields with logging."""
        self.logger.debug("Clearing login form fields")
        self.login_username.clear()
        self.login_password.clear()
    
    def clear_register_form(self) -> None:
        """Clear registration form fields with logging."""
        self.logger.debug("Clearing registration form fields")
        self.register_username.clear()
        self.register_email.clear()
        self.register_password.clear()
        self.register_confirm_password.clear()
    
    def closeEvent(self, event) -> None:
        """Handle window close event with logging."""
        self.logger.info("Login window close event triggered")
        
        current_user = self.user_manager.get_current_user()
        if current_user:
            log_user_action(current_user.user_id, "APPLICATION_EXIT", f"Application closed by {current_user.username}")
        else:
            log_user_action(None, "APPLICATION_EXIT", "Application closed from login window")
        
        if self.todo_window:
            self.logger.debug("Closing main window during login window close")
            self.todo_window.close()
        
        self.logger.info("Login window closed")
        event.accept()
    
    def showEvent(self, event) -> None:
        """Handle window show event with logging."""
        self.logger.debug("Login window shown")
        log_user_action(None, "LOGIN_WINDOW_SHOWN", "Login window displayed to user")
        super().showEvent(event)
    
    def hideEvent(self, event) -> None:
        """Handle window hide event with logging."""
        self.logger.debug("Login window hidden")
        super().hideEvent(event)
