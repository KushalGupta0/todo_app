"""
Database handler module with comprehensive logging.

This module handles all database operations for the To-Do List application.
"""

import sqlite3
import json
import time
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from core.tasks import Task, Tag, Priority
from core.user import User
from utils.logger import get_logger, log_database_operation, log_exception, log_performance


class DatabaseHandler:
    """Handles all database operations with comprehensive logging."""
    
    def __init__(self, db_path: str = "todo_app.db") -> None:
        """
        Initialize database handler.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.logger = get_logger(__name__)
        self._ensure_db_directory()
        
        self.logger.info(f"Database handler initialized with path: {db_path}")
    
    def _ensure_db_directory(self) -> None:
        """Ensure database directory exists."""
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        self.logger.debug(f"Database directory ensured: {db_file.parent}")
    
    def initialize_database(self) -> None:
        """Initialize database tables with logging."""
        start_time = time.time()
        self.logger.info("Starting database initialization")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Users table
                self.logger.debug("Creating users table")
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
                self.logger.debug("Creating tasks table")
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
                self.logger.debug("Creating tags table")
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
                self.logger.debug("Creating task_tags table")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS task_tags (
                        task_id INTEGER,
                        tag_id INTEGER,
                        PRIMARY KEY (task_id, tag_id),
                        FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE,
                        FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
                    )
                """)

                
                conn.commit()
                
                duration = (time.time() - start_time) * 1000
                log_performance("Database initialization", duration)
                self.logger.info("Database initialized successfully")
                
        except sqlite3.Error as e:
            self.logger.error(f"Database initialization failed: {e}")
            log_exception(e, "Database initialization")
            raise
    
    # User operations
    def save_user(self, user: User) -> Optional[int]:
        """
        Save a user to database with logging.
        
        Args:
            user: User to save
            
        Returns:
            User ID if successful, None otherwise
        """
        start_time = time.time()
        self.logger.info(f"Saving user: {user.username}")
        
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
                user_id = cursor.lastrowid
                
                duration = (time.time() - start_time) * 1000
                log_database_operation("CREATE", "users", user_id, True)
                log_performance("Save user", duration)
                self.logger.info(f"User {user.username} saved with ID: {user_id}")
                
                return user_id
                
        except sqlite3.Error as e:
            duration = (time.time() - start_time) * 1000
            log_database_operation("CREATE", "users", None, False)
            log_performance("Save user (failed)", duration)
            self.logger.error(f"Failed to save user {user.username}: {e}")
            log_exception(e, f"Saving user {user.username}")
            return None
    
    def load_user_by_username(self, username: str) -> Optional[User]:
        """
        Load user by username with logging.
        
        Args:
            username: Username to search for
            
        Returns:
            User if found, None otherwise
        """
        start_time = time.time()
        self.logger.debug(f"Loading user by username: {username}")
        
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
                    
                    duration = (time.time() - start_time) * 1000
                    log_database_operation("READ", "users", row[0], True)
                    log_performance("Load user", duration)
                    self.logger.debug(f"User {username} loaded successfully")
                    
                    return user
                else:
                    duration = (time.time() - start_time) * 1000
                    log_database_operation("READ", "users", None, False)
                    log_performance("Load user (not found)", duration)
                    self.logger.debug(f"User {username} not found")
                    
        except sqlite3.Error as e:
            duration = (time.time() - start_time) * 1000
            log_performance("Load user (error)", duration)
            self.logger.error(f"Failed to load user {username}: {e}")
            log_exception(e, f"Loading user {username}")
            
        return None
    
    def user_exists(self, username: str) -> bool:
        """
        Check if user exists with logging.
        
        Args:
            username: Username to check
            
        Returns:
            True if user exists, False otherwise
        """
        start_time = time.time()
        self.logger.debug(f"Checking if user exists: {username}")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
                exists = cursor.fetchone() is not None
                
                duration = (time.time() - start_time) * 1000
                log_performance("Check user exists", duration)
                self.logger.debug(f"User {username} exists: {exists}")
                
                return exists
                
        except sqlite3.Error as e:
            duration = (time.time() - start_time) * 1000
            log_performance("Check user exists (error)", duration)
            self.logger.error(f"Error checking if user {username} exists: {e}")
            log_exception(e, f"Checking user exists {username}")
            return False
    
    def update_user_last_login(self, user: User) -> bool:
        """
        Update user's last login timestamp with logging.
        
        Args:
            user: User to update
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        self.logger.debug(f"Updating last login for user: {user.username}")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users SET last_login = ? WHERE id = ?
                """, (user.last_login.isoformat() if user.last_login else None, user.user_id))
                
                success = cursor.rowcount > 0
                duration = (time.time() - start_time) * 1000
                log_database_operation("UPDATE", "users", user.user_id, success)
                log_performance("Update user last login", duration)
                
                if success:
                    self.logger.debug(f"Last login updated for user: {user.username}")
                else:
                    self.logger.warning(f"Failed to update last login for user: {user.username}")
                
                return success
                
        except sqlite3.Error as e:
            duration = (time.time() - start_time) * 1000
            log_performance("Update user last login (error)", duration)
            self.logger.error(f"Error updating last login for user {user.username}: {e}")
            log_exception(e, f"Updating last login for {user.username}")
            return False
    
    def update_user(self, user: User) -> bool:
        """
        Update user information with logging.
        
        Args:
            user: User to update
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        self.logger.info(f"Updating user: {user.username}")
        
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
                
                success = cursor.rowcount > 0
                duration = (time.time() - start_time) * 1000
                log_database_operation("UPDATE", "users", user.user_id, success)
                log_performance("Update user", duration)
                
                if success:
                    self.logger.info(f"User {user.username} updated successfully")
                else:
                    self.logger.warning(f"Failed to update user {user.username}")
                
                return success
                
        except sqlite3.Error as e:
            duration = (time.time() - start_time) * 1000
            log_performance("Update user (error)", duration)
            self.logger.error(f"Error updating user {user.username}: {e}")
            log_exception(e, f"Updating user {user.username}")
            return False
    
    def load_all_users(self) -> List[User]:
        """
        Load all users with logging.
        
        Returns:
            List of all users
        """
        start_time = time.time()
        self.logger.info("Loading all users")
        
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
                
                duration = (time.time() - start_time) * 1000
                log_performance("Load all users", duration)
                self.logger.info(f"Loaded {len(users)} users")
                
        except sqlite3.Error as e:
            duration = (time.time() - start_time) * 1000
            log_performance("Load all users (error)", duration)
            self.logger.error(f"Error loading all users: {e}")
            log_exception(e, "Loading all users")
            
        return users
    
    # Task operations
    def save_task(self, task: Task) -> Optional[int]:
        """
        Save a task to database with logging.
        
        Args:
            task: Task to save
            
        Returns:
            Task ID if successful, None otherwise
        """
        start_time = time.time()
        self.logger.info(f"Saving task: {task.title}")
        
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
                
                duration = (time.time() - start_time) * 1000
                log_database_operation("CREATE", "tasks", task_id, True)
                log_performance("Save task", duration)
                self.logger.info(f"Task '{task.title}' saved with ID: {task_id}")
                
                return task_id
                
        except sqlite3.Error as e:
            duration = (time.time() - start_time) * 1000
            log_database_operation("CREATE", "tasks", None, False)
            log_performance("Save task (failed)", duration)
            self.logger.error(f"Failed to save task '{task.title}': {e}")
            log_exception(e, f"Saving task '{task.title}'")
            return None
    
    def load_task(self, task_id: int) -> Optional[Task]:
        """
        Load a task by ID with logging.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task if found, None otherwise
        """
        start_time = time.time()
        self.logger.debug(f"Loading task ID: {task_id}")
        
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
                    
                    duration = (time.time() - start_time) * 1000
                    log_database_operation("READ", "tasks", task_id, True)
                    log_performance("Load task", duration)
                    self.logger.debug(f"Task ID {task_id} loaded successfully")
                    
                    return task
                else:
                    duration = (time.time() - start_time) * 1000
                    log_database_operation("READ", "tasks", task_id, False)
                    log_performance("Load task (not found)", duration)
                    self.logger.debug(f"Task ID {task_id} not found")
                    
        except sqlite3.Error as e:
            duration = (time.time() - start_time) * 1000
            log_performance("Load task (error)", duration)
            self.logger.error(f"Error loading task ID {task_id}: {e}")
            log_exception(e, f"Loading task ID {task_id}")
            
        return None
    
    def load_user_tasks(self, user_id: int, include_completed: bool = True) -> List[Task]:
        """
        Load all tasks for a user with logging.
        
        Args:
            user_id: User ID
            include_completed: Whether to include completed tasks
            
        Returns:
            List of user tasks
        """
        start_time = time.time()
        self.logger.debug(f"Loading tasks for user ID {user_id}, include_completed={include_completed}")
        
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
                
                duration = (time.time() - start_time) * 1000
                log_performance("Load user tasks", duration, f"Loaded {len(tasks)} tasks")
                self.logger.debug(f"Loaded {len(tasks)} tasks for user ID {user_id}")
                
        except sqlite3.Error as e:
            duration = (time.time() - start_time) * 1000
            log_performance("Load user tasks (error)", duration)
            self.logger.error(f"Error loading tasks for user ID {user_id}: {e}")
            log_exception(e, f"Loading tasks for user ID {user_id}")
            
        return tasks
    
    def update_task(self, task: Task) -> bool:
        """
        Update an existing task with logging.
        
        Args:
            task: Task to update
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        self.logger.info(f"Updating task: {task.title}")
        
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
                
                success = cursor.rowcount > 0
                duration = (time.time() - start_time) * 1000
                log_database_operation("UPDATE", "tasks", task.task_id, success)
                log_performance("Update task", duration)
                
                if success:
                    self.logger.info(f"Task '{task.title}' updated successfully")
                else:
                    self.logger.warning(f"Failed to update task '{task.title}'")
                
                return success
                
        except sqlite3.Error as e:
            duration = (time.time() - start_time) * 1000
            log_performance("Update task (error)", duration)
            self.logger.error(f"Error updating task '{task.title}': {e}")
            log_exception(e, f"Updating task '{task.title}'")
            return False
    
    def delete_task(self, task_id: int) -> bool:
        """
        Delete a task with logging.
        
        Args:
            task_id: Task ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        self.logger.info(f"Deleting task ID: {task_id}")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                
                success = cursor.rowcount > 0
                duration = (time.time() - start_time) * 1000
                log_database_operation("DELETE", "tasks", task_id, success)
                log_performance("Delete task", duration)
                
                if success:
                    self.logger.info(f"Task ID {task_id} deleted successfully")
                else:
                    self.logger.warning(f"Failed to delete task ID {task_id}")
                
                return success
                
        except sqlite3.Error as e:
            duration = (time.time() - start_time) * 1000
            log_performance("Delete task (error)", duration)
            self.logger.error(f"Error deleting task ID {task_id}: {e}")
            log_exception(e, f"Deleting task ID {task_id}")
            return False
    
    # Tag operations
    def save_tag(self, tag: Tag) -> Optional[int]:
        """
        Save a tag to database with logging.
        
        Args:
            tag: Tag to save
            
        Returns:
            Tag ID if successful, None otherwise
        """
        start_time = time.time()
        self.logger.debug(f"Saving tag: {tag.name}")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO tags (name, color, description, created_at)
                    VALUES (?, ?, ?, ?)
                """, (tag.name, tag.color, tag.description, tag.created_at.isoformat()))
                
                if cursor.rowcount > 0:
                    tag_id = cursor.lastrowid
                    duration = (time.time() - start_time) * 1000
                    log_database_operation("CREATE", "tags", tag_id, True)
                    log_performance("Save tag", duration)
                    self.logger.debug(f"Tag '{tag.name}' saved with ID: {tag_id}")
                    return tag_id
                else:
                    # Tag already exists, get its ID
                    cursor.execute("SELECT id FROM tags WHERE name = ?", (tag.name,))
                    row = cursor.fetchone()
                    tag_id = row[0] if row else None
                    
                    duration = (time.time() - start_time) * 1000
                    log_performance("Save tag (exists)", duration)
                    self.logger.debug(f"Tag '{tag.name}' already exists with ID: {tag_id}")
                    return tag_id
                    
        except sqlite3.Error as e:
            duration = (time.time() - start_time) * 1000
            log_performance("Save tag (error)", duration)
            self.logger.error(f"Error saving tag '{tag.name}': {e}")
            log_exception(e, f"Saving tag '{tag.name}'")
            return None
    
    def load_tag_by_name(self, name: str) -> Optional[Tag]:
        """
        Load tag by name with logging.
        
        Args:
            name: Tag name
            
        Returns:
            Tag if found, None otherwise
        """
        start_time = time.time()
        self.logger.debug(f"Loading tag by name: {name}")
        
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
                    
                    duration = (time.time() - start_time) * 1000
                    log_performance("Load tag", duration)
                    self.logger.debug(f"Tag '{name}' loaded successfully")
                    
                    return tag
                else:
                    duration = (time.time() - start_time) * 1000
                    log_performance("Load tag (not found)", duration)
                    self.logger.debug(f"Tag '{name}' not found")
                    
        except sqlite3.Error as e:
            duration = (time.time() - start_time) * 1000
            log_performance("Load tag (error)", duration)
            self.logger.error(f"Error loading tag '{name}': {e}")
            log_exception(e, f"Loading tag '{name}'")
            
        return None
    
    def load_all_tags(self) -> List[Tag]:
        """
        Load all tags with logging.
        
        Returns:
            List of all tags
        """
        start_time = time.time()
        self.logger.debug("Loading all tags")
        
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
                
                duration = (time.time() - start_time) * 1000
                log_performance("Load all tags", duration, f"Loaded {len(tags)} tags")
                self.logger.debug(f"Loaded {len(tags)} tags")
                
        except sqlite3.Error as e:
            duration = (time.time() - start_time) * 1000
            log_performance("Load all tags (error)", duration)
            self.logger.error(f"Error loading all tags: {e}")
            log_exception(e, "Loading all tags")
            
        return tags
    
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
