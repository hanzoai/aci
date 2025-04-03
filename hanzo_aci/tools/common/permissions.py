"""Permissions management for Hanzo ACI tools.

This module provides functionality for permissions management
and security for tool operations.
"""

import os
from pathlib import Path
from typing import final, List, Set, Optional


@final
class PermissionManager:
    """Manages permissions for operations on the filesystem.
    
    This class is responsible for validating that operations are only performed
    on allowed paths, to enhance security when tools are used by AI agents.
    """
    
    def __init__(self) -> None:
        """Initialize the permission manager with empty allowed paths."""
        self.allowed_paths: Set[str] = set()
    
    def add_allowed_path(self, path: str) -> None:
        """Add a path to the allowed paths.
        
        Args:
            path: The path to allow operations on
        """
        try:
            real_path = os.path.realpath(path)
            self.allowed_paths.add(real_path)
        except Exception:
            # If there's any error resolving the path, just use it as is
            self.allowed_paths.add(path)
    
    def is_path_allowed(self, path: str) -> bool:
        """Check if a path is allowed for operations.
        
        Args:
            path: The path to check
            
        Returns:
            True if the path is allowed, False otherwise
        """
        try:
            real_path = os.path.realpath(path)
            
            # Always allow paths that are literally in the allowed set
            if real_path in self.allowed_paths:
                return True
            
            # Check if the path is within any allowed path
            for allowed_path in self.allowed_paths:
                # Check if the path is a subdirectory of the allowed path
                if real_path.startswith(allowed_path + os.sep):
                    return True
            
            return False
        except Exception:
            # If there's any error checking the path, default to not allowed
            return False
    
    def get_allowed_paths(self) -> List[str]:
        """Get the list of allowed paths.
        
        Returns:
            List of allowed paths
        """
        return list(self.allowed_paths)
    
    def clear_allowed_paths(self) -> None:
        """Clear all allowed paths."""
        self.allowed_paths.clear()
    
    def is_restricted_path(self, path: str) -> bool:
        """Check if a path is restricted (sensitive system path).
        
        Args:
            path: The path to check
            
        Returns:
            True if the path is restricted, False otherwise
        """
        try:
            real_path = os.path.realpath(path)
            
            # Define restricted paths based on operating system
            restricted_paths = []
            
            if os.name == 'posix':  # Unix-like systems
                restricted_paths = [
                    '/etc',
                    '/var',
                    '/usr',
                    '/bin',
                    '/sbin',
                    '/boot',
                    '/dev',
                    '/proc',
                    '/sys',
                    '/root',
                    '/private',
                ]
            elif os.name == 'nt':  # Windows
                restricted_paths = [
                    'C:\\Windows',
                    'C:\\Program Files',
                    'C:\\Program Files (x86)',
                    'C:\\ProgramData',
                ]
            
            # Check if the path is within any restricted path
            for restricted_path in restricted_paths:
                if real_path.startswith(restricted_path):
                    return True
            
            return False
        except Exception:
            # If there's any error checking the path, default to restricted
            return True