import sys
import logging
from controller.app_controller import AppController
from ui.main_window import MainWindow
from PyQt6.QtWidgets import QApplication

def setup_logging():
    """Configure application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("app.log"),
            logging.StreamHandler()
        ]
    )

def main():
    """Application entry point."""
    # Set up logging
    setup_logging()
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("AI Agent Desktop")
    
    # Initialize the application controller
    controller = AppController()
    
    # Initialize UI
    window = MainWindow(controller)
    window.show()
    
    # Start the event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()