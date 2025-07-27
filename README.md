# To-Do List Manager

A modern, feature-rich To-Do List application built with PySide6 and Python. This application provides a clean, user-friendly interface for managing tasks with comprehensive logging, user authentication, and advanced filtering capabilities.

## 🎯 Features

### Core Functionality

- **User Authentication**: Secure login and registration system with password hashing
- **Task Management**: Create, edit, delete, and organize tasks
- **Task Completion**: Mark tasks as complete with visual strikethrough
- **Priority System**: Assign priority levels (Low, Medium, High, Urgent) with color indicators
- **Due Dates**: Set and track task deadlines with overdue detection
- **Search \& Filter**: Advanced filtering by status, priority, and text search
- **Comprehensive Logging**: Detailed application logs for debugging and monitoring


### User Interface

- **Modern Design**: Clean, professional interface with proper color schemes
- **Responsive Layout**: Scrollable areas and resizable panels
- **Visual Indicators**: Color-coded priority dots and completion status
- **Context Menus**: Right-click options for task management
- **Keyboard Shortcuts**: Quick access to common functions
- **Real-time Updates**: Live statistics and status updates


## 📁 Project Structure

```
todo_app_project/
├── .venv/                    # Virtual environment
├── logs/                     # Application logs (auto-generated)
├── requirements.txt          # Dependencies
└── todo_app/                # Main application
    ├── __init__.py
    ├── main.py              # Entry point
    ├── todo_app.db          # SQLite database (auto-generated)
    ├── core/                # Business logic
    │   ├── __init__.py
    │   ├── tasks.py         # Task management classes
    │   └── user.py          # User authentication
    ├── gui/                 # User interface
    │   ├── __init__.py
    │   ├── login.py         # Login/registration window
    │   ├── todowindow.py    # Main application window
    │   └── widgets.py       # Custom UI components
    ├── database/            # Data persistence
    │   ├── __init__.py
    │   └── db_handler.py    # Database operations
    └── utils/               # Utilities
        ├── __init__.py
        ├── logger.py        # Logging configuration
        └── validators.py    # Input validation
```


## 🚀 Installation \& Setup

### Prerequisites

- Python 3.8 or higher
- Virtual environment support


### Step-by-Step Installation

1. **Create Project Directory**

```bash
mkdir todo_app_project
cd todo_app_project
```

2. **Set Up Virtual Environment**

```bash
# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

3. **Install Dependencies**

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. **Run the Application**

```bash
cd todo_app
python main.py
```


## 📦 Dependencies

```
PySide6>=6.5.0
bcrypt>=4.0.0
```


## 🏗️ Architecture Overview

### Core Modules

#### `core/tasks.py`

- **Task Class**: Represents individual tasks with properties like title, description, priority, due date
- **TaskManager Class**: Handles CRUD operations for tasks
- **Priority Enum**: Defines priority levels (LOW, MEDIUM, HIGH, URGENT)

Key Features:

- Priority management with visual indicators
- Due date tracking and overdue detection
- Completion status tracking


#### `core/user.py`

- **User Class**: Represents user accounts with secure password handling
- **UserManager Class**: Handles user authentication and account management

Security Features:

- Password hashing using bcrypt
- Secure login/logout functionality
- User session management


#### `database/db_handler.py`

- **DatabaseHandler Class**: Manages all database operations
- **SQLite Integration**: Lightweight, file-based database
- **Comprehensive Logging**: All database operations are logged

Database Schema:

- `users`: User accounts and authentication data
- `tasks`: Task information and relationships
- Foreign key constraints ensure data integrity


#### `utils/logger.py`

- **TodoLogger Class**: Centralized logging system
- **Multiple Log Levels**: DEBUG, INFO, WARNING, ERROR
- **Log Rotation**: Daily log files with 30-day retention
- **Performance Tracking**: Operation timing and metrics


### GUI Components

#### `gui/login.py`

- **LoginWindow Class**: User authentication interface
- **Tabbed Interface**: Separate tabs for login and registration
- **Input Validation**: Real-time form validation
- **Responsive Design**: Scrollable layout for different screen sizes

Features:

- Password strength requirements
- User-friendly error messages
- Professional styling


#### `gui/todowindow.py`

- **TodoWindow Class**: Main application interface
- **Split Layout**: Filters panel and task display area
- **Advanced Filtering**: Multiple filter options with manual apply/reset
- **Statistics Panel**: Real-time task counts and metrics

Interface Elements:

- Menu bar with keyboard shortcuts
- Toolbar for quick actions
- Status bar for user feedback
- Context-sensitive help


#### `gui/widgets.py`

- **TaskWidget Class**: Individual task display components
- **TaskTreeWidget Class**: Hierarchical task list display
- **Custom Styling**: Consistent visual design

Interactive Features:

- Hover effects and visual feedback
- Drag-and-drop support
- Context menus for task actions


## 💾 Database Design

The application uses SQLite with the following schema:

### Tables

#### Users Table

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT,
    password_hash BLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);
```


#### Tasks Table

```sql
CREATE TABLE tasks (
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
);
```


## 📊 Logging System

The application includes comprehensive logging for debugging and monitoring:

### Log Files

- **`logs/TodoApp_app_YYYY-MM-DD.log`**: Daily rotating logs
- **`logs/session_YYYYMMDD_HHMMSS.log`**: Individual session logs
- **`logs/error.log`**: Error-only log file


### Logged Events

- User authentication (login/logout/registration)
- Task operations (create/update/delete/complete)
- Database operations with performance metrics
- UI interactions and navigation
- Error handling with full stack traces


### Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General application flow
- **WARNING**: Potentially harmful situations
- **ERROR**: Error events that don't stop the application
- **CRITICAL**: Serious errors that may abort the program


## 🎨 User Interface

