# app/ui/shell.py
import os
from typing import Optional, Callable

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, 
                             QLineEdit, QHBoxLayout, QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QProcess
from PyQt6.QtGui import QFont, QColor, QTextCursor

class Terminal(QWidget):
    """Terminal emulator widget for executing shell commands"""
    command_executed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_directory = os.path.expanduser("~")
        self.command_history = []
        self.history_index = 0
        
        self._init_ui()
        
    def _init_ui(self):
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Output display area
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setFont(QFont("Consolas", 10))
        self.output_area.setStyleSheet("background-color: #1E1E1E; color: #DCDCDC;")
        layout.addWidget(self.output_area)
        
        # Input area
        input_layout = QHBoxLayout()
        
        # Command prompt label
        self.prompt_label = QLineEdit()
        self.prompt_label.setReadOnly(True)
        self.prompt_label.setMaximumWidth(200)
        self.prompt_label.setFont(QFont("Consolas", 10))
        self.prompt_label.setStyleSheet("background-color: #1E1E1E; color: #569CD6; border: none;")
        self._update_prompt()
        
        # Command input field
        self.command_input = QLineEdit()
        self.command_input.setFont(QFont("Consolas", 10))
        self.command_input.setStyleSheet("background-color: #1E1E1E; color: #DCDCDC; border: none;")
        self.command_input.returnPressed.connect(self._execute_command)
        
        # Handle up/down keys for command history
        self.command_input.installEventFilter(self)
        
        # Execute button
        self.execute_button = QPushButton("Run")
        self.execute_button.setStyleSheet("background-color: #0E639C; color: white;")
        self.execute_button.clicked.connect(self._execute_command)
        
        input_layout.addWidget(self.prompt_label)
        input_layout.addWidget(self.command_input)
        input_layout.addWidget(self.execute_button)
        
        layout.addLayout(input_layout)
        
        # Welcome message
        self._append_output("Shell initialized. Type commands and press Enter to execute.\n", color="#569CD6")
        
    def _update_prompt(self):
        """Update command prompt with current directory"""
        user = os.environ.get('USERNAME', os.environ.get('USER', 'user'))
        host = os.environ.get('COMPUTERNAME', os.environ.get('HOSTNAME', 'localhost'))
        shortened_path = self.current_directory.replace(os.path.expanduser("~"), "~")
        self.prompt_label.setText(f"{user}@{host}:{shortened_path}$ ")
        
    def _execute_command(self):
        """Execute the command in the input field"""
        command = self.command_input.text().strip()
        if not command:
            return
            
        # Add to history
        self.command_history.append(command)
        self.history_index = len(self.command_history)
        
        # Display command
        self._append_output(f"{self.prompt_label.text()} {command}\n")
        
        # Clear input
        self.command_input.clear()
        
        # Emit signal for agent to handle
        self.command_executed.emit(command)
        
    def display_result(self, result: str, error: bool = False):
        """Display result of command execution"""
        if result:
            color = "#FF6B68" if error else "#DCDCDC"
            self._append_output(f"{result}\n", color)
            
    def set_current_directory(self, directory: str):
        """Update the current working directory"""
        self.current_directory = directory
        self._update_prompt()
        
    def _append_output(self, text: str, color: str = "#DCDCDC"):
        """Append text to output area with specified color"""
        cursor = self.output_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Apply text color
        format = cursor.charFormat()
        format.setForeground(QColor(color))
        cursor.setCharFormat(format)
        
        cursor.insertText(text)
        self.output_area.setTextCursor(cursor)
        self.output_area.ensureCursorVisible()
        
    def clear_output(self):
        """Clear the output area"""
        self.output_area.clear()
        
    def eventFilter(self, obj, event):
        """Handle up/down keys for command history"""
        if obj is self.command_input and event.type() == event.Type.KeyPress:
            key = event.key()
            
            if key == Qt.Key.Key_Up:
                # Navigate command history up
                if self.command_history and self.history_index > 0:
                    self.history_index -= 1
                    self.command_input.setText(self.command_history[self.history_index])
                return True
                
            elif key == Qt.Key.Key_Down:
                # Navigate command history down
                if self.command_history and self.history_index < len(self.command_history) - 1:
                    self.history_index += 1
                    self.command_input.setText(self.command_history[self.history_index])
                else:
                    self.history_index = len(self.command_history)
                    self.command_input.clear()
                return True
                
        return super().eventFilter(obj, event)
        
    def connect_to_agent(self, agent_handler: Callable):
        """Connect shell to agent handler function"""
        self.command_executed.connect(agent_handler)


