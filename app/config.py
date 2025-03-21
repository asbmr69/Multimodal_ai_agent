import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

class Config:
    """Application configuration manager"""
    
    def __init__(self):
        self.app_dir = self._get_app_directory()
        self.config_file = self.app_dir / "config.json"
        self.settings = self._load_config()
        self._setup_logging()
        
    def _get_app_directory(self) -> Path:
        """Get or create application directory"""
        app_dir = Path.home() / "AIAgentApp"
        app_dir.mkdir(exist_ok=True)
        return app_dir
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if not self.config_file.exists():
            return self._create_default_config()
            
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return self._create_default_config()
            
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration"""
        default_config = {
            "app": {
                "name": "AI Agent Desktop",
                "theme": "light",
                "max_history": 100
            },
            "llm": {
                "provider": "openai",
                "model": "gpt-4o",
                "api_key": "",
                "anthropic_api_key": "",
                "gemini_api_key": "",
                "mistral_api_key": "",
                "deepseek_api_key": "",
                "temperature": 0.7,
                "models": {
                    "openai": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
                    "anthropic": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
                    "gemini": ["gemini-1.5-pro", "gemini-2.0-flash"],
                    "mistral": ["mistral-large", "mistral-medium", "mistral-small"],
                    "deepseek": ["deepseek-coder", "deepseek-chat"]
                }
            },
            "agents": {
                "coder": {
                    "enabled": True,
                    "languages": ["python", "javascript", "java", "c++"]
                },
                "computer": {
                    "enabled": True,
                    "allowed_directories": [
                        str(Path.home() / "Documents"),
                        str(Path.home() / "Downloads")
                    ],
                    "restricted_commands": ["rm -rf", "format", "del /f"]
                },
                "assistant": {
                    "enabled": True
                }
            },
            "ui": {
                "font_size": 12,
                "split_sizes": [30, 70],
                "editor_theme": "vs-dark"
            }
        }
        
        # Save default config
        self.save_config(default_config)
        return default_config
        
    def save_config(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Save configuration to file"""
        if config:
            self.settings = config
            
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
            
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        try:
            return self.settings.get(section, {}).get(key, default)
        except:
            return default
            
    def set(self, section: str, key: str, value: Any) -> None:
        """Set configuration value"""
        if section not in self.settings:
            self.settings[section] = {}
            
        self.settings[section][key] = value
        self.save_config()
        
    def _setup_logging(self) -> None:
        """Setup application logging"""
        log_dir = self.app_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / "app.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
# Global configuration instance
config = Config()