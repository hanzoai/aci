#!/usr/bin/env python3
"""Example demonstrating how MCP would import and use ACI.

This example shows how Hanzo MCP would import and use ACI as its
underlying computer interaction layer.
"""

import os
import sys
import asyncio
import logging
import json
from typing import Dict, Any, List, Optional, Union

# Import ACI components
from hanzo_aci import ComputerInterface, NativeComputerInterface


# Mock MCP server class
class MCPServerManager:
    """Mock MCP server manager for demonstration purposes."""
    
    def __init__(self):
        """Initialize the MCP server manager."""
        self.servers = {}
        self.tools = {}
    
    def register_tool(self, name: str, tool_fn):
        """Register a tool with the MCP server.
        
        Args:
            name: Name of the tool
            tool_fn: Tool function
        """
        self.tools[name] = tool_fn
        print(f"Registered tool: {name}")


# Example MCP computer-use implementation using ACI
class ComputerUseServer:
    """MCP server for computer use operations using ACI."""
    
    def __init__(self):
        """Initialize the server with ACI."""
        # Use the ACI NativeComputerInterface
        self.computer = NativeComputerInterface(permit_all=False)
        self.tools = {}
        self._register_tools()
    
    def _register_tools(self):
        """Register all computer use tools."""
        # File operations
        self.tools["list_files"] = self._list_files
        self.tools["read_file"] = self._read_file
        self.tools["write_file"] = self._write_file
        
        # Command operations
        self.tools["run_command"] = self._run_command
        
        # System operations
        self.tools["take_screenshot"] = self._take_screenshot
        self.tools["clipboard_get"] = self._clipboard_get
        self.tools["clipboard_set"] = self._clipboard_set
        self.tools["open_application"] = self._open_application
        
        # Advanced operations
        self.tools["analyze_project"] = self._analyze_project
        self.tools["vector_search"] = self._vector_search
        self.tools["symbol_find"] = self._symbol_find
    
    async def _list_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List files in a directory."""
        path = params.get("path", ".")
        return await self.computer.list_files(path)
    
    async def _read_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read a file."""
        path = params.get("path")
        if not path:
            return {"success": False, "error": "Path is required"}
        return await self.computer.read_file(path)
    
    async def _write_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Write to a file."""
        path = params.get("path")
        content = params.get("content")
        if not path or content is None:
            return {"success": False, "error": "Path and content are required"}
        return await self.computer.write_file(path, content)
    
    async def _run_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run a shell command."""
        command = params.get("command")
        cwd = params.get("cwd")
        if not command:
            return {"success": False, "error": "Command is required"}
        return await self.computer.run_command(command, cwd)
    
    async def _take_screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Take a screenshot."""
        return await self.computer.take_screenshot()
    
    async def _clipboard_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get clipboard contents."""
        return await self.computer.clipboard_get()
    
    async def _clipboard_set(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set clipboard contents."""
        text = params.get("text")
        if text is None:
            return {"success": False, "error": "Text is required"}
        return await self.computer.clipboard_set(text)
    
    async def _open_application(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Open an application."""
        app_name = params.get("name")
        if not app_name:
            return {"success": False, "error": "Application name is required"}
        return await self.computer.open_application(app_name)
    
    async def _analyze_project(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a project."""
        project_dir = params.get("project_dir")
        if not project_dir:
            return {"success": False, "error": "Project directory is required"}
        return await self.computer.analyze_project(project_dir)
    
    async def _vector_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search the vector store."""
        query_text = params.get("query_text")
        project_dir = params.get("project_dir")
        n_results = params.get("n_results", 10)
        if not query_text or not project_dir:
            return {"success": False, "error": "Query text and project directory are required"}
        return await self.computer.vector_search(query_text, project_dir, n_results)
    
    async def _symbol_find(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Find symbols in a file or directory."""
        path = params.get("path")
        symbol_name = params.get("symbol_name")
        if not path:
            return {"success": False, "error": "Path is required"}
        return await self.computer.symbol_find(path, symbol_name)
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request from the MCP.
        
        Args:
            request: Request dictionary with tool name and parameters
            
        Returns:
            Response dictionary
        """
        tool_name = request.get("tool")
        params = request.get("params", {})
        
        if not tool_name:
            return {"success": False, "error": "Tool name is required"}
        
        if tool_name not in self.tools:
            return {
                "success": False, 
                "error": f"Unknown tool: {tool_name}",
                "available_tools": list(self.tools.keys())
            }
        
        try:
            result = await self.tools[tool_name](params)
            return result
        except Exception as e:
            return {"success": False, "error": f"Error executing tool: {str(e)}"}


# Example MCP DevTool implementation using ACI
class DevToolServer:
    """MCP server for developer tools using ACI."""
    
    def __init__(self):
        """Initialize the server with ACI."""
        # Use the ACI NativeComputerInterface
        self.computer = NativeComputerInterface(permit_all=False)
        self.tools = {}
        self._register_tools()
    
    def _register_tools(self):
        """Register all developer tools."""
        # File operations
        self.tools["read"] = self._read
        self.tools["write"] = self._write
        self.tools["edit"] = self._edit
        self.tools["directory_tree"] = self._directory_tree
        self.tools["search_content"] = self._search_content
        
        # Project operations
        self.tools["analyze_project"] = self._analyze_project
        
        # Vector operations
        self.tools["vector_search"] = self._vector_search
        self.tools["vector_index"] = self._vector_index
        
        # Symbol operations
        self.tools["symbol_find"] = self._symbol_find
        self.tools["symbol_search"] = self._symbol_search
    
    async def _read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read file(s)."""
        paths = params.get("paths")
        if not paths:
            return {"success": False, "error": "Paths parameter is required"}
        
        # Handle single path or list of paths
        if isinstance(paths, str):
            return await self.computer.read_file(paths)
        elif isinstance(paths, list):
            results = []
            for path in paths:
                result = await self.computer.read_file(path)
                results.append(result)
            return {"success": True, "results": results}
        else:
            return {"success": False, "error": "Invalid paths parameter"}
    
    async def _write(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Write to a file."""
        path = params.get("path")
        content = params.get("content")
        if not path or content is None:
            return {"success": False, "error": "Path and content are required"}
        return await self.computer.write_file(path, content)
    
    async def _edit(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Edit a file with line-based edits."""
        path = params.get("path")
        edits = params.get("edits")
        dry_run = params.get("dry_run", False)
        
        if not path or not edits:
            return {"success": False, "error": "Path and edits are required"}
        
        # Read the file
        read_result = await self.computer.read_file(path)
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
        return await self.computer.write_file(path, content)
    
    async def _directory_tree(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get a directory tree."""
        path = params.get("path", ".")
        depth = params.get("depth", 3)
        include_filtered = params.get("include_filtered", False)
        
        # List files recursively
        result = {"success": True, "tree": ""}
        
        # Simple recursive function to build tree
        async def build_tree(dir_path, prefix="", level=0):
            if level > depth and depth > 0:
                return
            
            list_result = await self.computer.list_files(dir_path)
            if not list_result.get("success", False):
                return
            
            files = list_result.get("files", [])
            directories = list_result.get("directories", [])
            
            # Sort entries
            files.sort()
            directories.sort()
            
            # Add directories
            for i, dirname in enumerate(directories):
                is_last = (i == len(directories) - 1 and len(files) == 0)
                
                if include_filtered or not dirname.startswith("."):
                    if is_last:
                        result["tree"] += f"{prefix}└── {dirname}/\n"
                        await build_tree(
                            os.path.join(dir_path, dirname),
                            prefix + "    ",
                            level + 1
                        )
                    else:
                        result["tree"] += f"{prefix}├── {dirname}/\n"
                        await build_tree(
                            os.path.join(dir_path, dirname),
                            prefix + "│   ",
                            level + 1
                        )
            
            # Add files
            for i, filename in enumerate(files):
                is_last = (i == len(files) - 1)
                
                if include_filtered or not filename.startswith("."):
                    if is_last:
                        result["tree"] += f"{prefix}└── {filename}\n"
                    else:
                        result["tree"] += f"{prefix}├── {filename}\n"
        
        # Start building tree
        result["tree"] = f"{os.path.basename(path)}/\n"
        await build_tree(path)
        
        return result
    
    async def _search_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for content in files."""
        pattern = params.get("pattern")
        path = params.get("path")
        file_pattern = params.get("file_pattern", "*")
        
        if not pattern or not path:
            return {"success": False, "error": "Pattern and path are required"}
        
        # Execute search using grep or similar
        command = f"grep -r \"{pattern}\" --include=\"{file_pattern}\" {path}"
        result = await self.computer.run_command(command)
        
        if not result.get("success", False):
            return result
        
        # Parse results
        output = result.get("stdout", "")
        lines = output.strip().split("\n")
        matches = []
        
        for line in lines:
            if line:
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    file_path, line_number, content = parts
                    matches.append({
                        "file": file_path,
                        "line": int(line_number),
                        "content": content.strip()
                    })
        
        return {"success": True, "matches": matches}
    
    async def _analyze_project(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a project directory structure and dependencies."""
        project_dir = params.get("project_dir")
        if not project_dir:
            return {"success": False, "error": "Project directory is required"}
        
        return await self.computer.analyze_project(project_dir)
    
    async def _vector_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search the vector store."""
        query_text = params.get("query_text")
        project_dir = params.get("project_dir")
        n_results = params.get("n_results", 10)
        
        if not query_text or not project_dir:
            return {"success": False, "error": "Query text and project directory are required"}
        
        return await self.computer.vector_search(query_text, project_dir, n_results)
    
    async def _vector_index(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Index a file or directory in the vector store."""
        path = params.get("path")
        recursive = params.get("recursive", True)
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        return await self.computer.vector_index(path, recursive)
    
    async def _symbol_find(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Find symbols in a file or directory."""
        path = params.get("path")
        symbol_name = params.get("symbol_name")
        
        if not path:
            return {"success": False, "error": "Path is required"}
        
        return await self.computer.symbol_find(path, symbol_name)
    
    async def _symbol_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for symbols matching a pattern."""
        pattern = params.get("pattern")
        path = params.get("path")
        
        if not pattern or not path:
            return {"success": False, "error": "Pattern and path are required"}
        
        return await self.computer.symbol_search(pattern, path)
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request from the MCP.
        
        Args:
            request: Request dictionary with tool name and parameters
            
        Returns:
            Response dictionary
        """
        operation = request.get("operation")
        params = request.get("params", {})
        
        if not operation:
            return {"success": False, "error": "Operation is required"}
        
        if operation not in self.tools:
            return {
                "success": False, 
                "error": f"Unknown operation: {operation}",
                "available_operations": list(self.tools.keys())
            }
        
        try:
            result = await self.tools[operation](params)
            return result
        except Exception as e:
            return {"success": False, "error": f"Error executing operation: {str(e)}"}


async def demo():
    """Run a demonstration of MCP integration with ACI."""
    # Create an MCP server manager
    manager = MCPServerManager()
    
    # Create servers
    computer_use = ComputerUseServer()
    dev_tool = DevToolServer()
    
    print("\n=== MCP Integration with ACI ===")
    print("\nRegistering servers with MCP...")
    manager.servers["computer-use"] = computer_use
    manager.servers["dev-tool"] = dev_tool
    
    # Simulate MCP request to computer-use server
    print("\n=== Testing Computer Use Server ===")
    request = {
        "tool": "list_files",
        "params": {"path": "."}
    }
    print(f"Request: {request}")
    
    response = await computer_use.process_request(request)
    print(f"Response: {json.dumps(response, indent=2)}")
    
    # Simulate MCP request to dev-tool server
    print("\n=== Testing Dev Tool Server ===")
    request = {
        "operation": "directory_tree",
        "params": {"path": ".", "depth": 1}
    }
    print(f"Request: {request}")
    
    response = await dev_tool.process_request(request)
    print(f"Response: {json.dumps(response, indent=2)}")
    
    print("\n=== ACI capabilities available via MCP ===")
    print("\nComputer Use Tools:")
    for tool in computer_use.tools:
        print(f"- {tool}")
    
    print("\nDev Tools:")
    for tool in dev_tool.tools:
        print(f"- {tool}")
    
    print("\nDemo complete.")


if __name__ == "__main__":
    asyncio.run(demo())
