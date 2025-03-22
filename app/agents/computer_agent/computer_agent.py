import os
import asyncio
import subprocess
from typing import Dict, Any, List, Optional
import shutil

from agents.base_agent import BaseAgent

class ComputerAgent(BaseAgent):
    @property
    def agent_type(self):
        """Return the type identifier for this agent."""
        return "computer"
    
    @property
    def capabilities(self):
        """Return a list of capabilities provided by this agent."""
        return ["file_operations", "shell_execution", "task_automation"]
    
    async def initialize(self) -> None:
        self.processes = []
        self.base_directory = os.path.expanduser("~")
        self.current_directory = self.base_directory
        
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        action = context.get("action", "execute_command")
        
        if action == "execute_command":
            command = context.get("command", "")
            result = await self._execute_shell_command(command)
            return {
                "content": f"Command executed:\n\n```\n{result}\n```",
                "workspace_update": {
                    "type": "shell_result",
                    "result": result,
                    "current_directory": self.current_directory
                }
            }
            
        elif action == "list_files":
            path = context.get("path", self.current_directory)
            files = await self._list_files(path)
            return {
                "content": f"Files in {path}:\n\n{files}",
                "workspace_update": {
                    "type": "file_list",
                    "path": path,
                    "files": files
                }
            }
            
        elif action == "read_file":
            path = context.get("path", "")
            content = await self._read_file(path)
            return {
                "content": f"Content of {path}:\n\n```\n{content}\n```",
                "workspace_update": {
                    "type": "file_content",
                    "path": path,
                    "content": content
                }
            }
            
        return {"content": "Unsupported action"}
    
    async def _execute_shell_command(self, command: str) -> str:
        if not command:
            return "No command provided"
            
        # Security check - prevent potentially harmful commands
        forbidden_commands = ["rm -rf", "format", "del /f", "deltree"]
        if any(cmd in command.lower() for cmd in forbidden_commands):
            return "Command rejected for security reasons"
        
        try:
            # Handle 'cd' command differently since it needs to change our internal state
            if command.strip().startswith("cd "):
                new_dir = command.strip()[3:].strip()
                
                # Handle home directory shortcut
                if new_dir == "~" or new_dir.startswith("~/"):
                    home = os.path.expanduser("~")
                    new_dir = home if new_dir == "~" else os.path.join(home, new_dir[2:])
                
                # Handle parent directory
                elif new_dir == "..":
                    new_dir = os.path.dirname(self.current_directory)
                
                # Handle absolute path
                elif os.path.isabs(new_dir):
                    pass  # Keep as is
                
                # Handle relative path
                else:
                    new_dir = os.path.join(self.current_directory, new_dir)
                
                # Check if directory exists
                if os.path.isdir(new_dir):
                    old_dir = self.current_directory
                    self.current_directory = os.path.normpath(new_dir)
                    return f"Changed directory from {old_dir} to {self.current_directory}"
                else:
                    return f"Error: Directory not found: {new_dir}"
            
            # For Windows, we need to use shell=True to properly execute commands
            # but this has security implications
            use_shell = os.name == 'nt'
            
            # Choose the right shell based on OS
            if os.name == 'nt':
                # On Windows, use cmd.exe
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=self.current_directory,
                    shell=True
                )
            else:
                # On Unix-like systems, we can use the command directly
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=self.current_directory
                )
            
            self.processes.append(process)
            stdout, stderr = await process.communicate()
            
            stdout_str = stdout.decode('utf-8', errors='replace') if stdout else ""
            stderr_str = stderr.decode('utf-8', errors='replace') if stderr else ""
            
            # For commands like 'dir' on Windows or 'ls' on Unix, ensure we get output
            if process.returncode == 0:
                return stdout_str if stdout_str else "Command executed successfully (no output)"
            else:
                return f"Error (code {process.returncode}):\n{stderr_str}"
                
        except Exception as e:
            return f"Execution error: {str(e)}"
    
    async def _list_files(self, path: str) -> List[Dict[str, Any]]:
        try:
            if not os.path.isabs(path):
                path = os.path.join(self.current_directory, path)
                
            if not os.path.exists(path):
                return [{"error": f"Path does not exist: {path}"}]
                
            files = []
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                stats = os.stat(item_path)
                
                files.append({
                    "name": item,
                    "path": item_path,
                    "size": stats.st_size,
                    "modified": stats.st_mtime,
                    "is_directory": os.path.isdir(item_path)
                })
                
            return files
            
        except Exception as e:
            return [{"error": f"Failed to list files: {str(e)}"}]
    
    async def _read_file(self, path: str) -> str:
        try:
            if not os.path.isabs(path):
                path = os.path.join(self.current_directory, path)
                
            if not os.path.exists(path):
                return f"File does not exist: {path}"
                
            if os.path.isdir(path):
                return f"{path} is a directory, not a file"
                
            # Limit file size to prevent memory issues
            if os.path.getsize(path) > 1024 * 1024:  # 1MB
                return f"File too large to read entirely. First 1MB:\n\n{open(path, 'r', errors='replace').read(1024*1024)}"
                
            return open(path, 'r', errors='replace').read()
            
        except Exception as e:
            return f"Failed to read file: {str(e)}"
    
    async def cleanup(self):
        """Clean up resources used by the agent."""
        # Terminate any running processes
        for process in self.processes:
            try:
                process.terminate()
            except:
                pass
        self.processes = []
        return {"status": "cleaned up"}
    
    def get_ui_components(self):
        """Get UI components for this agent."""
        # This agent doesn't provide UI components directly
        return []
    
    async def handle_ui_event(self, event_type, payload):
        """Handle UI events specific to this agent."""
        # This agent doesn't handle UI events directly
        return {"status": "event ignored"}