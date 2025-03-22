# app/ui/agent_workspace.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, 
                            QSplitter, QStackedWidget, QLabel, QApplication)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QEvent
import asyncio
import threading
import os

from .components.code_editor import CodeEditor
from .components.terminal import Terminal, Shell
from .components.file_browser import FileExplorer

# Custom event for command completion
class CommandCompletedEvent(QEvent):
    """Custom event for command completion"""
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())
    
    def __init__(self, result):
        super().__init__(self.EVENT_TYPE)
        self.result = result

class AgentWorkspace(QWidget):
    status_message = pyqtSignal(str)
    
    def __init__(self, core_controller):
        super().__init__()
        self.core_controller = core_controller
        self.agents = {}  # Store active agent widgets
        
        # Initialize computer agent instance directly
        from app.agents.computer_agent.computer_agent import ComputerAgent
        self.computer_agent = ComputerAgent()
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Agent workspace label
        self.title_label = QLabel("Agent Workspace")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Tab widget for multiple agents
        self.agent_tabs = QTabWidget()
        self.agent_tabs.setTabsClosable(True)
        self.agent_tabs.tabCloseRequested.connect(self._handle_tab_close_request)
        layout.addWidget(self.agent_tabs)
        
        # Create default welcome tab
        welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_label = QLabel("Select an agent to get started")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(welcome_label)
        
        self.agent_tabs.addTab(welcome_widget, "Welcome")
        
    @pyqtSlot(str)
    def activate_agent(self, agent_type):
        """Activate or focus an agent workspace"""
        # Check if agent tab already exists
        if agent_type in self.agents:
            # Focus existing tab
            self.agent_tabs.setCurrentWidget(self.agents[agent_type])
            return
            
        # Create new agent workspace based on type
        if agent_type == "coder":
            agent_widget = self.create_coder_workspace()
            tab_title = "Coder"
        elif agent_type == "computer":
            agent_widget = self.create_computer_workspace()
            tab_title = "Computer"
        elif agent_type == "assistant":
            agent_widget = self.create_assistant_workspace()
            tab_title = "Assistant"
        else:
            self.status_message.emit(f"Unknown agent type: {agent_type}")
            return
            
        # Add new tab and store reference
        tab_index = self.agent_tabs.addTab(agent_widget, tab_title)
        self.agents[agent_type] = agent_widget
        
        # Switch to new tab
        self.agent_tabs.setCurrentIndex(tab_index)
        self.status_message.emit(f"{tab_title} agent workspace opened")
        
    def create_coder_workspace(self):
        """Create a coding workspace with editor and terminal"""
        workspace = QWidget()
        layout = QVBoxLayout(workspace)
        
        # Create vertical splitter for editor and terminal
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Add code editor
        editor = CodeEditor()
        editor.set_language("python")  # Default language
        
        # Add terminal
        terminal = Terminal()
        
        # Add to splitter
        splitter.addWidget(editor)
        splitter.addWidget(terminal)
        splitter.setSizes([700, 300])  # Default sizes
        
        layout.addWidget(splitter)
        return workspace
        
    def create_computer_workspace(self):
        """Create workspace for computer agent"""
        workspace = QWidget()
        layout = QVBoxLayout(workspace)
        
        # Create horizontal splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Add file explorer
        file_explorer = FileExplorer()
        
        # Add shell terminal
        self._setup_terminal()
        
        # Add to splitter
        splitter.addWidget(file_explorer)
        splitter.addWidget(self.terminal_container)
        splitter.setSizes([400, 600])  # Default sizes
        
        layout.addWidget(splitter)
        return workspace
        
    def create_assistant_workspace(self):
        """Create a simple assistant workspace"""
        workspace = QWidget()
        layout = QVBoxLayout(workspace)
        
        # Add content view
        content_label = QLabel("Assistant workspace")
        content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(content_label)
        return workspace
        
    def _handle_tab_close_request(self, index):
        """Handle tab close request by removing the tab and cleaning up resources"""
        widget = self.agent_tabs.widget(index)
        
        # Find agent type for this widget
        agent_type = None
        for key, value in self.agents.items():
            if value == widget:
                agent_type = key
                break
                
        if agent_type:
            # Remove from agents dict
            del self.agents[agent_type]
            
            # Schedule agent termination using a thread to avoid blocking UI
            threading.Thread(
                target=self._terminate_agent_thread,
                args=(agent_type,),
                daemon=True
            ).start()
        
        # Remove tab
        self.agent_tabs.removeTab(index)
        
    async def close_agent_tab(self, index):
        """Close an agent tab and clean up resources"""
        widget = self.agent_tabs.widget(index)
        
        # Find agent type for this widget
        agent_type = None
        for key, value in self.agents.items():
            if value == widget:
                agent_type = key
                break
                
        if agent_type:
            # Remove from agents dict
            del self.agents[agent_type]
            
            # Schedule agent termination asynchronously
            asyncio.create_task(self._terminate_agent(agent_type))
        
        # Remove tab
        self.agent_tabs.removeTab(index)  # Changed to synchronous call

    async def _terminate_agent(self, agent_type):
        """Async helper to terminate an agent"""
        await self.core_controller.agent_manager.terminate_agent(agent_type)
        
    def _terminate_agent_thread(self, agent_type):
        """Run the async terminate_agent method in a new event loop"""
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run the async method in the new loop
            loop.run_until_complete(self._terminate_agent(agent_type))
        finally:
            # Clean up
            loop.close()
        
    def terminate_all_agents(self):
        """Terminate all active agents synchronously"""
        # Create a thread to handle the async termination
        if self.agents:
            thread = threading.Thread(
                target=self._terminate_all_agents_thread,
                daemon=True
            )
            thread.start()
            # Wait for the thread to complete to ensure clean shutdown
            thread.join()
    
    def _terminate_all_agents_thread(self):
        """Helper method to terminate all agents in a separate thread"""
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run the async termination in the new loop
            loop.run_until_complete(self._terminate_all_agents_async())
        finally:
            # Clean up
            loop.close()
    
    async def _terminate_all_agents_async(self):
        """Async implementation of terminating all agents"""
        for agent_type in list(self.agents.keys()):
            await self.core_controller.agent_manager.terminate_agent(agent_type)
        
    def _setup_terminal(self):
        """Set up the terminal component."""
        self.terminal_container = QWidget()
        layout = QVBoxLayout(self.terminal_container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.shell = Shell(agent_controller=None)  # Not connecting to agent_controller directly
        layout.addWidget(self.shell)
        
        # Connect shell signals to our methods
        self.shell.command_executed.connect(self.handle_shell_command)
        
        # Initialize the shell with current directory
        current_dir = os.getcwd()
        self.shell.set_prompt(f"{current_dir}> ")
        
    def handle_shell_command(self, command):
        """Handle shell command execution via the ComputerAgent."""
        self.shell.set_executing(True)
        
        # Update the prompt before executing the command
        current_dir = self.computer_agent.current_directory if hasattr(self.computer_agent, 'current_directory') else os.getcwd()
        self.shell.set_prompt(f"{current_dir}> ")
        
        # Start a new thread for command execution to prevent GUI freezing
        command_thread = threading.Thread(
            target=self._execute_command_thread,
            args=(command,)
        )
        command_thread.daemon = True
        command_thread.start()
    
    def _execute_command_thread(self, command):
        """Execute the command in a separate thread."""
        try:
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Execute the command
            result = loop.run_until_complete(self.computer_agent.process({
                "action": "execute_command",
                "command": command
            }))
            
            # Post the result back to the main thread
            QApplication.postEvent(self, CommandCompletedEvent(result))
            
        except Exception as e:
            # Post error back to the main thread
            QApplication.postEvent(self, CommandCompletedEvent(f"Error: {str(e)}"))
        finally:
            loop.close()
    
    def event(self, event):
        """Handle custom events."""
        if event.type() == CommandCompletedEvent.EVENT_TYPE:
            # Display the command result in the shell
            self.shell.display_result(event.result)
            self.shell.set_executing(False)
            return True
        return super().event(event)