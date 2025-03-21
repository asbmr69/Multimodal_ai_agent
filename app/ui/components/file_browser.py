# app/ui/file_browser.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTreeView, 
                           QFileSystemModel, QLabel, QLineEdit,
                           QPushButton, QHBoxLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QDir

class FileExplorer(QWidget):
    file_selected = pyqtSignal(str)
    directory_changed = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Path navigation
        path_layout = QHBoxLayout()
        
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Enter path")
        self.path_input.returnPressed.connect(self.navigate_to_path)
        
        self.go_button = QPushButton("Go")
        self.go_button.clicked.connect(self.navigate_to_path)
        
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.go_button)
        
        # File system model and view
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.homePath())
        
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.model)
        self.tree_view.setRootIndex(self.model.index(QDir.homePath()))
        self.tree_view.setAnimated(False)
        self.tree_view.setIndentation(20)
        self.tree_view.setSortingEnabled(True)
        
        # Show only filename column initially
        for i in range(1, self.model.columnCount()):
            self.tree_view.hideColumn(i)
            
        # Connect signals
        self.tree_view.clicked.connect(self.item_clicked)
        
        # Update path input with current dir
        self.path_input.setText(QDir.homePath())
        
        # Add widgets to layout
        layout.addLayout(path_layout)
        layout.addWidget(self.tree_view)
        
    def navigate_to_path(self):
        """Navigate to the specified path"""
        path = self.path_input.text()
        index = self.model.index(path)
        if index.isValid():
            self.tree_view.setRootIndex(index)
            self.directory_changed.emit(path)
            
    def item_clicked(self, index):
        """Handle item selection in the tree view"""
        path = self.model.filePath(index)
        self.file_selected.emit(path)
        
        # Update path input if directory
        if self.model.isDir(index):
            self.path_input.setText(path)
            self.directory_changed.emit(path)