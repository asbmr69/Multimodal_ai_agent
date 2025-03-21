import logging
import asyncio
import os
import tempfile
import subprocess
from pathlib import Path
#import typing
from typing import Any
from typing import List
from typing import Dict
from typing import Optional

from app.agents.base_agent import BaseAgent

class CoderAgent(BaseAgent):
    """Agent for code generation, editing, and execution."""
    
    def __init__(self, event_manager):
        self.logger = logging.getLogger(__name__)
        self.event_manager = event_manager
        self._working_dir = None
        self._execution_process = None
    
    @property
    def agent_type(self):
        return "coder"
    
    @property
    def capabilities(self):
        return [
            "code_generation",
            "code_execution",
            "code_explanation",
            "debugging",
            "file_editing"
        ]
    
    async def initialize(self):
        """Initialize the coder agent."""
        self.logger.info("Initializing coder agent")
        
        # Create a temporary working directory
        temp_dir = tempfile.mkdtemp(prefix="coder_agent_")
        self._working_dir = Path(temp_dir)
        
        self.logger.info(f"Created working directory: {self._working_dir}")
        
        # Notify that agent is initialized
        self.event_manager.emit("agent_initialized", self.agent_type)
    
    async def process(self, context):
        """Process a request for the coder agent."""
        prompt = context.get("prompt", "")
        action = context.get("action", "code_generation")
        
        self.logger.info(f"Processing coder agent request: {action}")
        
        if action == "code_generation":
            return await self._generate_code(prompt, context)
        elif action == "code_execution":
            code = context.get("code", "")
            language = context.get("language", "python")
            return await self._execute_code(code, language)
        elif action == "file_edit":
            file_path = context.get("file_path", "")
            content = context.get("content", "")
            return await self._edit_file(file_path, content)
        else:
            return {
                "status": "error",
                "message": f"Unknown action: {action}"
            }
    
    async def _generate_code(self, prompt, context):
        """Generate code based on the prompt."""
        # In a real implementation, this would call the LLM for code generation
        # For this example, we'll return a placeholder
        language = context.get("language", "python")
        
        # Placeholder code generation
        if language == "python":
            code = f"""
# Generated based on prompt: {prompt}
def main():
    print("Hello, World!")
    print("This is a sample function generated by the coder agent")
    
if __name__ == "__main__":
    main()
"""
        else:
            code = f"// Sample code for {language} based on: {prompt}"
        
        return {
            "status": "success",
            "code": code,
            "language": language,
            "message": "Code generated successfully"
        }
    
    async def _execute_code(self, code, language):
        """Execute the provided code."""
        if not code:
            return {
                "status": "error",
                "message": "No code provided for execution"
            }
        
        # Create a file for the code
        file_extension = self._get_file_extension(language)
        temp_file = self._working_dir / f"code{file_extension}"
        
        with open(temp_file, "w") as f:
            f.write(code)
        
        # Determine the command to run based on language
        command = self._get_execution_command(language, temp_file)
        
        # Execute the code
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self._working_dir)
            )
            
            self._execution_process = process
            stdout, stderr = await process.communicate()
            
            return {
                "status": "success" if process.returncode == 0 else "error",
                "stdout": stdout.decode(),
                "stderr": stderr.decode(),
                "return_code": process.returncode
            }
        except Exception as e:
            self.logger.error(f"Error executing code: {e}")
            return {
                "status": "error",
                "message": f"Error executing code: {str(e)}"
            }
    
    async def _edit_file(self, file_path, content):
        """Edit or create a file with the given content."""
        if not file_path:
            return {
                "status": "error",
                "message": "No file path provided"
            }
        
        try:
            full_path = self._working_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, "w") as f:
                f.write(content)
            
            return {
                "status": "success",
                "message": f"File {file_path} saved successfully",
                "file_path": str(full_path)
            }
        except Exception as e:
            self.logger.error(f"Error saving file: {e}")
            return {
                "status": "error",
                "message": f"Error saving file: {str(e)}"
            }
    
    def _get_file_extension(self, language):
        """Get the file extension for the given language."""
        extensions = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "java": ".java",
            "c": ".c",
            "cpp": ".cpp",
            "csharp": ".cs",
            "go": ".go",
            "rust": ".rs",
            "ruby": ".rb",
            "php": ".php",
            "swift": ".swift",
            "kotlin": ".kt"
        }
        return extensions.get(language.lower(), ".txt")
    
    def _get_execution_command(self, language: str, file_path: str) -> List[str]:
        commands = {
            "python": ["python", file_path],
            "javascript": ["node", file_path],
            "java": ["java", file_path],
        }
        return commands.get(language.lower(), ["echo", f"No execution support for {language}"])
    
    async def cleanup(self) -> None:
        # Terminate any running processes
        for process in self.processes:
            try:
                process.terminate()
                await process.wait()
            except:
                pass
        
        # Clean up temporary directory
        try:
            import shutil
            shutil.rmtree(self.working_dir, ignore_errors=True)
        except:
            pass
    
    def get_ui_components(self) -> Dict[str, Any]:
        from app.ui.components.code_editor import CodeEditor
        from app.ui.components.terminal import Terminal
        
        return {
            "main": CodeEditor,
            "secondary": Terminal,
            "layout": "vertical"
        }
    
    async def handle_ui_event(self, event: str, payload: Any) -> Optional[Dict[str, Any]]:
        if event == "execute_code":
            result = await self._execute_code(payload["code"], payload["language"])
            return {
                "type": "execution_result",
                "result": result
            }
        
        return None