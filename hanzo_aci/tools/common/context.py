"""Enhanced Context classes for Hanzo ACI tools.

This module provides context classes for tool operations.
"""

import json
import time
from typing import Any, ClassVar, final, Optional


@final
class SimpleToolContext:
    """A simplified context for tools when an MCP context is not available.
    
    This class provides a minimal implementation for tracking operations
    and handling success/error responses.
    """
    
    def __init__(self) -> None:
        """Initialize the simple tool context."""
        # For tracking operations and params
        self.current_operation: Optional[str] = None
        self.operation_params: dict[str, Any] = {}
        
    async def info(self, message: str) -> None:
        """Log an informational message.
        
        Args:
            message: The message to log
        """
        print(f"[INFO] {message}")
        
    async def debug(self, message: str) -> None:
        """Log a debug message.
        
        Args:
            message: The message to log
        """
        print(f"[DEBUG] {message}")
        
    async def warning(self, message: str) -> None:
        """Log a warning message.
        
        Args:
            message: The message to log
        """
        print(f"[WARNING] {message}")
        
    async def error(self, message: str) -> None:
        """Log an error message.
        
        Args:
            message: The message to log
        """
        print(f"[ERROR] {message}")
        
    async def success(self, message: str, data: dict[str, Any] | None = None) -> str:
        """Create a success response with standardized format.
        
        Args:
            message: Success message
            data: Optional data to include in the response
            
        Returns:
            JSON string response
        """
        if data is None:
            data = {}
            
        # Always include the operation name if we have it
        if self.current_operation and "tool" not in data:
            data["tool"] = self.current_operation
            
        # Add operation params for transparency if needed
        if self.operation_params and "params" not in data:
            # Don't include passwords, tokens, or keys
            filtered_params = {k: v for k, v in self.operation_params.items() 
                              if not any(sensitive in k.lower() for sensitive in 
                                      ["password", "token", "key", "secret"])}
            if filtered_params:
                data["params"] = filtered_params
        
        # Create response
        response = {
            "status": "success",
            "success": True,
            "message": message,
            "data": data
        }
        
        return json.dumps(response)


@final
class DocumentContext:
    """Manages document context and codebase understanding."""

    def __init__(self) -> None:
        """Initialize the document context."""
        self.documents: dict[str, str] = {}
        self.document_metadata: dict[str, dict[str, Any]] = {}
        self.modified_times: dict[str, float] = {}
        self.allowed_paths: set[str] = set()

    def add_allowed_path(self, path: str) -> None:
        """Add a path to the allowed paths.

        Args:
            path: The path to allow
        """
        self.allowed_paths.add(path)

    def is_path_allowed(self, path: str) -> bool:
        """Check if a path is allowed.

        Args:
            path: The path to check

        Returns:
            True if the path is allowed, False otherwise
        """
        for allowed_path in self.allowed_paths:
            if path.startswith(allowed_path):
                return True
        return False

    def add_document(
        self, path: str, content: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """Add a document to the context.

        Args:
            path: The path of the document
            content: The content of the document
            metadata: Optional metadata about the document
        """
        self.documents[path] = content
        self.modified_times[path] = time.time()

        if metadata:
            self.document_metadata[path] = metadata
        else:
            # Try to infer metadata
            self.document_metadata[path] = self._infer_metadata(path, content)

    def get_document(self, path: str) -> str | None:
        """Get a document from the context.

        Args:
            path: The path of the document

        Returns:
            The document content, or None if not found
        """
        return self.documents.get(path)

    def get_document_metadata(self, path: str) -> dict[str, Any] | None:
        """Get document metadata.

        Args:
            path: The path of the document

        Returns:
            The document metadata, or None if not found
        """
        return self.document_metadata.get(path)

    def update_document(self, path: str, content: str) -> None:
        """Update a document in the context.

        Args:
            path: The path of the document
            content: The new content of the document
        """
        self.documents[path] = content
        self.modified_times[path] = time.time()

        # Update metadata
        self.document_metadata[path] = self._infer_metadata(path, content)

    def remove_document(self, path: str) -> None:
        """Remove a document from the context.

        Args:
            path: The path of the document
        """
        if path in self.documents:
            del self.documents[path]

        if path in self.document_metadata:
            del self.document_metadata[path]

        if path in self.modified_times:
            del self.modified_times[path]

    def _infer_metadata(self, path: str, content: str) -> dict[str, Any]:
        """Infer metadata about a document.

        Args:
            path: The path of the document
            content: The content of the document

        Returns:
            Inferred metadata
        """
        import os

        extension: str = os.path.splitext(path)[1].lower()

        metadata: dict[str, Any] = {
            "extension": extension,
            "size": len(content),
            "line_count": content.count("\n") + 1,
        }

        # Infer language based on extension
        language_map: dict[str, list[str]] = {
            "python": [".py"],
            "javascript": [".js", ".jsx"],
            "typescript": [".ts", ".tsx"],
            "java": [".java"],
            "c++": [".c", ".cpp", ".h", ".hpp"],
            "go": [".go"],
            "rust": [".rs"],
            "ruby": [".rb"],
            "php": [".php"],
            "html": [".html", ".htm"],
            "css": [".css"],
            "markdown": [".md"],
            "json": [".json"],
            "yaml": [".yaml", ".yml"],
            "xml": [".xml"],
            "sql": [".sql"],
            "shell": [".sh", ".bash"],
        }

        # Find matching language
        for language, extensions in language_map.items():
            if extension in extensions:
                metadata["language"] = language
                break
        else:
            metadata["language"] = "text"

        return metadata