"""Concrete implementation of the Computer Interface.

This module provides a concrete implementation of the Computer Interface that
delegates operations to the appropriate backend based on availability.
"""

import os
import logging
from typing import Dict, List, Optional, Any, Union

from hanzo_aci.interface import ComputerInterface
from hanzo_aci.tools.native import NativeComputerInterface, native_computer

logger = logging.getLogger(__name__)

# Lazy imports to avoid dependency issues
_mcp_computer = None
_claude_code_computer = None


def _get_mcp_computer():
    """Get the MCP computer interface."""
    global _mcp_computer
    if _mcp_computer is None:
        try:
            from hanzo_aci.integrations.mcp import MCPComputerInterface, mcp_computer
            _mcp_computer = mcp_computer
        except ImportError:
            logger.debug("MCP integration not available")
            _mcp_computer = None
    return _mcp_computer


def _get_claude_code_computer():
    """Get the Claude Code computer interface."""
    global _claude_code_computer
    if _claude_code_computer is None:
        try:
            from hanzo_aci.integrations.claude_code import ClaudeCodeInterface, claude_code_computer
            _claude_code_computer = claude_code_computer
        except ImportError:
            logger.debug("Claude Code integration not available")
            _claude_code_computer = None
    return _claude_code_computer


class ConcreteComputerInterface(ComputerInterface):
    """Concrete implementation of the computer interface.
    
    This implementation delegates to the appropriate backend based on
    availability and configuration.
    """
    
    def __init__(
        self,
        backend: Optional[str] = None,
        native_interface: Optional[NativeComputerInterface] = None
    ):
        """Initialize the concrete computer interface.
        
        Args:
            backend: Optional backend to use ('native', 'mcp', or 'claude_code').
                If not specified, it will try to use the best available backend.
            native_interface: Optional native interface to use. If not specified,
                the default native interface will be used.
        """
        self.backend = backend
        self.native_interface = native_interface or native_computer
        self._selected_backend = None
    
    async def _select_backend(self) -> ComputerInterface:
        """Select the appropriate backend based on availability.
        
        Returns:
            The selected backend interface
        """
        # If a backend is explicitly specified, use it
        if self.backend:
            if self.backend == "native":
                return self.native_interface
            elif self.backend == "mcp":
                mcp = _get_mcp_computer()
                if mcp and await mcp.is_available():
                    return mcp
                logger.warning("MCP backend requested but not available, falling back to native")
                return self.native_interface
            elif self.backend == "claude_code":
                claude_code = _get_claude_code_computer()
                if claude_code and await claude_code.is_available():
                    return claude_code
                logger.warning("Claude Code backend requested but not available, falling back to native")
                return self.native_interface
            else:
                logger.warning(f"Unknown backend: {self.backend}, falling back to native")
                return self.native_interface
        
        # Otherwise, try to use the best available backend
        # First, try MCP
        mcp = _get_mcp_computer()
        if mcp and await mcp.is_available():
            return mcp
        
        # Then, try Claude Code
        claude_code = _get_claude_code_computer()
        if claude_code and await claude_code.is_available():
            return claude_code
        
        # Finally, fall back to native
        return self.native_interface
    
    async def is_available(self) -> bool:
        """Check if any backend is available.
        
        Returns:
            True if any backend is available, False otherwise
        """
        backend = await self._select_backend()
        return await backend.is_available()
    
    async def ensure_running(self) -> Dict[str, Any]:
        """Ensure that the selected backend is running.
        
        Returns:
            Dictionary with status information
        """
        backend = await self._select_backend()
        return await backend.ensure_running()
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get information about the computer's capabilities.
        
        Returns:
            Dictionary with information about available operations
        """
        backend = await self._select_backend()
        capabilities = await backend.get_capabilities()
        
        # Add information about the selected backend
        if isinstance(backend, NativeComputerInterface):
            capabilities["backend"] = "native"
        else:
            backend_module = backend.__class__.__module__
            if "mcp" in backend_module:
                capabilities["backend"] = "mcp"
            elif "claude_code" in backend_module:
                capabilities["backend"] = "claude_code"
            else:
                capabilities["backend"] = "unknown"
        
        return capabilities
    
    async def execute_operation(
        self,
        operation: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an operation using the selected backend.
        
        Args:
            operation: The operation to execute
            params: Parameters for the operation
            
        Returns:
            Operation result
        """
        backend = await self._select_backend()
        return await backend.execute_operation(operation, params)


# Create a singleton instance
computer = ConcreteComputerInterface()
