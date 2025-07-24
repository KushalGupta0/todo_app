"""
Custom GUI widgets for the To-Do List application.

This module contains custom PySide6 widgets for displaying tasks, tags, and hierarchies.
"""

from typing import List, Optional, Set
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QCheckBox, QTreeWidget, QTreeWidgetItem, QFrame, 
    QMenu, QSizePolicy, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPalette, QColor, QAction, QCursor

from core.tasks import Task, Tag, Priority


class TaskWidget(QWidget):
    """Widget for displaying a single task with interactive elements."""
    
    # Signals
    completed_changed = Signal(bool)
    edit_requested = Signal()
    delete_requested = Signal()
    
    def __init__(self, task: Task, parent=None) -> None:
        """
        Initialize task widget.
        
        Args:
            task: Task to display
            parent: Parent widget
        """
        super().__init__(parent)
        self.task = task
        self.setup_ui()
        self.update_display()
    
    def setup_ui(self) -> None:
        """Set up the widget UI."""
        self.setMaximumHeight(80)
        self.setStyleSheet("""
            TaskWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin: 2px;
            }
            
            TaskWidget:hover {
                border-color: #007bff;
                background-color: #f8f9ff;
            }
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(4)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)
        
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # Completion checkbox
        self.completed_checkbox = QCheckBox()
        self.completed_checkbox.setChecked(self.task.completed)
        self.completed_checkbox.toggled.connect(self.completed_changed.emit)
        layout.addWidget(self.completed_checkbox)
        
        # Task content
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)
        
        # Title
        self.title_label = QLabel(self.task.title)
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        content_layout.addWidget(self.title_label)
        
        # Description (if exists)
        if self.task.description:
            self.description_label = QLabel(self.task.description)
            self.description_label.setStyleSheet("color: #6c757d; font-size: 9pt;")
            self.description_label.setWordWrap(True)
            content_layout.addWidget(self.description_label)
        
        layout.addLayout(content_layout)
        
        # Priority indicator
        self.priority_label = QLabel()
        self.priority_label.setFixedSize(12, 12)
        self.priority_label.setStyleSheet("border-radius: 6px;")
        layout.addWidget(self.priority_label)
        
        # Tags area
        self.tags_layout = QHBoxLayout()
        self.tags_layout.setSpacing(4)
        layout.addLayout(self.tags_layout)
        
        layout.addStretch()
        
        # Action buttons (initially hidden)
        self.edit_button = QPushButton("Edit")
        self.edit_button.setFixedSize(50, 24)
        self.edit_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #1e7e34;
            }
        """)
        self.edit_button.clicked.connect(self.edit_requested.emit)
        self.edit_button.hide()
        layout.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("Del")
        self.delete_button.setFixedSize(40, 24)
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        self.delete_button.clicked.connect(self.delete_requested.emit)
        self.delete_button.hide()
        layout.addWidget(self.delete_button)
    
    def update_display(self) -> None:
        """Update widget display based on task state."""
        # Update completion style
        if self.task.completed:
            self.title_label.setStyleSheet("""
                text-decoration: line-through;
                color: #6c757d;
                font-weight: normal;
            """)
            if hasattr(self, 'description_label'):
                self.description_label.setStyleSheet("""
                    text-decoration: line-through;
                    color: #adb5bd;
                    font-size: 9pt;
                """)
        else:
            self.title_label.setStyleSheet("color: #212529; font-weight: bold;")
            if hasattr(self, 'description_label'):
                self.description_label.setStyleSheet("color: #6c757d; font-size: 9pt;")
        
        # Update priority indicator
        priority_colors = {
            Priority.LOW: "#28a745",
            Priority.MEDIUM: "#ffc107", 
            Priority.HIGH: "#fd7e14",
            Priority.URGENT: "#dc3545"
        }
        color = priority_colors.get(self.task.priority, "#6c757d")
        self.priority_label.setStyleSheet(f"background-color: {color}; border-radius: 6px;")
        
        # Update tags
        self.update_tags()
        
        # Update checkbox
        self.completed_checkbox.setChecked(self.task.completed)
    
    def update_tags(self) -> None:
        """Update tags display."""
        # Clear existing tag widgets
        while self.tags_layout.count():
            child = self.tags_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Add tag widgets
        for tag in list(self.task.tags)[:3]:  # Show max 3 tags
            tag_widget = TagWidget(tag)
            self.tags_layout.addWidget(tag_widget)
        
        # Add "more" indicator if there are more tags
        if len(self.task.tags) > 3:
            more_label = QLabel(f"+{len(self.task.tags) - 3}")
            more_label.setStyleSheet("""
                background-color: #e9ecef;
                color: #495057;
                padding: 2px 6px;
                border-radius: 10px;
                font-size: 8pt;
            """)
            self.tags_layout.addWidget(more_label)
    
    def enterEvent(self, event) -> None:
        """Show action buttons on mouse enter."""
        self.edit_button.show()
        self.delete_button.show()
        super().enterEvent(event)
    
    def leaveEvent(self, event) -> None:
        """Hide action buttons on mouse leave."""
        self.edit_button.hide()
        self.delete_button.hide()
        super().leaveEvent(event)


