"""Command-line interface for the Hanzo Code Tool.

This module provides a CLI and stdio interface for editing and interacting with code,
designed to be integrated with the ACI ecosystem.
"""

import argparse
import asyncio
import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from hanzo_aci.tools.common.context import DocumentContext, SimpleToolContext
from hanzo_aci.tools.common.permissions import PermissionManager
from hanzo_aci.tools.shell.command_executor import CommandExecutor
from hanzo_aci.tools.project.analysis import ProjectAnalyzer, ProjectManager
from hanzo_aci.tools.llm_file_manager import LLMFileManager
from hanzo_aci.tools.dev_tool import DevTool

# Conditional import for vector store manager
try:
    from hanzo_aci.tools.vector.store_manager import VectorStoreManager
    has_vector_store = True
except ImportError:
    has_vector_store = False
    VectorStoreManager = None
    
# Conditional import for tree-sitter components
try:
    from hanzo_aci.tools.symbols.tree_sitter_manager import TreeSitterManager
    has_tree_sitter = True
except ImportError:
    has_tree_sitter = False
    TreeSitterManager = None


class CodeCLI:
    """CLI for the Hanzo Code Tool."""
    
    def __init__(
        self,
        allowed_paths: List[str] = None,
        project_dir: Optional[str] = None,
        verbose: bool = False
    ):
        """Initialize the CLI.
        
        Args:
            allowed_paths: List of allowed paths for operations
            project_dir: Project directory to work in
            verbose: Whether to enable verbose output
        """
        self.verbose = verbose
        self.project_dir = project_dir if project_dir else os.getcwd()
        
        # Set up allowed paths
        if allowed_paths is None:
            allowed_paths = [os.getcwd()]
            
        if project_dir and project_dir not in allowed_paths:
            allowed_paths.append(project_dir)
            
        # Initialize permission manager
        self.permission_manager = PermissionManager()
        for path in allowed_paths:
            self.permission_manager.add_allowed_path(path)
            
        self.document_context = DocumentContext()
        self.command_executor = CommandExecutor(self.permission_manager)
        self.project_analyzer = ProjectAnalyzer(self.command_executor)
        self.project_manager = ProjectManager(
            document_context=self.document_context,
            permission_manager=self.permission_manager,
            project_analyzer=self.project_analyzer
        )
        self.llm_file_manager = LLMFileManager(self.permission_manager)
        
        # Initialize vector store manager if available
        if has_vector_store:
            self.vector_store_manager = VectorStoreManager(self.permission_manager)
        else:
            self.vector_store_manager = None
            
        # Initialize tree-sitter manager if available
        if has_tree_sitter:
            self.tree_sitter_manager = TreeSitterManager()
        else:
            self.tree_sitter_manager = None
            
        # Initialize DevTool
        self.dev_tool = DevTool(
            document_context=self.document_context,
            permission_manager=self.permission_manager,
            command_executor=self.command_executor,
            project_manager=self.project_manager,
            project_analyzer=self.project_analyzer,
            vector_store_manager=self.vector_store_manager,
            tree_sitter_manager=self.tree_sitter_manager
        )
        
        # Create tool context for CLI operations
        self.tool_context = SimpleToolContext()
        
    async def execute_operation(
        self,
        operation: str,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a DevTool operation.
        
        Args:
            operation: The operation to execute
            args: Arguments for the operation
            
        Returns:
            Operation result
        """
        # Map operations to DevTool methods
        operations = {
            # File operations
            "read": self.dev_tool._read,
            "write": self.dev_tool._write,
            "edit": self.dev_tool._edit,
            "directory_tree": self.dev_tool._directory_tree,
            "get_file_info": self.dev_tool._get_file_info,
            "search_content": self.dev_tool._search_content,
            "find_replace": self.dev_tool._find_replace,
            
            # Command operations
            "run_command": self.dev_tool._run_command,
            "run_script": self.dev_tool._run_script,
            
            # Project operations
            "analyze_project": self.dev_tool._analyze_project,
            
            # Jupyter operations
            "jupyter_read": self.dev_tool._jupyter_read,
            "jupyter_edit": self.dev_tool._jupyter_edit,
            
            # Vector operations (if enabled)
            "vector_search": self.dev_tool._vector_search,
            "vector_index": self.dev_tool._vector_index,
            "vector_list": self.dev_tool._vector_list,
            "vector_delete": self.dev_tool._vector_delete,
            
            # Cursor Rules operations
            "rule_check": self.dev_tool._rule_check,
            
            # MCP Server operations
            "run_mcp": self.dev_tool._run_mcp,
            
            # LLM.md operations
            "llm_read": self.dev_tool._llm_read,
            "llm_update": self.dev_tool._llm_update,
            "llm_append": self.dev_tool._llm_append,
            
            # Symbol operations (if tree-sitter is available)
            "symbol_find": self.dev_tool._symbol_find,
            "symbol_references": self.dev_tool._symbol_references,
            "ast_explore": self.dev_tool._ast_explore,
            "ast_query": self.dev_tool._ast_query,
            "symbolic_search": self.dev_tool._symbolic_search,
        }
        
        if operation not in operations:
            available_ops = sorted(operations.keys())
            return {
                "success": False,
                "error": f"Unknown operation: {operation}",
                "available_operations": available_ops
            }
        
        # Reset tool context for this operation
        self.tool_context = SimpleToolContext()
        self.tool_context.current_operation = operation
        self.tool_context.operation_params = args
        
        # Call the operation
        try:
            result_str = await operations[operation](self.tool_context, **args)
            result = json.loads(result_str)
            return result
        except Exception as e:
            if self.verbose:
                traceback.print_exc()
            
            return {
                "success": False,
                "error": f"Error executing operation {operation}: {str(e)}"
            }

    async def process_stdin_command(self) -> None:
        """Process a command from stdin.
        
        Reads a JSON command from stdin, executes it, and writes the result to stdout.
        Format: {"operation": "<operation_name>", "args": {...}}
        """
        try:
            # Read a single line from stdin
            command_str = sys.stdin.readline().strip()
            
            if not command_str:
                # No input, return empty result
                sys.stdout.write(json.dumps({"success": False, "error": "No input provided"}) + "\n")
                sys.stdout.flush()
                return
            
            # Parse command
            try:
                command = json.loads(command_str)
            except json.JSONDecodeError:
                sys.stdout.write(json.dumps({"success": False, "error": "Invalid JSON input"}) + "\n")
                sys.stdout.flush()
                return
            
            # Validate command structure
            if not isinstance(command, dict) or "operation" not in command:
                sys.stdout.write(json.dumps({"success": False, "error": "Missing required 'operation' field"}) + "\n")
                sys.stdout.flush()
                return
            
            # Get operation and args
            operation = command.get("operation")
            args = command.get("args", {})
            
            # Execute operation
            result = await self.execute_operation(operation, args)
            
            # Write result to stdout
            sys.stdout.write(json.dumps(result) + "\n")
            sys.stdout.flush()
            
        except Exception as e:
            if self.verbose:
                traceback.print_exc()
            
            sys.stdout.write(json.dumps({"success": False, "error": f"Error processing command: {str(e)}"}) + "\n")
            sys.stdout.flush()

    async def stdio_mode(self) -> None:
        """Run in stdio mode, processing commands from stdin."""
        if self.verbose:
            sys.stderr.write("Running in stdio mode\n")
            sys.stderr.flush()
        
        while True:
            await self.process_stdin_command()

    async def run_cli_command(self, operation: str, args: Dict[str, Any]) -> int:
        """Run a CLI command.
        
        Args:
            operation: The operation to execute
            args: Arguments for the operation
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        result = await self.execute_operation(operation, args)
        
        if result.get("success", False) is False:
            print(json.dumps(result, indent=2))
            return 1
        
        print(json.dumps(result, indent=2))
        return 0