class Shell(QWidget):
    """Interactive shell interface that connects to the computer agent."""
    
    command_executed = pyqtSignal(str)
    
    def __init__(self, parent=None, agent_controller=None):
        super().__init__(parent)
        self.agent_controller = agent_controller
        self.process = None
        self.current_directory = os.path.expanduser("~")
        self.environment_vars = dict(os.environ)
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Set up the Shell UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create the terminal component
        self.terminal = Terminal(self)
        layout.addWidget(self.terminal)
        
        # Add a status bar
        status_layout = QHBoxLayout()
        
        self.status_label = QLineEdit()
        self.status_label.setReadOnly(True)
        self.status_label.setStyleSheet("background-color: #007ACC; color: white; border: none;")
        self.status_label.setText("Ready")
        
        self.kill_button = QPushButton("Kill Process")
        self.kill_button.setStyleSheet("background-color: #C62828; color: white;")
        self.kill_button.clicked.connect(self._kill_current_process)
        self.kill_button.setEnabled(False)
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.kill_button)
        
        layout.addLayout(status_layout)
    
    def _connect_signals(self):
        """Connect signal handlers"""
        self.terminal.command_executed.connect(self._handle_command)
    
    def _handle_command(self, command):
        """Handle command execution"""
        # Special commands handling
        if command.lower() == "clear" or command.lower() == "cls":
            self.terminal.clear_output()
            return
        
        # If we have an agent controller, delegate to it
        if self.agent_controller:
            self._set_executing_state(True)
            # Create context for the computer agent
            context = {
                "action": "execute_command",
                "command": command,
                "current_directory": self.current_directory
            }
            
            # In a real implementation, this would be async
            # For simplicity, using a direct call pattern here
            self.command_executed.emit(command)
        else:
            # Fallback to local execution with QProcess
            self._execute_local_command(command)
    
    def _execute_local_command(self, command):
        """Execute command locally if no agent is available"""
        self._set_executing_state(True)
        
        # Create process
        self.process = QProcess()
        self.process.setWorkingDirectory(self.current_directory)
        
        # Set up environment
        process_env = self.process.processEnvironment()
        for key, value in self.environment_vars.items():
            process_env.insert(key, value)
        self.process.setProcessEnvironment(process_env)
        
        # Connect signals
        self.process.readyReadStandardOutput.connect(self._on_stdout_ready)
        self.process.readyReadStandardError.connect(self._on_stderr_ready)
        self.process.finished.connect(self._on_process_finished)
        
        # On Windows, use cmd.exe to execute the command
        if os.name == 'nt':
            self.process.start("cmd.exe", ["/c", command])
        else:
            # On Unix, use bash
            self.process.start("/bin/bash", ["-c", command])
    
    def _on_stdout_ready(self):
        """Handle standard output from process"""
        data = self.process.readAllStandardOutput().data().decode('utf-8', errors='replace')
        self.terminal.display_result(data)
    
    def _on_stderr_ready(self):
        """Handle standard error from process"""
        data = self.process.readAllStandardError().data().decode('utf-8', errors='replace')
        self.terminal.display_result(data, error=True)
    
    def _on_process_finished(self, exit_code, exit_status):
        """Handle process completion"""
        if exit_code != 0:
            self.terminal.display_result(f"Process exited with code {exit_code}", error=True)
        self._set_executing_state(False)
    
    def _set_executing_state(self, is_executing):
        """Update UI based on execution state"""
        self.kill_button.setEnabled(is_executing)
        self.status_label.setText("Executing..." if is_executing else "Ready")
        self.status_label.setStyleSheet(
            "background-color: #E65100; color: white; border: none;" if is_executing 
            else "background-color: #007ACC; color: white; border: none;"
        )
    
    def _kill_current_process(self):
        """Kill the currently running process"""
        if self.process and self.process.state() == QProcess.ProcessState.Running:
            self.process.kill()
            self.terminal.display_result("Process terminated by user", error=True)
            self._set_executing_state(False)
    
    def display_result(self, result, is_error=False):
        """Display result in the terminal"""
        self.terminal.display_result(result, error=is_error)
        self._set_executing_state(False)
    
    def set_current_directory(self, directory):
        """Update the current working directory"""
        if os.path.isdir(directory):
            self.current_directory = directory
            self.terminal.set_current_directory(directory)
    
    def connect_to_agent(self, agent_handler):
        """Connect shell to agent handler function"""
        self.agent_controller = agent_handler
        self.command_executed.connect(agent_handler)