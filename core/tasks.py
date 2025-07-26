"""
Task management module.

This module contains classes for managing tasks, tags, and task hierarchies.
"""

from typing import List, Optional, Dict, Any, Set
from datetime import datetime
from enum import Enum


class Priority(Enum):
    """Task priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

class Task:
    """Represents a single task with all its properties."""
    
    def __init__(
        self,
        title: str,
        description: str = "",
        task_id: Optional[int] = None,
        parent_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> None:
        """
        Initialize a task.
        
        Args:
            title: Task title
            description: Task description
            task_id: Unique task identifier
            parent_id: ID of parent task for hierarchy
            user_id: ID of the task owner
        """
        self.task_id: Optional[int] = task_id
        self.title: str = title
        self.description: str = description
        self.completed: bool = False
        self.parent_id: Optional[int] = parent_id
        self.user_id: Optional[int] = user_id
        self.priority: Priority = Priority.MEDIUM
        self.due_date: Optional[datetime] = None
        self.created_at: datetime = datetime.now()
        self.updated_at: datetime = datetime.now()
        self.completed_at: Optional[datetime] = None
        self.additional_properties: Dict[str, Any] = {}
        
        # Hierarchy management
        self.children: List['Task'] = []
        self.parent: Optional['Task'] = None
    
    
    def mark_completed(self, completed: bool = True) -> None:
        """
        Mark task as completed or uncompleted.
        
        Args:
            completed: Whether to mark as completed
        """
        self.completed = completed
        self.completed_at = datetime.now() if completed else None
        self.updated_at = datetime.now()
        
        # If marking as completed, also complete all children
        if completed:
            for child in self.children:
                child.mark_completed(True)
    
    def add_child(self, child_task: 'Task') -> None:
        """
        Add a child task.
        
        Args:
            child_task: Child task to add
        """
        if child_task not in self.children:
            self.children.append(child_task)
            child_task.parent = self
            child_task.parent_id = self.task_id
            self.updated_at = datetime.now()
    
    def remove_child(self, child_task: 'Task') -> None:
        """
        Remove a child task.
        
        Args:
            child_task: Child task to remove
        """
        if child_task in self.children:
            self.children.remove(child_task)
            child_task.parent = None
            child_task.parent_id = None
            self.updated_at = datetime.now()
    
    def set_property(self, key: str, value: Any) -> None:
        """
        Set an additional property.
        
        Args:
            key: Property key
            value: Property value
        """
        self.additional_properties[key] = value
        self.updated_at = datetime.now()
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """
        Get an additional property.
        
        Args:
            key: Property key
            default: Default value if key not found
            
        Returns:
            Property value or default
        """
        return self.additional_properties.get(key, default)
    
    def is_overdue(self) -> bool:
        """
        Check if task is overdue.
        
        Returns:
            True if task is overdue, False otherwise
        """
        if self.due_date is None or self.completed:
            return False
        return datetime.now() > self.due_date
    
    def get_completion_percentage(self) -> float:
        """
        Get completion percentage including children.
        
        Returns:
            Completion percentage (0.0 to 1.0)
        """
        if not self.children:
            return 1.0 if self.completed else 0.0
        
        if self.completed:
            return 1.0
        
        completed_children = sum(1 for child in self.children if child.completed)
        return completed_children / len(self.children)
    
    def __str__(self) -> str:
        """Return string representation of the task."""
        return f"Task({self.title}, completed={self.completed})"
    
    def __repr__(self) -> str:
        """Return detailed string representation of the task."""
        return (f"Task(id={self.task_id}, title='{self.title}', "
                f"completed={self.completed}, children={len(self.children)})")


class TaskManager:
    """Manages tasks and provides CRUD operations."""
    
    def __init__(self, db_handler) -> None:
        """
        Initialize task manager.
        
        Args:
            db_handler: Database handler instance
        """
        self.db_handler = db_handler
        self._tasks_cache: Dict[int, Task] = {}
        
    def create_task(
        self,
        title: str,
        description: str = "",
        user_id: Optional[int] = None,
        parent_id: Optional[int] = None
    ) -> Task:
        """
        Create a new task.
        
        Args:
            title: Task title
            description: Task description
            user_id: Owner user ID
            parent_id: Parent task ID
            
        Returns:
            Created task
            
        Raises:
            ValueError: If title is empty
        """
        if not title.strip():
            raise ValueError("Task title cannot be empty")
        
        task = Task(title.strip(), description.strip(), user_id=user_id, parent_id=parent_id)
        task_id = self.db_handler.save_task(task)
        task.task_id = task_id
        
        # Cache the task
        self._tasks_cache[task_id] = task
        
        # Handle parent-child relationship
        if parent_id:
            parent_task = self.get_task(parent_id)
            if parent_task:
                parent_task.add_child(task)
        
        return task
    
    def get_task(self, task_id: int) -> Optional[Task]:
        """
        Get a task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task if found, None otherwise
        """
        # Try cache first
        if task_id in self._tasks_cache:
            return self._tasks_cache[task_id]
        
        # Load from database
        task = self.db_handler.load_task(task_id)
        if task:
            self._tasks_cache[task_id] = task
        
        return task
    
    def get_user_tasks(self, user_id: int, include_completed: bool = True) -> List[Task]:
        """
        Get all tasks for a user.
        
        Args:
            user_id: User ID
            include_completed: Whether to include completed tasks
            
        Returns:
            List of user tasks
        """
        tasks = self.db_handler.load_user_tasks(user_id, include_completed)
        
        # Update cache
        for task in tasks:
            if task.task_id:
                self._tasks_cache[task.task_id] = task
        
        # Build hierarchy
        self._build_task_hierarchy(tasks)
        
        return tasks
    
    def update_task(self, task: Task) -> bool:
        """
        Update an existing task.
        
        Args:
            task: Task to update
            
        Returns:
            True if successful, False otherwise
        """
        task.updated_at = datetime.now()
        success = self.db_handler.update_task(task)
        
        if success and task.task_id:
            self._tasks_cache[task.task_id] = task
        
        return success
    
    def delete_task(self, task_id: int) -> bool:
        """
        Delete a task and all its children.
        
        Args:
            task_id: Task ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        task = self.get_task(task_id)
        if not task:
            return False
        
        # Delete all children first
        for child in task.children[:]:  # Copy list to avoid modification during iteration
            if child.task_id:
                self.delete_task(child.task_id)
        
        # Remove from parent
        if task.parent:
            task.parent.remove_child(task)
        
        # Delete from database
        success = self.db_handler.delete_task(task_id)
        
        if success:
            # Remove from cache
            self._tasks_cache.pop(task_id, None)
        
        return success
    
    def search_tasks(self, user_id: int, query: str) -> List[Task]:
        """
        Search tasks by title, description, or tags.
        
        Args:
            user_id: User ID
            query: Search query
            search_tags: Whether to search in tags
            
        Returns:
            List of matching tasks
        """
        if not query.strip():
            return []
        
        user_tasks = self.get_user_tasks(user_id)
        query_lower = query.lower()
        matching_tasks = []
        
        for task in user_tasks:
            # Search in title and description
            if (query_lower in task.title.lower() or 
                query_lower in task.description.lower()):
                matching_tasks.append(task)
                continue
            
        
        return matching_tasks
    
    def get_overdue_tasks(self, user_id: int) -> List[Task]:
        """
        Get overdue tasks for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of overdue tasks
        """
        user_tasks = self.get_user_tasks(user_id, include_completed=False)
        return [task for task in user_tasks if task.is_overdue()]
    
    def _build_task_hierarchy(self, tasks: List[Task]) -> None:
        """
        Build parent-child relationships from flat task list.
        
        Args:
            tasks: List of tasks to build hierarchy for
        """
        task_dict = {task.task_id: task for task in tasks if task.task_id}
        
        for task in tasks:
            if task.parent_id and task.parent_id in task_dict:
                parent = task_dict[task.parent_id]
                parent.add_child(task)
