"""
Main To-Do window module.

This module provides the main application interface for task management.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QSplitter, QTreeWidget, QTreeWidgetItem, QLineEdit,
    QPushButton, QLabel, QComboBox, QTextEdit, QDialog,
    QFormLayout, QDialogButtonBox, QMessageBox, QMenuBar,
    QMenu, QToolBar, QStatusBar, QCheckBox, QDateEdit,
    QScrollArea, QFrame, QGroupBox, QTabWidget
)
from PySide6.QtCore import Qt, Signal, QTimer, QDate
from PySide6.QtGui import QAction, QFont, QIcon, QPalette

from core.tasks import TaskManager, Task, Priority
from core.user import User
from gui.widgets import TaskWidget, TaskTreeWidget

import time
from utils.logger import log_performance, log_exception


class AddTaskDialog(QDialog):
    """Dialog for adding new tasks."""
    
    def __init__(self, parent=None, parent_task: Optional[Task] = None) -> None:
        """
        Initialize add task dialog.
        
        Args:
            parent: Parent widget
            parent_task: Parent task for creating subtasks
        """
        super().__init__(parent)
        self.parent_task = parent_task
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Set up the dialog UI."""
        self.setWindowTitle("Add New Task" if not self.parent_task else "Add Subtask")
        self.setModal(True)
        self.setMinimumSize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Title
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Enter task title...")
        form_layout.addRow("Title:", self.title_edit)
        
        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter task description (optional)...")
        self.description_edit.setMaximumHeight(100)
        form_layout.addRow("Description:", self.description_edit)
        
        # Priority
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Low", "Medium", "High", "Urgent"])
        self.priority_combo.setCurrentText("Medium")
        form_layout.addRow("Priority:", self.priority_combo)
        
        # Due date
        self.due_date_edit = QDateEdit()
        self.due_date_edit.setDate(QDate.currentDate())
        self.due_date_checkbox = QCheckBox("Set due date")
        due_date_layout = QHBoxLayout()
        due_date_layout.addWidget(self.due_date_checkbox)
        due_date_layout.addWidget(self.due_date_edit)
        form_layout.addRow("Due Date:", due_date_layout)
        
        # Initially disable due date
        self.due_date_edit.setEnabled(False)
        self.due_date_checkbox.toggled.connect(self.due_date_edit.setEnabled)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Focus on title
        self.title_edit.setFocus()
    
    def get_task_data(self) -> Dict[str, Any]:
        """
        Get task data from dialog.
        
        Returns:
            Dictionary with task data
        """
        priority_map = {
            "Low": Priority.LOW,
            "Medium": Priority.MEDIUM,
            "High": Priority.HIGH,
            "Urgent": Priority.URGENT
        }
        
        data = {
            'title': self.title_edit.text().strip(),
            'description': self.description_edit.toPlainText().strip(),
            'priority': priority_map[self.priority_combo.currentText()],
            'due_date': None
        }
        
        if self.due_date_checkbox.isChecked():
            qdate = self.due_date_edit.date()
            data['due_date'] = datetime(qdate.year(), qdate.month(), qdate.day())
        
        return data


