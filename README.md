
# Multimodal AI Agent Desktop Application - Comprehensive Guide

## Overview

This is a PyQt6-based desktop application that provides an interface for interacting with multiple AI agents. The application features a chat window where users can communicate with AI and an agent workspace where specialized AI agents (Coder, Computer, Assistant) can perform specific tasks with dedicated tools.

## Application Structure

The application follows a modular architecture with clear separation of concerns:

```
app/
├── ui/                    # User interface components
│   ├── main_window.py     # Main application window
│   ├── chat_widget.py     # Chat interface
│   ├── agent_workspace.py # Agent tools and interfaces
│   └── components/        # UI components (editor, terminal, etc.)
├── agents/                # Agent implementations
│   ├── base_agent.py      # Abstract base class for all agents
│   ├── coder_agent/       # Code-focused agent
│   ├── computer_agent/    # System operation agent
│   └── assistant_agent/   # General purpose assistant
├── controller/            # Application logic
│   ├── app_controller.py  # Main controller
│   ├── llm_controller.py  # LLM interface
│   └── event_manager.py   # Event handling
├── utils/                 # Utility functions
├── extensions/            # App extensions
├── resources/             # Application resources
└── config.py              # Configuration management
```

## Application Workflow

1. The application starts in `main.py`, which initializes the `AppController` and `MainWindow`
2. The UI is split into two main areas:
   - A chat widget for user-AI interaction
   - An agent workspace with tabs for different AI agents
3. User workflow:
   - User types a message in the chat interface
   - Message is processed by the `AppController`
   - The appropriate agent is activated based on the message
   - The agent produces a response shown in the chat
   - The agent workspace is updated with relevant tools
   - User can interact with both chat and workspace simultaneously

## Key Components

### 1. MainWindow (main_window.py)

The main application window that contains all UI elements and handles overall layout.

```python:app/ui/main_window.py
class MainWindow(QMainWindow):
    def __init__(self, core_controller):
        # Initialize main window with controller
        # Set up layout with splitter for chat and workspace
        # Configure menus, toolbars, and connect signals
```

Key features:
- **Main layout**: Horizontal splitter with chat on left, agent workspace on right
- **Menu bar**: File, Agents, and Settings menus
- **Toolbar**: Quick access to agents and layout options
- **Status bar**: Shows application status messages

### 2. ChatWidget (chat_widget.py)

Handles user interaction with the AI through a chat interface.

```python:app/ui/chat_widget.py
class ChatWidget(QWidget):
    agent_invoked = pyqtSignal(str)  # Signal when agent is invoked
    
    def __init__(self, core_controller):
        # Initialize chat interface
        # Set up UI components for displaying and sending messages
```

Key features:
- Text area for chat history
- Input field for user messages
- Send button for submitting messages
- Signal system to notify when agents should be activated

### 3. AgentWorkspace (agent_workspace.py)

A tabbed interface where different agents can display their specialized tools.

```python:app/ui/agent_workspace.py
class AgentWorkspace(QWidget):
    status_message = pyqtSignal(str)
    
    def __init__(self, core_controller):
        # Initialize workspace with tabs
        # Set up UI for different agent workspaces
```

Key features:
- Tabbed interface for multiple agents
- Agent-specific workspaces (coder, computer, assistant)
- Dynamic creation of agent workspaces
- Custom tools for each agent type

### 4. BaseAgent (base_agent.py)

Abstract base class that defines the interface all agents must implement.

```python:app/agents/base_agent.py
class BaseAgent(ABC):
    """Base interface that all agents must implement."""
    
    @property
    @abstractmethod
    def agent_type(self):
        """Return the type identifier for this agent."""
        pass
    
    # Other abstract methods for initialization, processing, etc.
```

Key requirements:
- Each agent must define its type and capabilities
- Agents must implement initialize, process, cleanup methods
- Agents provide UI components for the workspace
- Agents handle UI events specific to their functionality

### 5. AppController (app_controller.py)

Central controller managing application logic and communication between components.

```python:app/controller/app_controller.py
class AppController:
    def __init__(self):
        # Initialize controllers and managers
        # Set up LLM, events, and agents
```

Key responsibilities:
- Process user input from chat
- Route requests to appropriate agents
- Manage agents through AgentManager
- Handle application events
- Connect UI components to backend logic

### 6. Config (config.py)

Manages application configuration settings.

```python:app/config.py
class Config:
    """Application configuration manager"""
    
    def _create_default_config(self):
        """Create default configuration"""
        default_config = {
            "app": { /* app settings */ },
            "llm": { /* LLM settings */ },
            "agents": { /* agent settings */ },
            "ui": { /* UI settings */ }
        }
```

Key features:
- Stores application, LLM, agent, and UI settings
- Provides defaults when config file doesn't exist
- Handles saving/loading configurations

## Agent Types

### 1. Coder Agent
- Specialized in code editing and programming tasks
- Features a code editor and terminal
- Can write, analyze, and debug code

### 2. Computer Agent
- Interacts with the local system
- Can browse files and execute commands
- Has security restrictions for system safety

### 3. Assistant Agent
- General purpose AI assistant
- Provides information and answers questions
- Simpler interface focused on information display

## Event Flow

1. User enters a message in the chat
2. ChatWidget sends message to AppController
3. AppController processes the message, possibly with LLMController
4. If an agent is needed, the appropriate agent is activated
5. Agent processes the request and returns a response
6. Response is displayed in chat and workspace is updated
7. User can continue interaction in either chat or workspace

This desktop application provides a flexible and powerful interface for interacting with multiple AI agents, each with specialized capabilities, all within a unified user experience.
