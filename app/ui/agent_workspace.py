# app/ui/agent_workspace.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, 
                            QSplitter, QStackedWidget, QLabel)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
import asyncio

from .components.code_editor import CodeEditor
from .components.terminal import Terminal, Shell
from .components.file_browser import FileExplorer

class AgentWorkspace(QWidget):
    status_message = pyqtSignal(str)
    
    def __init__(self, core_controller):
        super().__init__()
        self.core_controller = core_controller
        self.agents = {}  # Store active agent widgets
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
        self.agent_tabs.tabCloseRequested.connect(self.close_agent_tab)
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
        shell = Shell(agent_controller=self.handle_shell_command)
        
        # Add to splitter
        splitter.addWidget(file_explorer)
        splitter.addWidget(shell)
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
        self.agent_tabs.removeTab(index)

    async def _terminate_agent(self, agent_type):
        """Async helper to terminate an agent"""
        await self.core_controller.agent_manager.terminate_agent(agent_type)
        
    def terminate_all_agents(self):
        """Terminate all active agents"""
        for agent_type in list(self.agents.keys()):
            self.core_controller.agent_manager.terminate_agent(agent_type)
        
    def handle_shell_command(self, command):
        """Handle shell command execution through the computer agent"""
        self.status_message.emit(f"Executing: {command}")
        
        # Create context for agent
        context = {
            "action": "execute_command",
            "command": command
        }
        
        # Execute asynchronously through the computer agent
        async_task = asyncio.create_task(
            self.core_controller.agent_manager.invoke_agent("computer", context)
        )
        
        # Add callback to handle the response
        async_task.add_done_callback(self._on_command_executed)
    
    def _on_command_executed(self, future):
        """Handle completion of command execution"""
        try:
            result = future.result()
            
            # Find the shell widget to display the result
            if "computer" in self.agents:
                computer_tab = self.agents["computer"]
                # Find the shell within the tab's widget hierarchy
                shell = self._find_shell_widget(computer_tab)
                if shell:
                    # Display command result in the shell
                    workspace_update = result.get("workspace_update", {})
                    shell.display_result(workspace_update.get("result", "No output"))
                    
                    # Update current directory if changed
                    current_dir = workspace_update.get("current_directory")
                    if current_dir:
                        shell.set_current_directory(current_dir)
                
                # Update status
                self.status_message.emit("Command completed")
                
        except Exception as e:
            self.status_message.emit(f"Error executing command: {str(e)}")
    
    def _find_shell_widget(self, parent):
        """Find Shell widget in the widget hierarchy"""
        # Check if parent is the shell
        if isinstance(parent, Shell):
            return parent
            
        # Check children
        for child in parent.findChildren(Shell):
            return child
            
        # Check for QSplitter and look inside its widgets
        for splitter in parent.findChildren(QSplitter):
            for i in range(splitter.count()):
                widget = splitter.widget(i)
                if isinstance(widget, Shell):
                    return widget
                
                # Check inside this widget
                shell = self._find_shell_widget(widget)
                if shell:
                    return shell
        
        return None