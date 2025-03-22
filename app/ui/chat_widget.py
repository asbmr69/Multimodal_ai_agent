# app/ui/chat_widget.py
import asyncio
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, 
                            QLineEdit, QPushButton, QHBoxLayout,
                            QSplitter, QLabel, QProgressBar, QMenu,
                            QToolButton, QFrame, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer
from PyQt6.QtGui import QTextCursor, QFont, QColor, QIcon, QAction
import threading

class ChatWidget(QWidget):
    agent_invoked = pyqtSignal(str)  # Signal when agent is invoked
    
    def __init__(self, core_controller):
        super().__init__()
        self.core_controller = core_controller
        self.loading = False
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Header with title and options
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Chat")
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        
        # Model selector combobox
        self.model_selector = QComboBox()
        self.model_selector.setToolTip("Select LLM Model")
        self.model_selector.addItems(["gpt-4", "gpt-3.5-turbo", "claude-3-opus", "gemini-pro"])
        self.model_selector.setCurrentIndex(0)
        self.model_selector.currentTextChanged.connect(self.set_model)
        
        # Action buttons
        self.clear_button = QPushButton("Clear Chat")
        self.clear_button.setToolTip("Clear chat history")
        self.clear_button.clicked.connect(self.clear_chat)
        
        self.save_button = QPushButton("Save Chat")
        self.save_button.setToolTip("Save chat history to file")
        self.save_button.clicked.connect(self.save_chat)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.model_selector)
        header_layout.addWidget(self.clear_button)
        header_layout.addWidget(self.save_button)
        
        layout.addLayout(header_layout)
        
        # Chat history display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Segoe UI", 10))
        self.chat_display.setStyleSheet("background-color: white; border: 1px solid #E0E0E0; border-radius: 4px;")
        layout.addWidget(self.chat_display)
        
        # Loading indicator
        self.loading_bar = QProgressBar()
        self.loading_bar.setRange(0, 0)  # Indeterminate progress
        self.loading_bar.setTextVisible(False)
        self.loading_bar.setFixedHeight(3)
        self.loading_bar.setStyleSheet("QProgressBar {background-color: transparent; border: none;} QProgressBar::chunk {background-color: #2196F3;}")
        self.loading_bar.hide()
        layout.addWidget(self.loading_bar)
        
        # Input area
        input_layout = QHBoxLayout()
        
        # Message input field
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.setFont(QFont("Segoe UI", 10))
        self.message_input.setStyleSheet("border: 1px solid #E0E0E0; border-radius: 4px; padding: 8px;")
        
        # Send button
        self.send_button = QPushButton("Send")
        self.send_button.setDefault(True)
        self.send_button.setStyleSheet("background-color: #2196F3; color: white; border-radius: 4px;")
        
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)
        
        layout.addLayout(input_layout)
        
        # Welcome message
        self._display_system_message("Welcome! How can I help you today?")
        
    def connect_signals(self):
        """Connect widget signals to slots"""
        self.send_button.clicked.connect(self.send_message_clicked)
        self.message_input.returnPressed.connect(self.send_message_clicked)
        
        # Connect to event manager for LLM status updates
        self.core_controller.event_manager.subscribe("llm_request_start", self.on_llm_request_start)
        self.core_controller.event_manager.subscribe("llm_request_complete", self.on_llm_request_complete)
        self.core_controller.event_manager.subscribe("llm_error", self.on_llm_error)
        
        # Setup thread signals
        self._setup_thread_signals()
        
    def set_model(self, model_name):
        """Change the LLM model"""
        # This would update app configuration in practice
        self._display_system_message(f"Switched to model: {model_name}")
        
    def invoke_agent(self, agent_type):
        """Explicitly invoke a specific agent"""
        self._display_system_message(f"Invoking {agent_type} agent...")
        self.agent_invoked.emit(agent_type)
        
    @pyqtSlot(str, dict)
    def on_llm_request_start(self, event_type, data):
        """Handle LLM request start event"""
        self.loading = True
        self.loading_bar.show()
        self.send_button.setEnabled(False)
        self.send_button.setText("Processing...")
        
    @pyqtSlot(str, dict)
    def on_llm_request_complete(self, event_type, data):
        """Handle LLM request complete event"""
        self.loading = False
        self.loading_bar.hide()
        self.send_button.setEnabled(True)
        self.send_button.setText("Send")
        
    @pyqtSlot(str, dict)
    def on_llm_error(self, event_type, data):
        """Handle LLM error event"""
        self.loading = False
        self.loading_bar.hide()
        self.send_button.setEnabled(True)
        self.send_button.setText("Send")
        self._display_system_message(f"Error: {data.get('error', 'Unknown error')}", error=True)
        
    def send_message_clicked(self):
        """Trigger sending a message"""
        if not self.loading:
            message = self.message_input.text().strip()
            if message:
                # Store the message and clear input immediately for better UX
                self.user_message = message
                self.message_input.clear()
                
                # Display user message right away
                self.display_message("You", message, "user")
                
                # Start processing in a separate thread
                threading.Thread(target=self._process_message_thread, args=(message,), daemon=True).start()
                
                # Set loading state
                self.loading = True
                self.loading_bar.show()
                self.send_button.setEnabled(False)
                self.send_button.setText("Processing...")
    
    def _process_message_thread(self, message):
        """Process message in a separate thread and update UI when done"""
        try:
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Process the message
            response = loop.run_until_complete(self.core_controller.process_user_input(message))
            
            # Update UI in the main thread
            self._handle_response(response)
        except Exception as e:
            # Handle errors
            self._handle_error(str(e))
        finally:
            # Clean up
            loop.close()
    
    def _handle_response(self, response):
        """Handle the response in the main thread"""
        # Use Qt's thread-safe signal/slot to update UI from a different thread
        if response["type"] == "agent_response":
            # Display LLM explanation
            self._safe_display_message("AI", response["content"], "assistant")
            
            # If there's agent-specific output, display it differently
            if "agent_result" in response:
                self._safe_display_message(
                    f"Agent ({response['agent_type']})",
                    response["agent_result"].get("content", "Task completed"),
                    "agent"
                )
                
            # Emit signal to activate agent workspace
            self.agent_invoked.emit(response["agent_type"])
            
        elif response["type"] == "direct_response":
            self._safe_display_message("AI", response["content"], "assistant")
            
        elif response["type"] == "error":
            self._safe_display_message("System", response["content"], "error")
        
        # Reset loading state
        self._reset_loading_state()
    
    def _handle_error(self, error_message):
        """Handle error in the main thread"""
        self._safe_display_message("System", f"Error processing message: {error_message}", "error")
        self._reset_loading_state()
    
    def _safe_display_message(self, sender, content, message_type):
        """Thread-safe version of display_message"""
        # Use QMetaObject.invokeMethod to call a method in the main thread from a secondary thread
        # Since that's complicated with PyQt6, we'll just use signals/slots
        self.display_message_signal.emit(sender, content, message_type)
    
    def _reset_loading_state(self):
        """Reset the loading state in the main thread"""
        self.loading = False
        self.loading_bar.hide()
        self.send_button.setEnabled(True)
        self.send_button.setText("Send")
    
    # Add these signals for thread-safe UI updates
    display_message_signal = pyqtSignal(str, str, str)
    reset_loading_signal = pyqtSignal()
    
    def _setup_thread_signals(self):
        """Connect the thread-safe signals to their slots"""
        self.display_message_signal.connect(self.display_message)
        self.reset_loading_signal.connect(self._do_reset_loading_state)
    
    def _do_reset_loading_state(self):
        """Actually reset the loading state (called in the main thread)"""
        self.loading = False
        self.loading_bar.hide()
        self.send_button.setEnabled(True)
        self.send_button.setText("Send")
        
    def display_message(self, sender, content, message_type):
        """Display a message in the chat history"""
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Format based on message type
        if message_type == "user":
            sender_format = f"<span style='color:#0066cc; font-weight:bold;'>{sender}:</span>"
            # Format code blocks in user messages
            content = self._format_code_blocks(content)
        elif message_type == "assistant":
            sender_format = f"<span style='color:#008800; font-weight:bold;'>{sender}:</span>"
            # Format code blocks, bullet points, etc.
            content = self._format_code_blocks(content)
            content = self._format_markdown_elements(content)
        elif message_type == "agent":
            sender_format = f"<span style='color:#9C27B0; font-weight:bold;'>{sender}:</span>"
            content = self._format_code_blocks(content)
        else:
            sender_format = f"<span style='color:#cc0000; font-weight:bold;'>{sender}:</span>"
            
        # Add message to display
        cursor.insertHtml(f"{sender_format} {content}<br><br>")
        
        # Scroll to bottom
        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()
        
    def _display_system_message(self, message, error=False):
        """Display a system message"""
        color = "#cc0000" if error else "#666666"
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(f"<span style='color:{color}; font-style:italic;'>{message}</span><br><br>")
        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()
        
    def _format_code_blocks(self, text):
        """Format code blocks in text"""
        # Very basic implementation - would be enhanced with proper regex
        if "```" in text:
            parts = text.split("```")
            formatted_text = parts[0]
            
            for i in range(1, len(parts)):
                if i % 2 == 1:  # Inside a code block
                    # Check for language identifier
                    code_parts = parts[i].split("\n", 1)
                    if len(code_parts) > 1:
                        language = code_parts[0].strip()
                        code = code_parts[1]
                        formatted_text += f"<pre style='background-color:#f0f0f0; padding:10px; border-radius:5px; font-family:monospace;'><code class='{language}'>{code}</code></pre>"
                    else:
                        formatted_text += f"<pre style='background-color:#f0f0f0; padding:10px; border-radius:5px; font-family:monospace;'><code>{parts[i]}</code></pre>"
                else:
                    formatted_text += parts[i]
                    
            return formatted_text
        return text
        
    def _format_markdown_elements(self, text):
        """Format basic markdown elements like bullet points, bold, etc."""
        # This is a very basic implementation
        lines = text.split('\n')
        
        for i in range(len(lines)):
            # Bold text
            line = lines[i]
            line = line.replace("**", "<b>", 1)
            if "**" in line:
                line = line.replace("**", "</b>", 1)
                
            # Bullet points
            if line.strip().startswith("- "):
                line = "• " + line.strip()[2:]
                
            lines[i] = line
            
        return "<br>".join(lines)
        
    def clear_chat(self):
        """Clear the chat history"""
        self.chat_display.clear()
        self._display_system_message("Chat history cleared.")
        # Clear conversation history in controller
        self.core_controller.clear_conversation()
        
    def save_chat(self):
        """Save the chat history to a file"""
        # Implementation for saving chat history
        self._display_system_message("Saving chat is not implemented yet.")