class TagWidget(QWidget):
    """Widget for displaying a single tag."""
    
    def __init__(self, tag: Tag, parent=None) -> None:
        """
        Initialize tag widget.
        
        Args:
            tag: Tag to display
            parent: Parent widget
        """
        super().__init__(parent)
        self.tag = tag
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Set up the widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(0)
        
        # Tag label
        label = QLabel(self.tag.name)
        label.setStyleSheet(f"""
            background-color: {self.tag.color};
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 8pt;
            font-weight: 500;
        """)
        
        layout.addWidget(label)
        
        # Set fixed size
        self.setFixedHeight(20)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)


class TaskTreeWidget(QTreeWidget):
    """Tree widget for displaying tasks in hierarchical structure."""
    
    # Signals
    task_completed = Signal(Task, bool)
    task_edited = Signal(Task)
    task_deleted = Signal(Task)
    subtask_requested = Signal(Task)
    
    def __init__(self, parent=None) -> None:
        """
        Initialize task tree widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.task_items: dict = {}  # Maps task_id to QTreeWidgetItem
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Set up the tree widget."""
        # Configure tree
        self.setHeaderHidden(True)
        self.setRootIsDecorated(True)
        self.setAlternatingRowColors(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
        # Set style
        self.setStyleSheet("""
            QTreeWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                selection-background-color: #e3f2fd;
            }
            
            QTreeWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f8f9fa;
            }
            
            QTreeWidget::item:hover {
                background-color: #f8f9ff;
            }
            
            QTreeWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
        """)
    
    def update_tasks(self, tasks: List[Task]) -> None:
        """
        Update the tree with new task list.
        
        Args:
            tasks: List of tasks to display
        """
        self.clear()
        self.task_items.clear()
        
        # Separate root tasks from child tasks
        root_tasks = [task for task in tasks if not task.parent_id]
        child_tasks = [task for task in tasks if task.parent_id]
        
        # Add root tasks first
        for task in root_tasks:
            self.add_task_item(task)
        
        # Add child tasks
        for task in child_tasks:
            self.add_task_item(task)
        
        # Expand all items
        self.expandAll()
    
    def add_task_item(self, task: Task) -> QTreeWidgetItem:
        """
        Add a task item to the tree.
        
        Args:
            task: Task to add
            
        Returns:
            Created tree widget item
        """
        # Find parent item
        parent_item = None
        if task.parent_id and task.parent_id in self.task_items:
            parent_item = self.task_items[task.parent_id]
        
        # Create item
        if parent_item:
            item = QTreeWidgetItem(parent_item)
        else:
            item = QTreeWidgetItem(self)
        
        # Store task reference
        item.setData(0, Qt.UserRole, task)
        if task.task_id:
            self.task_items[task.task_id] = item
        
        # Create and set task widget
        task_widget = TaskWidget(task)
        task_widget.completed_changed.connect(
            lambda completed, t=task: self.task_completed.emit(t, completed)
        )
        task_widget.edit_requested.connect(
            lambda t=task: self.task_edited.emit(t)
        )
        task_widget.delete_requested.connect(
            lambda t=task: self.task_deleted.emit(t)
        )
        
        self.setItemWidget(item, 0, task_widget)
        
        return item
    
    def show_context_menu(self, position) -> None:
        """
        Show context menu for tree items.
        
        Args:
            position: Mouse position
        """
        item = self.itemAt(position)
        if not item:
            return
        
        task = item.data(0, Qt.UserRole)
        if not task:
            return
        
        menu = QMenu(self)
        
        # Edit action
        edit_action = QAction("Edit Task", self)
        edit_action.triggered.connect(lambda: self.task_edited.emit(task))
        menu.addAction(edit_action)
        
        # Add subtask action
        subtask_action = QAction("Add Subtask", self)
        subtask_action.triggered.connect(lambda: self.subtask_requested.emit(task))
        menu.addAction(subtask_action)
        
        menu.addSeparator()
        
        # Complete/Uncomplete action
        if task.completed:
            complete_action = QAction("Mark as Pending", self)
            complete_action.triggered.connect(lambda: self.task_completed.emit(task, False))
        else:
            complete_action = QAction("Mark as Completed", self)
            complete_action.triggered.connect(lambda: self.task_completed.emit(task, True))
        menu.addAction(complete_action)
        
        menu.addSeparator()
        
        # Delete action
        delete_action = QAction("Delete Task", self)
        delete_action.triggered.connect(lambda: self.task_deleted.emit(task))
        menu.addAction(delete_action)
        
        # Show menu
        menu.exec(self.mapToGlobal(position))
    
    def get_selected_task(self) -> Optional[Task]:
        """
        Get currently selected task.
        
        Returns:
            Selected task or None
        """
        current_item = self.currentItem()
        if current_item:
            return current_item.data(0, Qt.UserRole)
        return None


class StatsWidget(QWidget):
    """Widget for displaying task statistics."""
    
    def __init__(self, parent=None) -> None:
        """
        Initialize stats widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self) -> None:
        """Set up the widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(20)
        
        # Total tasks
        self.total_frame = self.create_stat_frame("Total", "0", "#007bff")
        layout.addWidget(self.total_frame)
        
        # Completed tasks
        self.completed_frame = self.create_stat_frame("Completed", "0", "#28a745")
        layout.addWidget(self.completed_frame)
        
        # Pending tasks
        self.pending_frame = self.create_stat_frame("Pending", "0", "#ffc107")
        layout.addWidget(self.pending_frame)
        
        # Overdue tasks
        self.overdue_frame = self.create_stat_frame("Overdue", "0", "#dc3545")
        layout.addWidget(self.overdue_frame)
        
        layout.addStretch()
    
    def create_stat_frame(self, title: str, value: str, color: str) -> QFrame:
        """
        Create a statistics frame.
        
        Args:
            title: Stat title
            value: Stat value
            color: Color for the frame
            
        Returns:
            Created frame widget
        """
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-left: 4px solid {color};
                border-radius: 4px;
                padding: 8px;
            }}
        """)
        
        layout = QVBoxLayout(frame)
        layout.setSpacing(4)
        
        # Value label
        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 18pt; font-weight: bold;")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)
        
        # Title label
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #6c757d; font-size: 10pt;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Store labels for updates
        setattr(self, f"{title.lower()}_value_label", value_label)
        
        return frame
    
    def update_stats(self, total: int, completed: int, pending: int, overdue: int) -> None:
        """
        Update statistics display.
        
        Args:
            total: Total tasks count
            completed: Completed tasks count
            pending: Pending tasks count
            overdue: Overdue tasks count
        """
        self.total_value_label.setText(str(total))
        self.completed_value_label.setText(str(completed))
        self.pending_value_label.setText(str(pending))
        self.overdue_value_label.setText(str(overdue))
