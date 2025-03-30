"""MCP integration for Hanzo ACI.

This module provides an implementation of the computer interface that uses the
Hanzo MCP server to interact with the computer.
"""

import os
import asyncio
import logging
import json
from typing import Dict, List, Optional, Any, Union, Protocol

from hanzo_aci.interface import ComputerInterface

logger = logging.getLogger(__name__)


class MCPServerManager:
    """Proxy for the Hanzo MCP ServerManager.
    
    This is a minimal proxy to avoid direct dependency on the full MCP package.
    In a real implementation, this would use hanzo_mcp.tools.mcp_manager.
    """
    
    def __init__(self):
        """Initialize the MCP server manager proxy."""
        self.servers = {}
        self._try_import_mcp()
    
    def _try_import_mcp(self):
        """Try to import the MCP server manager."""
        try:
            from hanzo_mcp.tools.mcp_manager import MCPServerManager as MCPManager
            self._manager = MCPManager()
            self.servers = self._manager.servers
        except ImportError:
            logger.warning("Hanzo MCP not found. Some features may not be available.")
            self._manager = None
    
    def is_server_running(self, server_name: str) -> bool:
        """Check if a server is running."""
        if self._manager:
            return self._manager.is_server_running(server_name)
        return False
    
    def get_server(self, server_name: str) -> Any:
        """Get a server instance."""
        if self._manager:
            return self._manager.get_server(server_name)
        return None
    
    async def start_server(self, server_name: str) -> Dict[str, Any]:
        """Start a server."""
        if self._manager:
            return await self._manager.start_server(server_name)
        return {"success": False, "error": "MCP not available"}
    
    async def stop_server(self, server_name: str) -> Dict[str, Any]:
        """Stop a server."""
        if self._manager:
            return await self._manager.stop_server(server_name)
        return {"success": False, "error": "MCP not available"}


class MCPComputerInterface(ComputerInterface):
    """MCP implementation of the computer interface."""
    
    def __init__(self, manager: Optional[MCPServerManager] = None):
        """Initialize the MCP computer interface.
        
        Args:
            manager: Optional MCP server manager. If not provided, a new one will be created.
        """
        self.manager = manager or MCPServerManager()
        self._server_name = "computer-use"
    
    async def is_available(self) -> bool:
        """Check if the computer-use server is available.
        
        Returns:
            True if the server is available, False otherwise
        """
        return self._server_name in self.manager.servers
    
    def is_running(self) -> bool:
        """Check if the computer-use server is running.
        
        Returns:
            True if the server is running, False otherwise
        """
        return self.manager.is_server_running(self._server_name)
    
    async def ensure_running(self) -> Dict[str, Any]:
        """Ensure that the computer-use server is running.
        
        Returns:
            Dictionary with status information
        """
        if not await self.is_available():
            return {
                "success": False,
                "error": f"Server not available: {self._server_name}"
            }
            
        if not self.is_running():
            return await self.manager.start_server(self._server_name)
            
        return {
            "success": True,
            "message": f"Server already running: {self._server_name}"
        }
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get information about the computer's capabilities.
        
        Returns:
            Dictionary with information about available tools
        """
        if not await self.is_available():
            return {
                "available": False,
                "message": "Computer use is not available on this system"
            }
            
        await self.ensure_running()
        
        tools = await self.get_available_tools()
        
        return {
            "available": True,
            "tools": tools,
            "running": self.is_running()
        }
    
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools from the computer-use server.
        
        Returns:
            List of tool definitions
        """
        if not await self.is_available() or not self.is_running():
            return []
            
        server = self.manager.get_server(self._server_name)
        if not server:
            return []
            
        return [
            {
                "name": tool_name,
                "definition": tool_def
            }
            for tool_name, tool_def in server.tools.items()
        ]
    
    async def execute_operation(
        self,
        operation: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an operation using the computer-use server.
        
        Args:
            operation: Operation to execute
            params: Parameters for the operation
            
        Returns:
            Operation result
        """
        return await self.execute_tool(operation, params)
    
    async def execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool on the computer-use server.
        
        Args:
            tool_name: Name of the tool to execute
            params: Parameters for the tool
            
        Returns:
            Dictionary with the tool result
        """
        if not await self.is_available():
            return {
                "success": False,
                "error": f"Server not available: {self._server_name}"
            }
            
        # Make sure the server is running
        if not self.is_running():
            start_result = await self.manager.start_server(self._server_name)
            if not start_result["success"]:
                return start_result
                
        server = self.manager.get_server(self._server_name)
        if not server:
            return {
                "success": False,
                "error": f"Server not found: {self._server_name}"
            }
            
        # Check if the tool is available
        if tool_name not in server.tools:
            return {
                "success": False,
                "error": f"Tool not found: {tool_name}"
            }
            
        # Prepare the request
        request = {
            "tool": tool_name,
            "params": params
        }
        
        # Send the request
        try:
            response = server.process.stdin.write(json.dumps(request) + "\n")
            server.process.stdin.flush()
            
            # Wait for the response
            response_text = server.process.stdout.readline()
            
            # Parse the response
            try:
                result = json.loads(response_text)
                return result
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": f"Invalid response from server: {response_text}"
                }
                
        except Exception as e:
            logger.error(f"Error executing tool: {str(e)}")
            return {
                "success": False,
                "error": f"Error executing tool: {str(e)}"
            }


# Create a singleton instance for convenience
mcp_computer = MCPComputerInterface()
