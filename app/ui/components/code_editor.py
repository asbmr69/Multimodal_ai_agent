# app/ui/code_editor.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QComboBox, QTextEdit, QLabel,
                            QPushButton, QToolBar)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QSyntaxHighlighter, QTextCharFormat

class SyntaxHighlighter(QSyntaxHighlighter):
    """Basic syntax highlighter for code editor"""
    def __init__(self, document, language):
        super().__init__(document)
        self.language = language
        self.create_rules()
        
    def create_rules(self):
        """Create syntax highlighting rules based on language"""
        self.rules = []
        
        # Common formatting
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#0000FF"))
        keyword_format.setFontWeight(QFont.Weight.Bold)
        
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#008000"))
        
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#808080"))
        comment_format.setFontItalic(True)
        
        # Set up language-specific rules
        if self.language == "python":
            # Python keywords
            keywords = ["def", "class", "import", "from", "for", "while", 
                       "if", "elif", "else", "try", "except", "finally",
                       "with", "as", "return", "yield", "pass", "break",
                       "continue", "in", "is", "not", "and", "or"]
                       
            # Add keyword rules
            for word in keywords:
                pattern = r'\b' + word + r'\b'
                self.rules.append((pattern, keyword_format))
                
            # Add string rules
            self.rules.append((r'"[^"\\]*(\\.[^"\\]*)*"', string_format))
            self.rules.append((r"'[^'\\]*(\\.[^'\\]*)*'", string_format))
            
            # Add comment rule
            self.rules.append((r'#[^\n]*', comment_format))
        
        # Add more language rules as needed
    
    def highlightBlock(self, text):
        """Apply syntax highlighting to the given text block"""
        for pattern, format in self.rules:
            import re
            for match in re.finditer(pattern, text):
                start = match.start()
                length = match.end() - start
                self.setFormat(start, length, format)

class CodeEditor(QWidget):
    code_changed = pyqtSignal(str)
    execute_requested = pyqtSignal(str, str)  # code, language
    
    def __init__(self):
        super().__init__()
        self.language = "python"  # Default language
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Create toolbar
        toolbar = QToolBar()
        
        # Language selector
        lang_label = QLabel("Language:")
        toolbar.addWidget(lang_label)
        
        self.language_selector = QComboBox()
        self.language_selector.addItems(["python", "javascript", "java", "c", "cpp"])
        self.language_selector.currentTextChanged.connect(self.change_language)
        toolbar.addWidget(self.language_selector)
        
        toolbar.addSeparator()
        
        # Run button
        self.run_button = QPushButton("Run")
        self.run_button.clicked.connect(self.execute_code)
        toolbar.addWidget(self.run_button)
        
        # Editor widget
        self.editor = QTextEdit()
        self.editor.setFont(QFont("Courier New", 10))
        self.editor.textChanged.connect(self.on_text_changed)
        
        # Set up syntax highlighter
        self.highlighter = SyntaxHighlighter(self.editor.document(), self.language)
        
        # Add widgets to layout
        layout.addWidget(toolbar)
        layout.addWidget(self.editor)
        
    def change_language(self, language):
        """Change the editing language"""
        self.language = language
        # Update syntax highlighter
        self.highlighter = SyntaxHighlighter(self.editor.document(), language)
        self.highlighter.rehighlight()
        
    def set_language(self, language):
        """Set the language from external calls"""
        index = self.language_selector.findText(language)
        if index >= 0:
            self.language_selector.setCurrentIndex(index)
        
    def set_code(self, code):
        """Set the editor content"""
        self.editor.setText(code)
        
    def get_code(self):
        """Get the current code"""
        return self.editor.toPlainText()
        
    def on_text_changed(self):
        """Handle text changes"""
        self.code_changed.emit(self.get_code())
        
    def execute_code(self):
        """Execute the current code"""
        code = self.get_code()
        self.execute_requested.emit(code, self.language)