# app/ui/shell.py
import os
from typing import Optional, Callable

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, 
                             QLineEdit, QHBoxLayout, QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QProcess
from PyQt6.QtGui import QFont, QColor, QTextCursor

class Shell(QWidget):
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