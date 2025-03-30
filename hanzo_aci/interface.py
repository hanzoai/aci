"""Core interface definition for Hanzo ACI.

This module defines the abstract base class for all computer interface implementations.
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union, Protocol
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ComputerInterface(ABC):
    """Abstract base class for computer interaction interfaces."""
    
    @abstractmethod
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get information about the computer's capabilities.
        
        Returns:
            Dictionary with information about available tools and operations
        """
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the computer interface is available.
        
        Returns:
            True if the interface is available, False otherwise
        """
        pass
    
    @abstractmethod
    async def ensure_running(self) -> Dict[str, Any]:
        """Ensure that the computer interface is running and ready.
        
        Returns:
            Dictionary with status information
        """
        pass
    
    @abstractmethod
    async def execute_operation(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific operation with parameters.
        
        Args:
            operation: Name of the operation to execute
            params: Parameters for the operation
            
        Returns:
            Dictionary with the operation result
        """
        pass
    
    # File System Operations
    
    async def list_files(self, path: str) -> Dict[str, Any]:
        """List files in a directory.
        
        Args:
            path: Directory path to list
            
        Returns:
            Dictionary with the list of files
        """
        return await self.execute_operation(
            operation="list_files",
            params={"path": path}
        )
    
    async def read_file(self, path: str) -> Dict[str, Any]:
        """Read the contents of a file.
        
        Args:
            path: Path to the file to read
            
        Returns:
            Dictionary with the file contents
        """
        return await self.execute_operation(
            operation="read_file",
            params={"path": path}
        )
    
    async def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write content to a file.
        
        Args:
            path: Path to the file to write
            content: Content to write to the file
            
        Returns:
            Dictionary with the result of the operation
        """
        return await self.execute_operation(
            operation="write_file",
            params={"path": path, "content": content}
        )
    
    # Application Control
    
    async def open_application(self, app_name: str) -> Dict[str, Any]:
        """Open an application on the computer.
        
        Args:
            app_name: Name of the application to open
            
        Returns:
            Dictionary with the result of the operation
        """
        return await self.execute_operation(
            operation="open_application",
            params={"name": app_name}
        )
    
    async def file_explorer(self, path: str) -> Dict[str, Any]:
        """Open the file explorer at a specific path.
        
        Args:
            path: Path to open in the file explorer
            
        Returns:
            Dictionary with the result of the operation
        """
        return await self.execute_operation(
            operation="file_explorer",
            params={"path": path}
        )
    
    # System Operations
    
    async def take_screenshot(self) -> Dict[str, Any]:
        """Take a screenshot of the computer screen.
        
        Returns:
            Dictionary with the path to the screenshot
        """
        return await self.execute_operation(
            operation="take_screenshot",
            params={}
        )
    
    async def clipboard_get(self) -> Dict[str, Any]:
        """Get the current clipboard contents.
        
        Returns:
            Dictionary with the clipboard contents
        """
        return await self.execute_operation(
            operation="clipboard_get",
            params={}
        )
    
    async def clipboard_set(self, text: str) -> Dict[str, Any]:
        """Set the clipboard contents.
        
        Args:
            text: Text to set in the clipboard
            
        Returns:
            Dictionary with the result of the operation
        """
        return await self.execute_operation(
            operation="clipboard_set",
            params={"text": text}
        )
    
    # Environment Operations
    
    async def get_environment_variables(self) -> Dict[str, Any]:
        """Get the current environment variables.
        
        Returns:
            Dictionary with the environment variables
        """
        return await self.execute_operation(
            operation="get_environment",
            params={}
        )
    
    async def run_command(self, command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        """Run a shell command.
        
        Args:
            command: Command to run
            cwd: Working directory for the command
            
        Returns:
            Dictionary with the command output
        """
        params = {"command": command}
        if cwd:
            params["cwd"] = cwd
        return await self.execute_operation(
            operation="run_command",
            params=params
        )
