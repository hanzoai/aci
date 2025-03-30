"""Claude Code integration for Hanzo ACI.

This module provides an implementation of the computer interface that uses Claude Code
to interact with the computer.
"""

import os
import asyncio
import logging
import json
import subprocess
from typing import Dict, List, Optional, Any, Union

from hanzo_aci.interface import ComputerInterface

logger = logging.getLogger(__name__)


class ClaudeCodeInterface(ComputerInterface):
    """Claude Code implementation of the computer interface.
    
    This implementation uses the Claude Code command-line tool to interact with
    the computer through its tool execution mechanism.
    """
    
    def __init__(self, claude_code_path: Optional[str] = None):
        """Initialize the Claude Code interface.
        
        Args:
            claude_code_path: Optional path to the Claude Code executable.
                If not provided, it will attempt to find it on the PATH.
        """
        self.claude_code_path = claude_code_path or self._find_executable()
        self._available = self.claude_code_path is not None
    
    def _find_executable(self) -> Optional[str]:
        """Find the Claude Code executable on the PATH."""
        try:
            # Try to find the executable
            result = subprocess.run(
                ["which", "claude"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                return result.stdout.strip()
            
            # On Windows, try 'where' instead of 'which'
            if os.name == 'nt':
                result = subprocess.run(
                    ["where", "claude"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if result.returncode == 0:
                    return result.stdout.strip().splitlines()[0]
            
            return None
        except Exception as e:
            logger.warning(f"Error finding Claude Code executable: {str(e)}")
            return None
    
    async def is_available(self) -> bool:
        """Check if Claude Code is available.
        
        Returns:
            True if Claude Code is available, False otherwise
        """
        return self._available
    
    async def ensure_running(self) -> Dict[str, Any]:
        """Ensure that Claude Code is ready to use.
        
        Claude Code doesn't run as a server, so this just checks if it's available.
        
        Returns:
            Dictionary with status information
        """
        if not self._available:
            return {
                "success": False,
                "error": "Claude Code is not available. Please install it first."
            }
        
        return {
            "success": True,
            "message": "Claude Code is available."
        }
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get information about the Claude Code capabilities.
        
        Returns:
            Dictionary with information about available tools
        """
        if not self._available:
            return {
                "available": False,
                "message": "Claude Code is not available. Please install it first."
            }
        
        # Get the available tools
        # Since Claude Code doesn't have an API to list tools,
        # we'll return a predefined list based on documentation
        tools = [
            {
                "name": "FileReadTool",
                "description": "Reads the contents of files"
            },
            {
                "name": "FileWriteTool",
                "description": "Creates or overwrites files"
            },
            {
                "name": "FileEditTool",
                "description": "Makes targeted edits to specific files"
            },
            {
                "name": "LSTool",
                "description": "Lists files and directories"
            },
            {
                "name": "GrepTool",
                "description": "Searches for patterns in file contents"
            },
            {
                "name": "BashTool",
                "description": "Executes shell commands"
            }
        ]
        
        return {
            "available": True,
            "tools": tools
        }
    
    async def execute_operation(
        self,
        operation: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an operation using Claude Code.
        
        Args:
            operation: Operation to execute
            params: Parameters for the operation
            
        Returns:
            Operation result
        """
        if not self._available:
            return {
                "success": False,
                "error": "Claude Code is not available. Please install it first."
            }
        
        # Map our operations to Claude Code commands
        operation_map = {
            "list_files": self._execute_list_files,
            "read_file": self._execute_read_file,
            "write_file": self._execute_write_file,
            "take_screenshot": self._execute_screenshot,
            "run_command": self._execute_command,
            "clipboard_get": self._execute_clipboard_get,
            "clipboard_set": self._execute_clipboard_set,
            "open_application": self._execute_open_application,
            "file_explorer": self._execute_file_explorer
        }
        
        # Check if the operation is supported
        if operation not in operation_map:
            return {
                "success": False,
                "error": f"Operation not supported: {operation}"
            }
        
        # Execute the operation
        return await operation_map[operation](params)
    
    async def _execute_claude_code(self, command: str) -> Dict[str, Any]:
        """Execute a command with Claude Code.
        
        Args:
            command: The command to execute
            
        Returns:
            The command result
        """
        try:
            cmd = [self.claude_code_path, "-p", command]
            
            # Run the command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Check for errors
            if process.returncode != 0:
                return {
                    "success": False,
                    "error": f"Command failed: {stderr.decode()}"
                }
            
            # Parse the output
            output = stdout.decode().strip()
            
            # Try to parse JSON if possible
            try:
                result = json.loads(output)
                return {
                    "success": True,
                    "data": result
                }
            except json.JSONDecodeError:
                # Return the raw output if it's not JSON
                return {
                    "success": True,
                    "data": output
                }
        except Exception as e:
            logger.error(f"Error executing Claude Code command: {str(e)}")
            return {
                "success": False,
                "error": f"Error executing command: {str(e)}"
            }
    
    async def _execute_list_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List files in a directory using Claude Code."""
        path = params.get("path", ".")
        command = f"list files in {path}"
        return await self._execute_claude_code(command)
    
    async def _execute_read_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read a file using Claude Code."""
        path = params.get("path")
        if not path:
            return {
                "success": False,
                "error": "Path is required for read_file operation"
            }
        command = f"read file {path}"
        return await self._execute_claude_code(command)
    
    async def _execute_write_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Write to a file using Claude Code."""
        path = params.get("path")
        content = params.get("content")
        if not path or content is None:
            return {
                "success": False,
                "error": "Path and content are required for write_file operation"
            }
        # Writing files is more complex, we need to use a temporary file
        temp_file = f"/tmp/claude_code_temp_{os.getpid()}.txt"
        with open(temp_file, "w") as f:
            f.write(content)
        command = f"write the contents of {temp_file} to {path}"
        result = await self._execute_claude_code(command)
        # Clean up the temporary file
        try:
            os.remove(temp_file)
        except:
            pass
        return result
    
    async def _execute_screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Take a screenshot using Claude Code."""
        command = "take a screenshot"
        return await self._execute_claude_code(command)
    
    async def _execute_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a shell command using Claude Code."""
        command = params.get("command")
        cwd = params.get("cwd")
        if not command:
            return {
                "success": False,
                "error": "Command is required for run_command operation"
            }
        claude_command = f"run the command: {command}"
        if cwd:
            claude_command += f" in directory {cwd}"
        return await self._execute_claude_code(claude_command)
    
    async def _execute_clipboard_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get clipboard contents using Claude Code."""
        command = "get the clipboard contents"
        return await self._execute_claude_code(command)
    
    async def _execute_clipboard_set(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set clipboard contents using Claude Code."""
        text = params.get("text")
        if text is None:
            return {
                "success": False,
                "error": "Text is required for clipboard_set operation"
            }
        # We need to use a temporary file for this
        temp_file = f"/tmp/claude_code_temp_{os.getpid()}.txt"
        with open(temp_file, "w") as f:
            f.write(text)
        command = f"set the clipboard to the contents of {temp_file}"
        result = await self._execute_claude_code(command)
        # Clean up the temporary file
        try:
            os.remove(temp_file)
        except:
            pass
        return result
    
    async def _execute_open_application(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Open an application using Claude Code."""
        app_name = params.get("name")
        if not app_name:
            return {
                "success": False,
                "error": "Application name is required for open_application operation"
            }
        command = f"open the application {app_name}"
        return await self._execute_claude_code(command)
    
    async def _execute_file_explorer(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Open file explorer using Claude Code."""
        path = params.get("path", ".")
        command = f"open file explorer at {path}"
        return await self._execute_claude_code(command)


# Create a singleton instance for convenience
claude_code_computer = ClaudeCodeInterface()
