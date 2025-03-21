# app/ui/chat_widget.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, 
                            QLineEdit, QPushButton, QHBoxLayout,
                            QSplitter, QLabel)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QTextCursor, QFont, QColor

class ChatWidget(QWidget):
    agent_invoked = pyqtSignal(str)  # Signal when agent is invoked
    
    def __init__(self, core_controller):
        super().__init__()
        self.core_controller = core_controller
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Chat history display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Segoe UI", 10))
        
        # User input area
        input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.returnPressed.connect(self.send_message)
        
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)
        
        # Assemble the layout
        layout.addWidget(QLabel("Chat"))
        layout.addWidget(self.chat_display)
        layout.addLayout(input_layout)
        
    async def send_message(self):
        """Send user message to the core controller"""
        message = self.message_input.text().strip()
        if not message:
            return
            
        # Display user message
        self.display_message("You", message, "user")
        self.message_input.clear()
        
        # Process with controller
        try:
            response = await self.core_controller.process_user_input(message)
            
            # Handle different response types
            if response["type"] == "agent_response":
                self.display_message(
                    f"AI ({response['agent_type']})", 
                    response["content"], 
                    "assistant"
                )
                # Emit signal to activate agent workspace
                self.agent_invoked.emit(response["agent_type"])
            else:
                self.display_message("AI", response["content"], "assistant")
                
        except Exception as e:
            self.display_message("System", f"Error processing message: {str(e)}", "error")
            
    def display_message(self, sender, content, message_type):
        """Display a message in the chat history"""
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Format based on message type
        if message_type == "user":
            sender_format = f"<span style='color:#0066cc; font-weight:bold;'>{sender}:</span>"
        elif message_type == "assistant":
            sender_format = f"<span style='color:#008800; font-weight:bold;'>{sender}:</span>"
        else:
            sender_format = f"<span style='color:#cc0000; font-weight:bold;'>{sender}:</span>"
            
        # Add message to display
        cursor.insertHtml(f"{sender_format} {content}<br><br>")
        
        # Scroll to bottom
        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()
        
    def clear_chat(self):
        """Clear the chat history"""
        self.chat_display.clear()
        
    def save_chat(self):
        """Save the chat history to a file"""
        # Implementation for saving chat history
        pass