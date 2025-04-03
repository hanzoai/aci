"""Hanzo Dev integration for Hanzo ACI.

This module provides an implementation of the computer interface that uses the
Hanzo Dev tool to interact with the computer and provide advanced reasoning
capabilities.
"""

import os
import asyncio
import logging
import json
import importlib.util
from typing import Dict, List, Optional, Any, Union, Protocol

from hanzo_aci.interface import ComputerInterface

logger = logging.getLogger(__name__)


class DevManager:
    """Proxy for the Hanzo Dev manager.
    
    This is a minimal proxy to avoid direct dependency on the full dev package.
    """
    
    def __init__(self):
        """Initialize the Dev manager proxy."""
        self._available = False
        self._dev_module = None
        self._try_import_dev()
    
    def _try_import_dev(self):
        """Try to import the Dev module."""
        try:
            # First, try simple import
            import dev
            self._dev_module = dev
            self._available = True
        except ImportError:
            logger.debug("Simple import of dev failed, trying importlib")
            try:
                # Then try to locate the module using importlib
                spec = importlib.util.find_spec('dev')
                if spec is not None:
                    self._dev_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(self._dev_module)
                    self._available = True
                else:
                    logger.warning("Hanzo Dev module not found")
            except (ImportError, ModuleNotFoundError):
                logger.warning("Hanzo Dev not found. Some features may not be available.")
    
    @property
    def is_available(self) -> bool:
        """Check if the dev module is available."""
        return self._available and self._dev_module is not None
    
    def get_dev_module(self):
        """Get the dev module."""
        return self._dev_module
    
    async def initialize_dev(self) -> Dict[str, Any]:
        """Initialize the dev module.
        
        FIX: Changed to async method to match awaitable usage in the interface
        """
        if not self.is_available:
            return {"success": False, "error": "Dev module not available"}
        
        try:
            # Initialize dev components as needed
            # This will depend on the actual API of the dev module
            return {"success": True, "message": "Dev module initialized"}
        except Exception as e:
            logger.error(f"Error initializing dev: {str(e)}")
            return {"success": False, "error": f"Error initializing dev: {str(e)}"}


