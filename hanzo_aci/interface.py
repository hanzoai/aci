"""Core interface definition for Hanzo ACI.

This module defines the abstract base class for computer interface implementations.
It serves as the foundation for all interactions with the computer system.
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
    
    # Project Analysis
    
    async def analyze_project(self, project_dir: str) -> Dict[str, Any]:
        """Analyze a project directory structure and dependencies.
        
        Args:
            project_dir: Path to the project directory
            
        Returns:
            Dictionary with project analysis results
        """
        return await self.execute_operation(
            operation="analyze_project",
            params={"project_dir": project_dir}
        )
    
    # Vector Operations
    
    async def vector_search(self, query_text: str, project_dir: str, n_results: int = 10) -> Dict[str, Any]:
        """Search the vector store for similar content.
        
        Args:
            query_text: The text to search for
            project_dir: The project directory containing the vector store
            n_results: Maximum number of results to return
            
        Returns:
            Dictionary with search results
        """
        return await self.execute_operation(
            operation="vector_search",
            params={
                "query_text": query_text,
                "project_dir": project_dir,
                "n_results": n_results
            }
        )
    
    async def vector_index(self, path: str, recursive: bool = True) -> Dict[str, Any]:
        """Index a file or directory in the vector store.
        
        Args:
            path: Path to the file or directory to index
            recursive: Whether to recursively index directories
            
        Returns:
            Dictionary with indexing results
        """
        return await self.execute_operation(
            operation="vector_index",
            params={
                "path": path,
                "recursive": recursive
            }
        )
    
    # Symbol Operations
    
    async def symbol_find(self, path: str, symbol_name: Optional[str] = None) -> Dict[str, Any]:
        """Find symbols in a file or directory.
        
        Args:
            path: Path to file or directory
            symbol_name: Optional name of symbol to find
            
        Returns:
            Dictionary with found symbols
        """
        params = {"path": path}
        if symbol_name:
            params["symbol_name"] = symbol_name
        return await self.execute_operation(
            operation="symbol_find",
            params=params
        )
    
    async def symbol_search(self, pattern: str, path: str) -> Dict[str, Any]:
        """Search for symbols matching a pattern.
        
        Args:
            pattern: Pattern to search for
            path: Path to search in
            
        Returns:
            Dictionary with matching symbols
        """
        return await self.execute_operation(
            operation="symbol_search",
            params={
                "pattern": pattern,
                "path": path
            }
        )
    
    # Jupyter Operations
    
    async def jupyter_read(self, path: str) -> Dict[str, Any]:
        """Read a Jupyter notebook.
        
        Args:
            path: Path to the notebook
            
        Returns:
            Dictionary with notebook content
        """
        return await self.execute_operation(
            operation="jupyter_read",
            params={"path": path}
        )
    
    async def jupyter_edit(self, path: str, cell_number: int, new_source: str) -> Dict[str, Any]:
        """Edit a cell in a Jupyter notebook.
        
        Args:
            path: Path to the notebook
            cell_number: Number of the cell to edit
            new_source: New source code for the cell
            
        Returns:
            Dictionary with edit results
        """
        return await self.execute_operation(
            operation="jupyter_edit",
            params={
                "path": path,
                "cell_number": cell_number,
                "new_source": new_source
            }
        )
    
    # Browser Operations
    
    async def browser_navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to a URL in the browser.
        
        Args:
            url: URL to navigate to
            
        Returns:
            Dictionary with navigation results
        """
        return await self.execute_operation(
            operation="browser_navigate",
            params={"url": url}
        )
    
    async def browser_screenshot(self) -> Dict[str, Any]:
        """Take a screenshot of the browser window.
        
        Returns:
            Dictionary with screenshot results
        """
        return await self.execute_operation(
            operation="browser_screenshot",
            params={}
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
