"""
Database handler module.

This module handles all database operations for the To-Do List application.
"""

import sqlite3
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from core.tasks import Task, Tag, Priority
from core.user import User
from core.routines import Routine, RepeatType


class DatabaseHandler:
    """Handles all database operations."""
    
    def __init__(self, db_path: str = "todo_app.db") -> None:
        """
        Initialize database handler.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_db_directory()
    
    def _ensure_db_directory(self) -> None:
        """Ensure database directory exists."""
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
    
    def initialize_database(self) -> None:
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT,
                    password_hash BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # Tasks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    completed BOOLEAN DEFAULT 0,
                    parent_id INTEGER,
                    user_id INTEGER NOT NULL,
                    priority INTEGER DEFAULT 2,
                    due_date TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    additional_properties TEXT,
                    FOREIGN KEY (parent_id) REFERENCES tasks (id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)
            
            # Tags table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    color TEXT DEFAULT '#3498db',
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Task-Tags relationship table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_tags (
                    task_id INTEGER,
                    tag_id INTEGER,
                    PRIMARY KEY (task_id, tag_id),
                    FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE,
                    FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
                )
            """)
            
            # Routines table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS routines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    user_id INTEGER NOT NULL,
                    repeat_type TEXT DEFAULT 'daily',
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_generated TIMESTAMP,
                    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_date TIMESTAMP,
                    preferred_time TEXT,
                    custom_days TEXT,
                    repeat_interval INTEGER DEFAULT 1,
                    task_templates TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            """)
            
            conn.commit()
    
    # User operations
    def save_user(self, user: User) -> Optional[int]:
        """
        Save a user to database.
        
        Args:
            user: User to save
            
        Returns:
            User ID if successful, None otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, created_at, is_active)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    user.username,
                    user.email,
                    user.password_hash,
                    user.created_at.isoformat(),
                    user.is_active
                ))
                return cursor.lastrowid
        except sqlite3.Error:
            return None
    
    def load_user_by_username(self, username: str) -> Optional[User]:
        """
        Load user by username.
        
        Args:
            username: Username to search for
            
        Returns:
            User if found, None otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, username, email, password_hash, created_at, last_login, is_active
                    FROM users WHERE username = ?
                """, (username,))
                
                row = cursor.fetchone()
                if row:
                    user = User(row[1], row[2], row[0], row[3])
                    user.created_at = datetime.fromisoformat(row[4]) if row[4] else datetime.now()
                    user.last_login = datetime.fromisoformat(row[5]) if row[5] else None
                    user.is_active = bool(row[6])
                    return user
        except sqlite3.Error:
            pass
        return None
    
    def user_exists(self, username: str) -> bool:
        """
        Check if user exists.
        
        Args:
            username: Username to check
            
        Returns:
            True if user exists, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
                return cursor.fetchone() is not None
        except sqlite3.Error:
            return False
    
    def update_user_last_login(self, user: User) -> bool:
        """
        Update user's last login timestamp.
        
        Args:
            user: User to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users SET last_login = ? WHERE id = ?
                """, (user.last_login.isoformat() if user.last_login else None, user.user_id))
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False
    
    def update_user(self, user: User) -> bool:
        """
        Update user information.
        
        Args:
            user: User to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users SET username = ?, email = ?, password_hash = ?, is_active = ?
                    WHERE id = ?
                """, (
                    user.username,
                    user.email,
                    user.password_hash,
                    user.is_active,
                    user.user_id
                ))
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False
    
    def load_all_users(self) -> List[User]:
        """
        Load all users.
        
        Returns:
            List of all users
        """
        users = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, username, email, password_hash, created_at, last_login, is_active
                    FROM users ORDER BY username
                """)
                
                for row in cursor.fetchall():
                    user = User(row[1], row[2], row[0], row[3])
                    user.created_at = datetime.fromisoformat(row[4]) if row[4] else datetime.now()
                    user.last_login = datetime.fromisoformat(row[5]) if row[5] else None
                    user.is_active = bool(row[6])
                    users.append(user)
        except sqlite3.Error:
            pass
        return users
    
    # Task operations
    def save_task(self, task: Task) -> Optional[int]:
        """
        Save a task to database.
        
        Args:
            task: Task to save
            
        Returns:
            Task ID if successful, None otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO tasks (
                        title, description, completed, parent_id, user_id, priority,
                        due_date, created_at, updated_at, completed_at, additional_properties
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task.title,
                    task.description,
                    task.completed,
                    task.parent_id,
                    task.user_id,
                    task.priority.value,
                    task.due_date.isoformat() if task.due_date else None,
                    task.created_at.isoformat(),
                    task.updated_at.isoformat(),
                    task.completed_at.isoformat() if task.completed_at else None,
                    json.dumps(task.additional_properties)
                ))
                task_id = cursor.lastrowid
                
                # Save tags
                if task.tags:
                    self._save_task_tags(conn, task_id, task.tags)
                
                return task_id
        except sqlite3.Error:
            return None
    
    def load_task(self, task_id: int) -> Optional[Task]:
        """
        Load a task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task if found, None otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, title, description, completed, parent_id, user_id, priority,
                           due_date, created_at, updated_at, completed_at, additional_properties
                    FROM tasks WHERE id = ?
                """, (task_id,))
                
                row = cursor.fetchone()
                if row:
                    task = self._row_to_task(row)
                    task.tags = self._load_task_tags(conn, task_id)
                    return task
        except sqlite3.Error:
            pass
        return None
    
    def load_user_tasks(self, user_id: int, include_completed: bool = True) -> List[Task]:
        """
        Load all tasks for a user.
        
        Args:
            user_id: User ID
            include_completed: Whether to include completed tasks
            
        Returns:
            List of user tasks
        """
        tasks = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT id, title, description, completed, parent_id, user_id, priority,
                           due_date, created_at, updated_at, completed_at, additional_properties
                    FROM tasks WHERE user_id = ?
                """
                params = [user_id]
                
                if not include_completed:
                    query += " AND completed = 0"
                
                query += " ORDER BY created_at DESC"
                
                cursor.execute(query, params)
                
                for row in cursor.fetchall():
                    task = self._row_to_task(row)
                    task.tags = self._load_task_tags(conn, task.task_id)
                    tasks.append(task)
        except sqlite3.Error:
            pass
        return tasks
    
    def update_task(self, task: Task) -> bool:
        """
        Update an existing task.
        
        Args:
            task: Task to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE tasks SET
                        title = ?, description = ?, completed = ?, parent_id = ?,
                        priority = ?, due_date = ?, updated_at = ?, completed_at = ?,
                        additional_properties = ?
                    WHERE id = ?
                """, (
                    task.title,
                    task.description,
                    task.completed,
                    task.parent_id,
                    task.priority.value,
                    task.due_date.isoformat() if task.due_date else None,
                    task.updated_at.isoformat(),
                    task.completed_at.isoformat() if task.completed_at else None,
                    json.dumps(task.additional_properties),
                    task.task_id
                ))
                
                # Update tags
                self._delete_task_tags(conn, task.task_id)
                if task.tags:
                    self._save_task_tags(conn, task.task_id, task.tags)
                
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False
    
    def delete_task(self, task_id: int) -> bool:
        """
        Delete a task.
        
        Args:
            task_id: Task ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False
    
    # Tag operations
    def save_tag(self, tag: Tag) -> Optional[int]:
        """
        Save a tag to database.
        
        Args:
            tag: Tag to save
            
        Returns:
            Tag ID if successful, None otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO tags (name, color, description, created_at)
                    VALUES (?, ?, ?, ?)
                """, (tag.name, tag.color, tag.description, tag.created_at.isoformat()))
                
                if cursor.rowcount > 0:
                    return cursor.lastrowid
                else:
                    # Tag already exists, get its ID
                    cursor.execute("SELECT id FROM tags WHERE name = ?", (tag.name,))
                    row = cursor.fetchone()
                    return row[0] if row else None
        except sqlite3.Error:
            return None
    
    def load_tag_by_name(self, name: str) -> Optional[Tag]:
        """
        Load tag by name.
        
        Args:
            name: Tag name
            
        Returns:
            Tag if found, None otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name, color, description, created_at
                    FROM tags WHERE name = ?
                """, (name,))
                
                row = cursor.fetchone()
                if row:
                    tag = Tag(row[0], row[1], row[2])
                    tag.created_at = datetime.fromisoformat(row[3]) if row[3] else datetime.now()
                    return tag
        except sqlite3.Error:
            pass
        return None
    
    def load_all_tags(self) -> List[Tag]:
        """
        Load all tags.
        
        Returns:
            List of all tags
        """
        tags = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name, color, description, created_at
                    FROM tags ORDER BY name
                """)
                
                for row in cursor.fetchall():
                    tag = Tag(row[0], row[1], row[2])
                    tag.created_at = datetime.fromisoformat(row[3]) if row[3] else datetime.now()
                    tags.append(tag)
        except sqlite3.Error:
            pass
        return tags
    
    # Routine operations
    def save_routine(self, routine: Routine) -> Optional[int]:
        """
        Save a routine to database.
        
        Args:
            routine: Routine to save
            
        Returns:
            Routine ID if successful, None otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO routines (
                        name, description, user_id, repeat_type, is_active, created_at,
                        last_generated, start_date, end_date, preferred_time,
                        custom_days, repeat_interval, task_templates
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    routine.name,
                    routine.description,
                    routine.user_id,
                    routine.repeat_type.value,
                    routine.is_active,
                    routine.created_at.isoformat(),
                    routine.last_generated.isoformat() if routine.last_generated else None,
                    routine.start_date.isoformat(),
                    routine.end_date.isoformat() if routine.end_date else None,
                    routine.preferred_time.isoformat() if routine.preferred_time else None,
                    json.dumps(routine.custom_days),
                    routine.repeat_interval,
                    json.dumps(routine.task_templates)
                ))
                return cursor.lastrowid
        except sqlite3.Error:
            return None
    
    def load_routine(self, routine_id: int) -> Optional[Routine]:
        """
        Load a routine by ID.
        
        Args:
            routine_id: Routine ID
            
        Returns:
            Routine if found, None otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, description, user_id, repeat_type, is_active,
                           created_at, last_generated, start_date, end_date,
                           preferred_time, custom_days, repeat_interval, task_templates
                    FROM routines WHERE id = ?
                """, (routine_id,))
                
                row = cursor.fetchone()
                if row:
                    return self._row_to_routine(row)
        except sqlite3.Error:
            pass
        return None
    
    def load_user_routines(self, user_id: int, active_only: bool = True) -> List[Routine]:
        """
        Load routines for a user.
        
        Args:
            user_id: User ID
            active_only: Whether to load only active routines
            
        Returns:
            List of routines
        """
        routines = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT id, name, description, user_id, repeat_type, is_active,
                           created_at, last_generated, start_date, end_date,
                           preferred_time, custom_days, repeat_interval, task_templates
                    FROM routines WHERE user_id = ?
                """
                params = [user_id]
                
                if active_only:
                    query += " AND is_active = 1"
                
                query += " ORDER BY name"
                
                cursor.execute(query, params)
                
                for row in cursor.fetchall():
                    routine = self._row_to_routine(row)
                    routines.append(routine)
        except sqlite3.Error:
            pass
        return routines
    
    def update_routine(self, routine: Routine) -> bool:
        """
        Update a routine.
        
        Args:
            routine: Routine to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE routines SET
                        name = ?, description = ?, repeat_type = ?, is_active = ?,
                        last_generated = ?, start_date = ?, end_date = ?,
                        preferred_time = ?, custom_days = ?, repeat_interval = ?,
                        task_templates = ?
                    WHERE id = ?
                """, (
                    routine.name,
                    routine.description,
                    routine.repeat_type.value,
                    routine.is_active,
                    routine.last_generated.isoformat() if routine.last_generated else None,
                    routine.start_date.isoformat(),
                    routine.end_date.isoformat() if routine.end_date else None,
                    routine.preferred_time.isoformat() if routine.preferred_time else None,
                    json.dumps(routine.custom_days),
                    routine.repeat_interval,
                    json.dumps(routine.task_templates),
                    routine.routine_id
                ))
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False
    
    def delete_routine(self, routine_id: int) -> bool:
        """
        Delete a routine.
        
        Args:
            routine_id: Routine ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM routines WHERE id = ?", (routine_id,))
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False
    
    # Helper methods
    def _row_to_task(self, row) -> Task:
        """Convert database row to Task object."""
        task = Task(row[1], row[2], row[0], row[4], row[5])
        task.completed = bool(row[3])
        task.priority = Priority(row[6])
        task.due_date = datetime.fromisoformat(row[7]) if row[7] else None
        task.created_at = datetime.fromisoformat(row[8]) if row[8] else datetime.now()
        task.updated_at = datetime.fromisoformat(row[9]) if row[9] else datetime.now()
        task.completed_at = datetime.fromisoformat(row[10]) if row[10] else None
        task.additional_properties = json.loads(row[11]) if row[11] else {}
        return task
    
    def _row_to_routine(self, row) -> Routine:
        """Convert database row to Routine object."""
        routine = Routine(row[1], row[2], row[0], row[3])
        routine.repeat_type = RepeatType(row[4])
        routine.is_active = bool(row[5])
        routine.created_at = datetime.fromisoformat(row[6]) if row[6] else datetime.now()
        routine.last_generated = datetime.fromisoformat(row[7]) if row[7] else None
        routine.start_date = datetime.fromisoformat(row[8]) if row[8] else datetime.now()
        routine.end_date = datetime.fromisoformat(row[9]) if row[9] else None
        routine.preferred_time = datetime.fromisoformat(row[10]).time() if row[10] else None
        routine.custom_days = json.loads(row[11]) if row[11] else []
        routine.repeat_interval = row[12]
        routine.task_templates = json.loads(row[13]) if row[13] else []
        return routine
    
    def _save_task_tags(self, conn, task_id: int, tags: set) -> None:
        """Save task-tag relationships."""
        cursor = conn.cursor()
        
        for tag in tags:
            # Ensure tag exists
            tag_id = self.save_tag(tag)
            if tag_id:
                # Create relationship
                cursor.execute("""
                    INSERT OR IGNORE INTO task_tags (task_id, tag_id)
                    VALUES (?, ?)
                """, (task_id, tag_id))
    
    def _load_task_tags(self, conn, task_id: int) -> set:
        """Load tags for a task."""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.name, t.color, t.description, t.created_at
            FROM tags t
            JOIN task_tags tt ON t.id = tt.tag_id
            WHERE tt.task_id = ?
        """, (task_id,))
        
        tags = set()
        for row in cursor.fetchall():
            tag = Tag(row[0], row[1], row[2])
            tag.created_at = datetime.fromisoformat(row[3]) if row[3] else datetime.now()
            tags.add(tag)
        
        return tags
    
    def _delete_task_tags(self, conn, task_id: int) -> None:
        """Delete all tags for a task."""
        cursor = conn.cursor()
        cursor.execute("DELETE FROM task_tags WHERE task_id = ?", (task_id,))