class DevComputerInterface(ComputerInterface):
    """Dev implementation of the computer interface."""
    
    def __init__(self, manager: Optional[DevManager] = None):
        """Initialize the Dev computer interface.
        
        Args:
            manager: Optional Dev manager. If not provided, a new one will be created.
        """
        self.manager = manager or DevManager()
        self.dev = None
        if self.manager.is_available:
            self.dev = self.manager.get_dev_module()
    
    async def is_available(self) -> bool:
        """Check if the Dev interface is available.
        
        Returns:
            True if the interface is available, False otherwise
        """
        return self.manager.is_available
    
    async def ensure_running(self) -> Dict[str, Any]:
        """Ensure that the Dev interface is running.
        
        Returns:
            Dictionary with status information
        """
        if not await self.is_available():
            return {
                "success": False,
                "error": "Dev module not available"
            }
            
        # FIX: Use await on initialize_dev (now an async method)
        return await self.manager.initialize_dev()
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get information about the Dev interface capabilities.
        
        Returns:
            Dictionary with information about available capabilities
        """
        if not await self.is_available():
            return {
                "available": False,
                "message": "Dev interface is not available on this system"
            }
            
        await self.ensure_running()
        
        # Get capabilities based on available dev components
        capabilities = {
            "available": True,
            "backend": "dev",
            "capabilities": {
                "filesystem": True,
                "vector": True,
                "symbols": True,
                "project": True,
                "runtime": True,
                "browser": True
            }
        }
        
        # Add version information if available
        if hasattr(self.dev, "__version__"):
            capabilities["version"] = self.dev.__version__
        
        return capabilities
    
    async def execute_operation(
        self,
        operation: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an operation using the Dev interface.
        
        Args:
            operation: Operation to execute
            params: Parameters for the operation
            
        Returns:
            Operation result
        """
        if not await self.is_available():
            return {
                "success": False,
                "error": "Dev module not available"
            }
            
        # Make sure the interface is running
        await self.ensure_running()
        
        # Map operations to dev functions
        operations_map = {
            # File operations
            "list_files": self._list_files,
            "read_file": self._read_file,
            "write_file": self._write_file,
            "edit_file": self._edit_file,
            "directory_tree": self._directory_tree,
            
            # Vector operations
            "vector_search": self._vector_search,
            "vector_index": self._vector_index,
            
            # Symbol operations
            "symbol_find": self._symbol_find,
            "symbol_search": self._symbol_search,
            
            # Project operations
            "analyze_project": self._analyze_project,
            
            # Runtime operations
            "run_command": self._run_command,
            "take_screenshot": self._take_screenshot,
            "clipboard_get": self._clipboard_get,
            "clipboard_set": self._clipboard_set,
            
            # Browser operations
            "browser_navigate": self._browser_navigate,
            "browser_screenshot": self._browser_screenshot,
        }
        
        if operation not in operations_map:
            return {
                "success": False,
                "error": f"Operation not supported: {operation}",
                "available_operations": list(operations_map.keys())
            }
            
        try:
            result = await operations_map[operation](params)
            return result
        except Exception as e:
            logger.error(f"Error executing operation: {str(e)}")
            return {
                "success": False,
                "error": f"Error executing operation: {str(e)}"
            }
    
    # File Operations
    
    async def _list_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List files in a directory."""
        path = params.get("path", ".")
        
        try:
            # Use the dev module's file operations
            # Implementation will depend on the actual API
            files = []
            directories = []
            
            # For now, fall back to os.listdir if dev doesn't have a specific function
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    directories.append(item)
                else:
                    files.append(item)
            
            return {
                "success": True,
                "files": files,
                "directories": directories
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _read_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read the contents of a file."""
        path = params.get("path")
        if not path:
            return {"success": False, "error": "Path is required"}
        
        try:
            # Use dev's file reading capabilities if available
            # Fall back to built-in open() if needed
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            return {
                "success": True,
                "content": content
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _write_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Write content to a file."""
        path = params.get("path")
        content = params.get("content")
        if not path or content is None:
            return {"success": False, "error": "Path and content are required"}
        
        try:
            # Use dev's file writing capabilities if available
            # Fall back to built-in open() if needed
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _edit_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Edit a file with line-based edits."""
        path = params.get("path")
        edits = params.get("edits")
        dry_run = params.get("dry_run", False)
        
        if not path or not edits:
            return {"success": False, "error": "Path and edits are required"}
        
        try:
            # Read the file
            read_result = await self._read_file({"path": path})
            if not read_result.get("success", False):
                return read_result
            
            content = read_result.get("content", "")
            
            # Apply edits
            for edit in edits:
                old_text = edit.get("oldText")
                new_text = edit.get("newText")
                if old_text is None or new_text is None:
                    return {"success": False, "error": "Each edit must have oldText and newText"}
                
                content = content.replace(old_text, new_text)
            
            # If dry run, just return the result
            if dry_run:
                return {"success": True, "content": content, "dry_run": True}
            
            # Write the file
            return await self._write_file({"path": path, "content": content})
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _directory_tree(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get a directory tree."""
        path = params.get("path", ".")
        depth = params.get("depth", 3)
        include_filtered = params.get("include_filtered", False)
        
        # Implement directory tree functionality
        # This is a placeholder implementation
        return {
            "success": True,
            "tree": f"Directory tree for {path} (depth={depth})"
        }
    
    # Vector Operations
    
    async def _vector_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search the vector store for similar content."""
        query_text = params.get("query_text")
        project_dir = params.get("project_dir")
        n_results = params.get("n_results", 10)
        
        if not query_text or not project_dir:
            return {"success": False, "error": "Query text and project directory are required"}
        
        # Implement vector search using dev capabilities
        # This is a placeholder implementation
        return {
            "success": True,
            "results": [
                {"source": "example.py", "content": "Example content", "similarity": 0.95}
            ]
        }
    
    async def _vector_index(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Index a file or directory in the vector store."""
        path = params.get("path")
        recursive = params.get("recursive", True)
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        # Implement vector indexing using dev capabilities
        # This is a placeholder implementation
        return {
            "success": True,
            "indexed_files": 5,
            "message": f"Indexed {path} (recursive={recursive})"
        }
    
    # Symbol Operations
    
    async def _symbol_find(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Find symbols in a file or directory."""
        path = params.get("path")
        symbol_name = params.get("symbol_name")
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        # Implement symbol finding using dev capabilities
        # This is a placeholder implementation
        return {
            "success": True,
            "symbols": [
                {"name": "example_function", "type": "function", "file": "example.py", "line": 10}
            ]
        }
    
    async def _symbol_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for symbols matching a pattern."""
        pattern = params.get("pattern")
        path = params.get("path")
        
        if not pattern or not path:
            return {"success": False, "error": "Pattern and path are required"}
        
        # Implement symbol search using dev capabilities
        # This is a placeholder implementation
        return {
            "success": True,
            "symbols": [
                {"name": "example_function", "type": "function", "file": "example.py", "line": 10}
            ]
        }
    
    # Project Operations
    
    async def _analyze_project(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a project directory structure and dependencies."""
        project_dir = params.get("project_dir")
        
        if not project_dir:
            return {"success": False, "error": "Project directory is required"}
        
        # Implement project analysis using dev capabilities
        # This is a placeholder implementation
        return {
            "success": True,
            "project": {
                "name": os.path.basename(project_dir),
                "files": 100,
                "lines": 5000,
                "languages": ["python", "typescript"]
            }
        }
    
    # Runtime Operations
    
    async def _run_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run a shell command."""
        command = params.get("command")
        cwd = params.get("cwd")
        
        if not command:
            return {"success": False, "error": "Command is required"}
        
        try:
            # Use asyncio.create_subprocess_shell for async command execution
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode("utf-8"),
                "stderr": stderr.decode("utf-8"),
                "returncode": process.returncode
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _take_screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Take a screenshot of the computer screen."""
        # Implement screenshot functionality using dev capabilities
        # This is a placeholder implementation
        return {
            "success": True,
            "screenshot_path": "/tmp/screenshot.png",
            "message": "Screenshot taken (placeholder)"
        }
    
    async def _clipboard_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get the current clipboard contents."""
        # Implement clipboard get functionality
        # This is a placeholder implementation
        return {
            "success": True,
            "content": "Clipboard content (placeholder)"
        }
    
    async def _clipboard_set(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set the clipboard contents."""
        text = params.get("text")
        
        if text is None:
            return {"success": False, "error": "Text is required"}
        
        # Implement clipboard set functionality
        # This is a placeholder implementation
        return {
            "success": True,
            "message": f"Clipboard set to: {text} (placeholder)"
        }
    
    # Browser Operations
    
    async def _browser_navigate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate to a URL in the browser."""
        url = params.get("url")
        
        if not url:
            return {"success": False, "error": "URL is required"}
        
        # Implement browser navigation using dev capabilities
        # This is a placeholder implementation
        return {
            "success": True,
            "message": f"Navigated to {url} (placeholder)"
        }
    
    async def _browser_screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Take a screenshot of the browser window."""
        # Implement browser screenshot using dev capabilities
        # This is a placeholder implementation
        return {
            "success": True,
            "screenshot_path": "/tmp/browser_screenshot.png",
            "message": "Browser screenshot taken (placeholder)"
        }


# Create a singleton instance for convenience
dev_computer = DevComputerInterface()