import os
import asyncio
import subprocess
from typing import Dict, Any, List, Optional
import shutil

from agents.base_agent import BaseAgent

class ComputerAgent(BaseAgent):
    type = "computer"
    capabilities = ["file_operations", "shell_execution", "task_automation"]
    
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
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.current_directory
            )
            
            self.processes.append(process)
            stdout, stderr = await process.communicate()
            
            # Update current directory if command is cd
            if command.strip().startswith("cd "):
                new_dir = command.strip()[3:].strip()
                
                # Handle relative paths
                if not os.path.isabs(new_dir):
                    new_dir = os.path.join(self.current_directory, new_dir)
                
                if os.path.isdir(new_dir):
                    self.current_directory = os.path.normpath(new_dir)
            
            if process.returncode == 0:
                return stdout.decode() or "Command executed successfully"
            else:
                return f"Error: {stderr.decode()}"
                
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
    
    async def cleanup(self) -> None:
        # Terminate any running processes
        for process in self.processes:
            try:
                process.terminate()
                await process.wait()
            except:
                pass
    
    def get_ui_components(self) -> Dict[str, Any]:
        from app.ui.components.file_browser import FileExplorer
        from app.ui.components.terminal import Shell
        
        return {
            "main": FileExplorer,
            "secondary": Shell,
            "layout": "horizontal"
        }
    
    async def handle_ui_event(self, event: str, payload: Any) -> Optional[Dict[str, Any]]:
        if event == "execute_command":
            result = await self._execute_shell_command(payload["command"])
            return {
                "type": "shell_result",
                "result": result,
                "current_directory": self.current_directory
            }
            
        elif event == "navigate_directory":
            path = payload["path"]
            files = await self._list_files(path)
            
            if os.path.isdir(path):
                self.current_directory = path
                
            return {
                "type": "file_list",
                "path": path,
                "files": files,
                "current_directory": self.current_directory
            }
            
        elif event == "open_file":
            content = await self._read_file(payload["path"])
            return {
                "type": "file_content",
                "path": payload["path"],
                "content": content
            }
            
        return None