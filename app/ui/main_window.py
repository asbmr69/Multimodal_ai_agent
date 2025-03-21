# app/ui/main_window.py
import sys
from PyQt6.QtWidgets import (QMainWindow, QSplitter, QWidget, QVBoxLayout, 
                            QHBoxLayout, QTabWidget, QStatusBar, QPushButton,
                            QToolBar, QLabel, QMenuBar, QMenu, QApplication)
from PyQt6.QtCore import Qt, pyqtSlot, QSize, pyqtSignal
from PyQt6.QtGui import QAction, QIcon

from .chat_widget import ChatWidget
from .agent_workspace import AgentWorkspace

class MainWindow(QMainWindow):
    def __init__(self, core_controller):
        super().__init__()
        
        self.core_controller = core_controller
        self.setWindowTitle("AI Agent Desktop")
        self.setMinimumSize(QSize(1200, 800))
        
        # Create status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create main splitter
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.main_splitter)
        
        # Create chat widget
        self.chat_widget = ChatWidget(self.core_controller)
        
        # Create agent workspace
        self.agent_workspace = AgentWorkspace(self.core_controller)
        
        # Add widgets to splitter
        self.main_splitter.addWidget(self.chat_widget)
        self.main_splitter.addWidget(self.agent_workspace)
        self.main_splitter.setSizes([300, 900])  # Default sizes
        
        # Connect signals
        self.chat_widget.agent_invoked.connect(self.agent_workspace.activate_agent)
        self.agent_workspace.status_message.connect(self.update_status)
        
    def create_menu_bar(self):
        menu_bar = QMenuBar()
        self.setMenuBar(menu_bar)
        
        # File menu
        file_menu = QMenu("File", self)
        menu_bar.addMenu(file_menu)
        
        new_chat_action = QAction("New Chat", self)
        new_chat_action.triggered.connect(self.new_chat)
        file_menu.addAction(new_chat_action)
        
        save_chat_action = QAction("Save Chat", self)
        save_chat_action.triggered.connect(self.save_chat)
        file_menu.addAction(save_chat_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Agents menu
        agents_menu = QMenu("Agents", self)
        menu_bar.addMenu(agents_menu)
        
        coder_action = QAction("Coder Agent", self)
        coder_action.triggered.connect(lambda: self.activate_agent("coder"))
        agents_menu.addAction(coder_action)
        
        computer_action = QAction("Computer Agent", self)
        computer_action.triggered.connect(lambda: self.activate_agent("computer"))
        agents_menu.addAction(computer_action)
        
        assistant_action = QAction("Assistant Agent", self)
        assistant_action.triggered.connect(lambda: self.activate_agent("assistant"))
        agents_menu.addAction(assistant_action)
        
        # Settings menu
        settings_menu = QMenu("Settings", self)
        menu_bar.addMenu(settings_menu)
        
        preferences_action = QAction("Preferences", self)
        preferences_action.triggered.connect(self.show_preferences)
        settings_menu.addAction(preferences_action)
        
    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Add agent buttons
        coder_button = QPushButton("Coder")
        coder_button.clicked.connect(lambda: self.activate_agent("coder"))
        toolbar.addWidget(coder_button)
        
        computer_button = QPushButton("Computer")
        computer_button.clicked.connect(lambda: self.activate_agent("computer"))
        toolbar.addWidget(computer_button)
        
        assistant_button = QPushButton("Assistant")
        assistant_button.clicked.connect(lambda: self.activate_agent("assistant"))
        toolbar.addWidget(assistant_button)
        
        toolbar.addSeparator()
        
        # Add layout control buttons
        layout_label = QLabel("Layout:")
        toolbar.addWidget(layout_label)
        
        split_horizontal_button = QPushButton("Horizontal Split")
        split_horizontal_button.clicked.connect(self.set_horizontal_layout)
        toolbar.addWidget(split_horizontal_button)
        
        split_vertical_button = QPushButton("Vertical Split")
        split_vertical_button.clicked.connect(self.set_vertical_layout)
        toolbar.addWidget(split_vertical_button)
        
    def new_chat(self):
        self.chat_widget.clear_chat()
        self.statusBar.showMessage("New chat started")
        
    def save_chat(self):
        self.chat_widget.save_chat()
        self.statusBar.showMessage("Chat saved")
        
    def activate_agent(self, agent_type):
        self.agent_workspace.activate_agent(agent_type)
        self.statusBar.showMessage(f"{agent_type.capitalize()} agent activated")
        
    def show_preferences(self):
        # This would show a preferences dialog
        self.statusBar.showMessage("Preferences dialog would show here")
        
    def set_horizontal_layout(self):
        self.main_splitter.setOrientation(Qt.Orientation.Horizontal)
        self.statusBar.showMessage("Horizontal layout set")
        
    def set_vertical_layout(self):
        self.main_splitter.setOrientation(Qt.Orientation.Vertical)
        self.statusBar.showMessage("Vertical layout set")
        
    @pyqtSlot(str)
    def update_status(self, message):
        self.statusBar.showMessage(message)
        
    def closeEvent(self, event):
        """Handle application shutdown"""
        # Clean up and terminate all agents
        self.agent_workspace.terminate_all_agents()
        event.accept()