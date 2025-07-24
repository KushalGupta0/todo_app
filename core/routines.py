"""
Routines management module.

This module handles repetitive tasks and routine management.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, time
from enum import Enum

from .tasks import Task, TaskManager


class RepeatType(Enum):
    """Types of routine repetition."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    WEEKDAYS = "weekdays"
    WEEKENDS = "weekends"
    CUSTOM = "custom"


class Routine:
    """Represents a routine that generates tasks automatically."""
    
    def __init__(
        self,
        name: str,
        description: str = "",
        routine_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> None:
        """
        Initialize a routine.
        
        Args:
            name: Routine name
            description: Routine description
            routine_id: Unique routine identifier
            user_id: Owner user ID
        """
        self.routine_id: Optional[int] = routine_id
        self.name: str = name
        self.description: str = description
        self.user_id: Optional[int] = user_id
        self.repeat_type: RepeatType = RepeatType.DAILY
        self.is_active: bool = True
        self.created_at: datetime = datetime.now()
        self.last_generated: Optional[datetime] = None
        self.start_date: datetime = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.end_date: Optional[datetime] = None
        self.preferred_time: Optional[time] = None
        self.task_templates: List[Dict[str, Any]] = []
        
        # Custom repeat settings
        self.custom_days: List[int] = []  # 0=Monday, 6=Sunday
        self.repeat_interval: int = 1  # Every N days/weeks/months
    
    def add_task_template(self, title: str, description: str = "", **kwargs) -> None:
        """
        Add a task template to the routine.
        
        Args:
            title: Task title template
            description: Task description template
            **kwargs: Additional task properties
        """
        template = {
            'title': title,
            'description': description,
            **kwargs
        }
        self.task_templates.append(template)
    
    def remove_task_template(self, title: str) -> bool:
        """
        Remove a task template from the routine.
        
        Args:
            title: Title of template to remove
            
        Returns:
            True if removed, False if not found
        """
        for i, template in enumerate(self.task_templates):
            if template['title'] == title:
                del self.task_templates[i]
                return True
        return False
    
    def should_generate_today(self, target_date: Optional[datetime] = None) -> bool:
        """
        Check if routine should generate tasks for the given date.
        
        Args:
            target_date: Date to check (default: today)
            
        Returns:
            True if should generate, False otherwise
        """
        if not self.is_active:
            return False
        
        if target_date is None:
            target_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Check if within date range
        if target_date < self.start_date:
            return False
        
        if self.end_date and target_date > self.end_date:
            return False
        
        # Check if already generated today
        if (self.last_generated and 
            self.last_generated.date() == target_date.date()):
            return False
        
        # Check repeat pattern
        return self._matches_repeat_pattern(target_date)
    
    def _matches_repeat_pattern(self, target_date: datetime) -> bool:
        """
        Check if target date matches the routine's repeat pattern.
        
        Args:
            target_date: Date to check
            
        Returns:
            True if matches pattern, False otherwise
        """
        weekday = target_date.weekday()  # 0=Monday, 6=Sunday
        
        if self.repeat_type == RepeatType.DAILY:
            days_since_start = (target_date.date() - self.start_date.date()).days
            return days_since_start % self.repeat_interval == 0
        
        elif self.repeat_type == RepeatType.WEEKLY:
            weeks_since_start = (target_date.date() - self.start_date.date()).days // 7
            return (weeks_since_start % self.repeat_interval == 0 and
                    weekday == self.start_date.weekday())
        
        elif self.repeat_type == RepeatType.MONTHLY:
            return (target_date.day == self.start_date.day and
                    (target_date.year - self.start_date.year) * 12 + 
                    target_date.month - self.start_date.month) % self.repeat_interval == 0
        
        elif self.repeat_type == RepeatType.WEEKDAYS:
            return weekday < 5  # Monday to Friday
        
        elif self.repeat_type == RepeatType.WEEKENDS:
            return weekday >= 5  # Saturday and Sunday
        
        elif self.repeat_type == RepeatType.CUSTOM:
            return weekday in self.custom_days
        
        return False
    
    def generate_tasks(self, task_manager: TaskManager, target_date: Optional[datetime] = None) -> List[Task]:
        """
        Generate tasks for this routine.
        
        Args:
            task_manager: TaskManager instance
            target_date: Date to generate for (default: today)
            
        Returns:
            List of generated tasks
        """
        if not self.should_generate_today(target_date):
            return []
        
        if target_date is None:
            target_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        generated_tasks = []
        parent_task = None
        
        # Create parent task if multiple templates
        if len(self.task_templates) > 1:
            parent_title = f"{self.name} - {target_date.strftime('%Y-%m-%d')}"
            parent_task = task_manager.create_task(
                title=parent_title,
                description=self.description,
                user_id=self.user_id
            )
            generated_tasks.append(parent_task)
        
        # Create tasks from templates
        for template in self.task_templates:
            title = template['title']
            if len(self.task_templates) == 1:
                title = f"{title} - {target_date.strftime('%Y-%m-%d')}"
            
            task = task_manager.create_task(
                title=title,
                description=template.get('description', ''),
                user_id=self.user_id,
                parent_id=parent_task.task_id if parent_task else None
            )
            
            # Set due date if preferred time is specified
            if self.preferred_time:
                due_datetime = datetime.combine(target_date.date(), self.preferred_time)
                task.due_date = due_datetime
                task_manager.update_task(task)
            
            generated_tasks.append(task)
        
        # Update last generated timestamp
        self.last_generated = datetime.now()
        
        return generated_tasks
    
    def __str__(self) -> str:
        """Return string representation of the routine."""
        return f"Routine({self.name}, {self.repeat_type.value})"
    
    def __repr__(self) -> str:
        """Return detailed string representation of the routine."""
        return (f"Routine(id={self.routine_id}, name='{self.name}', "
                f"repeat_type={self.repeat_type.value}, active={self.is_active})")


class RoutineManager:
    """Manages routines and automatic task generation."""
    
    def __init__(self, db_handler, task_manager: TaskManager) -> None:
        """
        Initialize routine manager.
        
        Args:
            db_handler: Database handler instance
            task_manager: TaskManager instance
        """
        self.db_handler = db_handler
        self.task_manager = task_manager
    
    def create_routine(
        self,
        name: str,
        description: str = "",
        user_id: Optional[int] = None,
        repeat_type: RepeatType = RepeatType.DAILY
    ) -> Routine:
        """
        Create a new routine.
        
        Args:
            name: Routine name
            description: Routine description
            user_id: Owner user ID
            repeat_type: How often the routine repeats
            
        Returns:
            Created routine
            
        Raises:
            ValueError: If name is empty
        """
        if not name.strip():
            raise ValueError("Routine name cannot be empty")
        
        routine = Routine(name.strip(), description.strip(), user_id=user_id)
        routine.repeat_type = repeat_type
        
        routine_id = self.db_handler.save_routine(routine)
        routine.routine_id = routine_id
        
        return routine
    
    def get_routine(self, routine_id: int) -> Optional[Routine]:
        """
        Get a routine by ID.
        
        Args:
            routine_id: Routine ID
            
        Returns:
            Routine if found, None otherwise
        """
        return self.db_handler.load_routine(routine_id)
    
    def get_user_routines(self, user_id: int, active_only: bool = True) -> List[Routine]:
        """
        Get all routines for a user.
        
        Args:
            user_id: User ID
            active_only: Whether to include only active routines
            
        Returns:
            List of user routines
        """
        return self.db_handler.load_user_routines(user_id, active_only)
    
    def update_routine(self, routine: Routine) -> bool:
        """
        Update an existing routine.
        
        Args:
            routine: Routine to update
            
        Returns:
            True if successful, False otherwise
        """
        return self.db_handler.update_routine(routine)
    
    def delete_routine(self, routine_id: int) -> bool:
        """
        Delete a routine.
        
        Args:
            routine_id: Routine ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        return self.db_handler.delete_routine(routine_id)
    
    def generate_routine_tasks(self, user_id: int, target_date: Optional[datetime] = None) -> List[Task]:
        """
        Generate tasks for all active routines of a user.
        
        Args:
            user_id: User ID
            target_date: Date to generate for (default: today)
            
        Returns:
            List of all generated tasks
        """
        routines = self.get_user_routines(user_id, active_only=True)
        all_generated_tasks = []
        
        for routine in routines:
            generated_tasks = routine.generate_tasks(self.task_manager, target_date)
            all_generated_tasks.extend(generated_tasks)
            
            # Update routine in database if tasks were generated
            if generated_tasks:
                self.update_routine(routine)
        
        return all_generated_tasks
    
    def activate_routine(self, routine_id: int) -> bool:
        """
        Activate a routine.
        
        Args:
            routine_id: Routine ID
            
        Returns:
            True if successful, False otherwise
        """
        routine = self.get_routine(routine_id)
        if routine:
            routine.is_active = True
            return self.update_routine(routine)
        return False
    
    def deactivate_routine(self, routine_id: int) -> bool:
        """
        Deactivate a routine.
        
        Args:
            routine_id: Routine ID
            
        Returns:
            True if successful, False otherwise
        """
        routine = self.get_routine(routine_id)
        if routine:
            routine.is_active = False
            return self.update_routine(routine)
        return False