### Design Principles

- **Clean \& Modern**: Professional appearance with consistent styling
- **User-Friendly**: Intuitive navigation and clear visual hierarchy
- **Responsive**: Adapts to different screen sizes and resolutions
- **Accessible**: High contrast colors and readable fonts


### Color Scheme

- **Primary Blue**: `#007bff` (buttons and accents)
- **Success Green**: `#28a745` (completion indicators)
- **Warning Yellow**: `#ffc107` (medium priority)
- **Danger Red**: `#dc3545` (urgent priority, errors)
- **Background**: `#f8f9fa` (light gray)
- **Text**: `#000000` (black for maximum readability)


### Priority Indicators

Tasks display colored dots indicating priority levels:

- 🟢 **Green**: Low Priority
- 🟡 **Yellow**: Medium Priority
- 🟠 **Orange**: High Priority
- 🔴 **Red**: Urgent Priority


## 🔧 Configuration

### Application Settings

The application automatically configures itself with sensible defaults:

- Database location: `todo_app.db` in the application directory
- Log directory: `logs/` (auto-created)
- Session timeout: Managed automatically
- UI scaling: Adapts to system settings


### Customization Options

Users can customize:

- Task priorities when creating/editing tasks
- Due dates for deadline tracking
- Filter preferences (saved per session)
- Window layout (resizable panels)


## 🚦 Usage Guide

### First Time Setup

1. **Launch Application**: Run `python main.py`
2. **Create Account**: Use the Registration tab to create a new user account
3. **Login**: Switch to Login tab and enter your credentials
4. **Start Managing Tasks**: Use the + Add Task button to create your first task

### Daily Workflow

1. **View Tasks**: Main window shows all your tasks in a hierarchical list
2. **Filter Tasks**: Use the filters panel to find specific tasks
3. **Add Tasks**: Click "+ Add Task" or use Ctrl+N
4. **Edit Tasks**: Double-click a task or right-click for context menu
5. **Complete Tasks**: Check the completion checkbox to mark tasks done
6. **Monitor Progress**: Statistics panel shows your productivity metrics

### Advanced Features

- **Search**: Use the search box to find tasks by title or description
- **Filtering**: Combine multiple filters for precise task lists
- **Keyboard Shortcuts**: Use Ctrl+N (new task), F5 (refresh), Ctrl+Q (quit)


## 🐛 Troubleshooting

### Common Issues

#### "ModuleNotFoundError: No module named 'PySide6'"

- **Solution**: Ensure virtual environment is activated and dependencies are installed

```bash
source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```


#### Application Won't Start

- **Check**: Virtual environment activation
- **Check**: All required files are present
- **Check**: Python version (3.8+)
- **Review**: Log files in `logs/` directory for error details


#### Database Errors

- **Solution**: Delete `todo_app.db` file (will recreate with empty database)
- **Prevention**: Regular backups of database file


#### Login Issues

- **Check**: Username/password accuracy (case-sensitive)
- **Reset**: Create new account if password forgotten
- **Logs**: Check error logs for authentication details


### Debug Mode

The application includes comprehensive logging. To troubleshoot:

1. Check console output for immediate errors
2. Review log files in `logs/` directory
3. Look for ERROR level messages
4. Check session logs for specific user actions

## 🔒 Security Features

### Password Security

- **bcrypt Hashing**: Industry-standard password hashing
- **Salt Generation**: Unique salt for each password
- **Minimum Requirements**: 6 character minimum length
- **Secure Storage**: Passwords never stored in plain text


### Data Protection

- **Local Storage**: All data stored locally (no cloud transmission)
- **User Isolation**: Tasks isolated per user account
- **Session Management**: Automatic logout on application close
- **Input Validation**: Prevents SQL injection and XSS attacks


## 📈 Performance

### Optimization Features

- **Efficient Queries**: Optimized database operations
- **Lazy Loading**: Tasks loaded on-demand
- **Caching**: Frequently accessed data cached in memory
- **Async UI**: Non-blocking user interface updates


### Performance Monitoring

- **Timing Logs**: All operations timed and logged
- **Memory Usage**: Efficient data structures
- **Database Indexing**: Optimized for quick searches
- **UI Responsiveness**: Smooth animations and interactions


## 🔄 Development Workflow

### Code Organization

The codebase follows clean architecture principles:

- **Separation of Concerns**: UI, business logic, and data layers separated
- **Type Annotations**: Full type hints for better IDE support
- **Documentation**: Comprehensive docstrings for all public methods
- **Error Handling**: Graceful error handling with user feedback


### Adding New Features

1. **Core Logic**: Add business logic to appropriate `core/` module
2. **Database**: Update `db_handler.py` for data persistence
3. **UI Components**: Create or modify widgets in `gui/` modules
4. **Integration**: Connect UI to business logic through signals/slots
5. **Testing**: Verify functionality and check logs for errors

## 📝 Changelog

### Version 1.0.0 (Current)

- ✅ Core task management functionality
- ✅ User authentication system
- ✅ Priority-based task organization
- ✅ Advanced filtering and search
- ✅ Comprehensive logging system
- ✅ Modern PySide6 interface


## 🤝 Contributing

### Code Style

- Follow PEP 8 standards
- Use type annotations
- Include comprehensive docstrings
- Maintain existing logging patterns


### Testing

- Test all user workflows
- Verify database operations
- Check error handling
- Validate UI responsiveness


## 📄 License

This project is a personal productivity application. Feel free to modify and extend for your own use.

## 🆘 Support

For issues or questions:

1. Check the troubleshooting section above
2. Review log files for error details
3. Verify installation steps were followed correctly
4. Ensure all dependencies are properly installed

**Built with ❤️ using Python and PySide6**

*A modern, efficient, and user-friendly task management solution.*