class TodoWindow(QMainWindow):
    """Main To-Do List application window."""
    
    # Signals
    logout_requested = Signal()
    
    def __init__(self, db_handler, user: User) -> None:
        """
        Initialize the main window.
        
        Args:
            db_handler: Database handler instance
            user: Current logged-in user
        """
        super().__init__()
        self.db_handler = db_handler
        self.user = user
        self.task_manager = TaskManager(db_handler)
        
        from utils.logger import get_logger
        self.logger = get_logger(__name__)

        # State variables
        self.current_tasks: List[Task] = []
        self.filtered_tasks: List[Task] = []
        
        self.setup_ui()
        self.setup_menus()
        self.setup_toolbar()
        self.setup_statusbar()
        self.connect_signals()
        self.load_data()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_tasks)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
    
    def setup_ui(self) -> None:
        """Set up the main user interface."""
        self.setWindowTitle(f"To-Do List Manager - {self.user.username}")
        self.setMinimumSize(1000, 700)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel (filters and actions)
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel (task list)
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([300, 700])
        
        # Apply styles
        self.setup_styles()
    
    def create_left_panel(self) -> QWidget:
        """
        Create the left control panel.
        
        Returns:
            Left panel widget
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
        # User info
        user_group = QGroupBox("User")
        user_layout = QVBoxLayout(user_group)
        
        user_label = QLabel(f"Welcome, {self.user.username}")
        user_label.setStyleSheet("font-weight: bold; font-size: 12pt; color: #000000;")
        user_layout.addWidget(user_label)
        
        logout_btn = QPushButton("Logout")
        logout_btn.clicked.connect(self.logout_requested.emit)
        user_layout.addWidget(logout_btn)
        
        layout.addWidget(user_group)
        
        # Quick actions
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QVBoxLayout(actions_group)
        
        self.add_task_btn = QPushButton("+ Add Task")
        #self.add_task_btn.setStyleSheet("font-weight: bold; color: #ffffff; background-color: #007bff; border-radius: 4px; padding: 8px 16px;")
        actions_layout.addWidget(self.add_task_btn)
        
        layout.addWidget(actions_group)
        
        # Filters
        filters_group = QGroupBox("Filters")
        filters_main_layout = QVBoxLayout(filters_group)
        filters_main_layout.setContentsMargins(5, 15, 5, 5)
        filters_main_layout.setSpacing(5)

        # Create scroll area for filters
        filters_scroll = QScrollArea()
        filters_scroll.setWidgetResizable(True)
        filters_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        filters_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        filters_scroll.setFrameShape(QFrame.NoFrame)

        # Create content widget for scroll area
        filters_content = QWidget()
        filters_layout = QVBoxLayout(filters_content)
        filters_layout.setContentsMargins(10, 10, 10, 10)
        filters_layout.setSpacing(15)

        # Search
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search tasks...")
        filters_layout.addWidget(QLabel("Search:"))
        filters_layout.addWidget(self.search_edit)

        # Status filter
        self.status_combo = QComboBox()
        self.status_combo.addItems(["All Tasks", "Active", "Completed", "Overdue"])
        filters_layout.addWidget(QLabel("Status:"))
        filters_layout.addWidget(self.status_combo)

        # Priority filter
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["All Priorities", "Low", "Medium", "High", "Urgent"])
        filters_layout.addWidget(QLabel("Priority:"))
        filters_layout.addWidget(self.priority_combo)

        # Filter buttons section
        filter_buttons_layout = QHBoxLayout()
        filter_buttons_layout.setSpacing(10)

        # Reset Filters button
        self.reset_filters_btn = QPushButton("Reset")
        self.reset_filters_btn.setMinimumHeight(35)
        self.reset_filters_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #495057;
            }
        """)

        # Apply Filters button
        self.apply_filters_btn = QPushButton("Apply")
        self.apply_filters_btn.setMinimumHeight(35)
        self.apply_filters_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)

        filter_buttons_layout.addWidget(self.reset_filters_btn)
        filter_buttons_layout.addWidget(self.apply_filters_btn)

        filters_layout.addLayout(filter_buttons_layout)

        # Add stretch to push content to top
        filters_layout.addStretch()

        # Set content widget to scroll area
        filters_scroll.setWidget(filters_content)

        # Add scroll area to main filters layout
        filters_main_layout.addWidget(filters_scroll)

        layout.addWidget(filters_group)

        
        # Statistics
        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        self.total_tasks_label = QLabel("Total: 0")
        self.completed_tasks_label = QLabel("Completed: 0")
        self.pending_tasks_label = QLabel("Pending: 0")
        self.overdue_tasks_label = QLabel("Overdue: 0")
        
        stats_layout.addWidget(self.total_tasks_label)
        stats_layout.addWidget(self.completed_tasks_label)
        stats_layout.addWidget(self.pending_tasks_label)
        stats_layout.addWidget(self.overdue_tasks_label)
        
        layout.addWidget(stats_group)
        
        layout.addStretch()
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """
        Create the right task panel.
        
        Returns:
            Right panel widget
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Header
        header_layout = QHBoxLayout()
        
        tasks_label = QLabel("Tasks")
        tasks_label.setStyleSheet("font-size: 16pt; font-weight: bold; color: #000000;")
        header_layout.addWidget(tasks_label)
        
        header_layout.addStretch()
        
        # View options
        self.show_completed_checkbox = QCheckBox("Show Completed")
        self.show_completed_checkbox.setChecked(True)
        header_layout.addWidget(self.show_completed_checkbox)
        
        layout.addLayout(header_layout)
        
        # Task tree widget
        self.task_tree = TaskTreeWidget()
        layout.addWidget(self.task_tree)
        
        return panel
    
    def setup_menus(self) -> None:
        """Set up the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        logout_action = QAction("&Logout", self)
        logout_action.setShortcut("Ctrl+L")
        logout_action.triggered.connect(self.logout_requested.emit)
        file_menu.addAction(logout_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tasks menu
        tasks_menu = menubar.addMenu("&Tasks")
        
        add_task_action = QAction("&Add Task", self)
        add_task_action.setShortcut("Ctrl+N")
        add_task_action.triggered.connect(self.add_task)
        tasks_menu.addAction(add_task_action)
        
        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_tasks)
        tasks_menu.addAction(refresh_action)
    
    def setup_toolbar(self) -> None:
        """Set up the toolbar."""
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        
        # Add task
        add_action = QAction("Add Task", self)
        add_action.triggered.connect(self.add_task)
        toolbar.addAction(add_action)
        
        toolbar.addSeparator()
        
        # Refresh
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.refresh_tasks)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
    
    def setup_statusbar(self) -> None:
        """Set up the status bar."""
        self.statusBar().showMessage("Ready")
    
    def setup_styles(self) -> None:
        """Set up application styles."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #ffffff;
                color: #000000;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #000000;
            }
            
            QPushButton {
                background-color: #007bff;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #0056b3;
            }
            
            QPushButton:pressed {
                background-color: #004085;
            }
            
            QLineEdit, QComboBox {
                padding: 12px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: #ffffff;
                color: #000000;
                min-height: 20px;
            }
            
            QLineEdit:focus, QComboBox:focus {
                border-color: #007bff;
            }
            
            QLabel {
                color: #000000;
            }
            
            QCheckBox {
                color: #000000;
            }
            
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            
            QScrollArea > QWidget > QWidget {
                background-color: #ffffff;
            }
            
            QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #dee2e6;
                border-radius: 6px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #ced4da;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                background-color: #ffffff;
                border-radius: 8px;
            }
            
            QTabBar::tab {
                background-color: #e9ecef;
                color: #000000;
                padding: 12px 24px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 500;
            }
            
            QTabBar::tab:selected {
                background-color: #ffffff;
                color: #000000;
                border-bottom: 2px solid #007bff;
            }
            
            QTabBar::tab:hover:!selected {
                background-color: #f8f9fa;
            }
            
            QMenuBar {
                background-color: #ffffff;
                color: #000000;
                border-bottom: 1px solid #dee2e6;
            }
            
            QMenuBar::item {
                background-color: transparent;
                color: #000000;
                padding: 4px 8px;
            }
            
            QMenuBar::item:selected {
                background-color: #e9ecef;
                color: #000000;
            }
            
            QMenu {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #dee2e6;
            }
            
            QMenu::item {
                background-color: transparent;
                color: #000000;
                padding: 4px 20px;
            }
            
            QMenu::item:selected {
                background-color: #e9ecef;
                color: #000000;
            }
            
            QToolBar {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                color: #000000;
            }
            
            QToolBar QToolButton {
                background-color: transparent;
                color: #000000;
                border: none;
                padding: 4px 8px;
            }
            
            QToolBar QToolButton:hover {
                background-color: #e9ecef;
                color: #000000;
            }
            
            QToolBar QToolButton:pressed {
                background-color: #dee2e6;
                color: #000000;
            }
            
            QAction {
                color: #000000;
            }
            
             QMessageBox {
            background-color: #ffffff;
            color: #000000;
        }
        
        QMessageBox QLabel {
            background-color: #ffffff;
            color: #000000;
            font-size: 11pt;
        }
        
        QMessageBox QPushButton {
            background-color: #007bff;
            color: #ffffff;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: bold;
            min-width: 80px;
        }
        
        QMessageBox QPushButton:hover {
            background-color: #0056b3;
        }
        
        QMessageBox QPushButton:pressed {
            background-color: #004085;
        }
        
        QMessageBox QPushButton:default {
            background-color: #28a745;
        }
        
        QMessageBox QPushButton:default:hover {
            background-color: #1e7e34;
        }
        
        QDialog {
            background-color: #ffffff;
            color: #000000;
        }
        
        QDialog QLabel {
            color: #000000;
        }
        
        QDialog QPushButton {
            background-color: #007bff;
            color: #ffffff;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: bold;
            min-width: 80px;
        }
                           
         QLineEdit, QComboBox {
            padding: 12px;
            border: 1px solid #ced4da;
            border-radius: 4px;
            background-color: #ffffff;
            color: #000000;
            min-height: 20px;
        }
        
        QTextEdit {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #ced4da;
            border-radius: 4px;
            padding: 8px;
            font-size: 11pt;
            selection-background-color: #007bff;
            selection-color: #ffffff;
        }
        
        QTextEdit:focus {
            border-color: #007bff;
            outline: none;
        }
        
        QDateEdit {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #ced4da;
            border-radius: 4px;
            padding: 8px 12px;
            font-size: 11pt;
            min-height: 20px;
        }
        
        QDateEdit:focus {
            border-color: #007bff;
            outline: none;
        }
        
        QDateEdit::drop-down {
            background-color: #ffffff;
            border: none;
            width: 20px;
        }
        
        QDateEdit::down-arrow {
            image: none;
            border: 1px solid #ced4da;
            background-color: #f8f9fa;
            width: 12px;
            height: 12px;
        }
        
        QDateEdit QAbstractItemView {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #ced4da;
            selection-background-color: #007bff;
            selection-color: #ffffff;
        }
        
        QCalendarWidget {
            background-color: #ffffff;
            color: #000000;
        }
        
        QCalendarWidget QWidget {
            background-color: #ffffff;
            color: #000000;
        }
        
        QCalendarWidget QTableView {
            background-color: #ffffff;
            color: #000000;
            selection-background-color: #007bff;
            selection-color: #ffffff;
        }
        """)




    
    def connect_signals(self) -> None:
        """Connect widget signals to slots with logging."""
        # Left panel actions
        self.add_task_btn.clicked.connect(self.add_task)
        
        # Filter buttons
        self.reset_filters_btn.clicked.connect(self.reset_filters)
        self.apply_filters_btn.clicked.connect(self.apply_filters)
        
        self.show_completed_checkbox.toggled.connect(self.apply_filters)
        
        # Task tree
        self.task_tree.task_completed.connect(self.mark_task_completed)
        self.task_tree.task_edited.connect(self.edit_task)
        self.task_tree.task_deleted.connect(self.delete_task)
        self.task_tree.subtask_requested.connect(self.add_subtask)

    
    def load_data(self) -> None:
        """Load initial data."""
        self.refresh_tasks()
    
    def refresh_tasks(self) -> None:
        """Refresh task list from database."""
        try:
            self.current_tasks = self.task_manager.get_user_tasks(
                self.user.user_id, 
                include_completed=True
            )
            self.apply_filters()
            self.update_statistics()
            self.statusBar().showMessage(f"Loaded {len(self.current_tasks)} tasks")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load tasks: {str(e)}")
    
    def apply_filters(self) -> None:
        """Apply current filters to task list."""
        filtered_tasks = self.current_tasks[:]
        
        # Search filter
        search_text = self.search_edit.text().strip().lower()
        if search_text:
            filtered_tasks = [
                task for task in filtered_tasks
                if (search_text in task.title.lower() or 
                    search_text in task.description.lower())
            ]
        
        # Status filter
        status_filter = self.status_combo.currentText()
        if status_filter == "Active":
            filtered_tasks = [task for task in filtered_tasks if not task.completed]
        elif status_filter == "Completed":
            filtered_tasks = [task for task in filtered_tasks if task.completed]
        elif status_filter == "Overdue":
            filtered_tasks = [task for task in filtered_tasks if task.is_overdue()]
        
        # Priority filter
        priority_filter = self.priority_combo.currentText()
        if priority_filter != "All Priorities":
            priority_map = {
                "Low": Priority.LOW,
                "Medium": Priority.MEDIUM,
                "High": Priority.HIGH,
                "Urgent": Priority.URGENT
            }
            filtered_tasks = [
                task for task in filtered_tasks
                if task.priority == priority_map[priority_filter]
            ]
        
        # Show completed filter
        if not self.show_completed_checkbox.isChecked():
            filtered_tasks = [task for task in filtered_tasks if not task.completed]
        
        self.filtered_tasks = filtered_tasks
        self.task_tree.update_tasks(self.filtered_tasks)

        # Add status update
        self.statusBar().showMessage(f"Showing {len(self.filtered_tasks)} of {len(self.current_tasks)} tasks")

    def update_statistics(self) -> None:
        """Update task statistics."""
        total = len(self.current_tasks)
        completed = len([task for task in self.current_tasks if task.completed])
        pending = total - completed
        overdue = len([task for task in self.current_tasks if task.is_overdue()])
        
        self.total_tasks_label.setText(f"Total: {total}")
        self.completed_tasks_label.setText(f"Completed: {completed}")
        self.pending_tasks_label.setText(f"Pending: {pending}")
        self.overdue_tasks_label.setText(f"Overdue: {overdue}")
    
    def add_task(self) -> None:
        """Add a new task."""
        dialog = AddTaskDialog(self)
        if dialog.exec() == QDialog.Accepted:
            task_data = dialog.get_task_data()
            
            if not task_data['title']:
                QMessageBox.warning(self, "Warning", "Task title cannot be empty")
                return
            
            try:
                task = self.task_manager.create_task(
                    title=task_data['title'],
                    description=task_data['description'],
                    user_id=self.user.user_id
                )
                
                task.priority = task_data['priority']
                task.due_date = task_data['due_date']
                
                self.task_manager.update_task(task)
                self.refresh_tasks()
                
                self.statusBar().showMessage("Task added successfully")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add task: {str(e)}")
    
    def add_subtask(self, parent_task: Task) -> None:
        """
        Add a subtask to a parent task.
        
        Args:
            parent_task: Parent task
        """
        dialog = AddTaskDialog(self, parent_task)
        if dialog.exec() == QDialog.Accepted:
            task_data = dialog.get_task_data()
            
            if not task_data['title']:
                QMessageBox.warning(self, "Warning", "Task title cannot be empty")
                return
            
            try:
                task = self.task_manager.create_task(
                    title=task_data['title'],
                    description=task_data['description'],
                    user_id=self.user.user_id,
                    parent_id=parent_task.task_id
                )
                
                task.priority = task_data['priority']
                task.due_date = task_data['due_date']
                
                self.task_manager.update_task(task)
                self.refresh_tasks()
                
                self.statusBar().showMessage("Subtask added successfully")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add subtask: {str(e)}")
    
    def mark_task_completed(self, task: Task, completed: bool) -> None:
        """
        Mark task as completed or uncompleted.
        
        Args:
            task: Task to update
            completed: Whether to mark as completed
        """
        try:
            task.mark_completed(completed)
            self.task_manager.update_task(task)
            self.refresh_tasks()
            
            status = "completed" if completed else "uncompleted"
            self.statusBar().showMessage(f"Task marked as {status}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update task: {str(e)}")
    
    def edit_task(self, task: Task) -> None:
        """
        Edit an existing task.
        
        Args:
            task: Task to edit
        """
        dialog = AddTaskDialog(self)
        
        # Pre-fill dialog with current task data
        dialog.title_edit.setText(task.title)
        dialog.description_edit.setPlainText(task.description)
        
        priority_map = {
            Priority.LOW: "Low",
            Priority.MEDIUM: "Medium", 
            Priority.HIGH: "High",
            Priority.URGENT: "Urgent"
        }
        dialog.priority_combo.setCurrentText(priority_map[task.priority])
        
        if task.due_date:
            dialog.due_date_checkbox.setChecked(True)
            qdate = QDate(task.due_date.year, task.due_date.month, task.due_date.day)
            dialog.due_date_edit.setDate(qdate)
        
        dialog.setWindowTitle("Edit Task")
        
        if dialog.exec() == QDialog.Accepted:
            task_data = dialog.get_task_data()
            
            if not task_data['title']:
                QMessageBox.warning(self, "Warning", "Task title cannot be empty")
                return
            
            try:
                task.title = task_data['title']
                task.description = task_data['description']
                task.priority = task_data['priority']
                task.due_date = task_data['due_date']
                
                self.task_manager.update_task(task)
                self.refresh_tasks()
                
                self.statusBar().showMessage("Task updated successfully")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update task: {str(e)}")
    
    def delete_task(self, task: Task) -> None:
        """
        Delete a task.
        
        Args:
            task: Task to delete
        """
        reply = QMessageBox.question(
            self, 
            "Confirm Delete",
            f"Are you sure you want to delete '{task.title}'?\n",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if task.task_id:
                    self.task_manager.delete_task(task.task_id)
                    self.refresh_tasks()
                    self.statusBar().showMessage("Task deleted successfully")
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete task: {str(e)}")
    
   
    def closeEvent(self, event) -> None:
        """Handle window close event."""
        self.refresh_timer.stop()
        event.accept()

    def reset_filters(self) -> None:
        """Reset all filters to default values."""
        try:
            # Reset all filter controls to default
            self.search_edit.clear()
            self.status_combo.setCurrentIndex(0)  # "All Tasks"
            self.priority_combo.setCurrentIndex(0)  # "All Priorities"
            self.show_completed_checkbox.setChecked(True)
            
            # Apply the reset filters
            self.apply_filters()
            
            self.statusBar().showMessage("Filters reset")
            
        except Exception as e:
            self.statusBar().showMessage(f"Failed to reset filters: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to reset filters: {str(e)}")
