#!/usr/bin/env python3
"""Example demonstrating the specialized modules in Hanzo ACI.

This example shows how to use the vector search and symbolic reasoning modules
in Hanzo ACI, and how they can be exposed through MCP as separate tools.
"""

import os
import sys
import json
import asyncio
import argparse
import tempfile
from typing import Dict, List, Optional, Any, Union

# Import the relevant modules
# These will be imported conditionally to handle missing dependencies
try:
    from hanzo_aci.specialized.vector_search import VectorSearchInterface
    vector_search_available = True
except ImportError:
    vector_search_available = False

try:
    from hanzo_aci.specialized.symbolic_reasoning import SymbolicReasoningInterface
    symbolic_reasoning_available = True
except ImportError:
    symbolic_reasoning_available = False


class VectorSearchTool:
    """MCP tool for vector search operations."""
    
    def __init__(self):
        """Initialize with the vector search interface."""
        if not vector_search_available:
            raise ImportError(
                "Vector search dependencies not available. "
                "Install with pip install 'hanzo-aci[vectordb]'"
            )
        
        self.interface = VectorSearchInterface()
        self.tools = {
            "load_collection": self._load_collection,
            "vector_search": self._vector_search,
            "semantic_search": self._semantic_search,
            "vector_index": self._vector_index,
            "hybrid_search": self._hybrid_search
        }
    
    async def _load_collection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Load a collection for searching."""
        path = params.get("path")
        if not path:
            return {"success": False, "error": "Path parameter is required"}
        
        return await self.interface.execute_operation("load_collection", {"path": path})
    
    async def _vector_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform vector search."""
        query = params.get("query")
        n_results = params.get("n_results", 10)
        
        if not query:
            return {"success": False, "error": "Query parameter is required"}
        
        return await self.interface.execute_operation(
            "vector_search",
            {"query": query, "n_results": n_results}
        )
    
    async def _semantic_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Alias for vector search with different parameter names."""
        text = params.get("text")
        limit = params.get("limit", 10)
        
        if not text:
            return {"success": False, "error": "Text parameter is required"}
        
        return await self.interface.execute_operation(
            "semantic_search",
            {"text": text, "limit": limit}
        )
    
    async def _vector_index(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Index content in the vector database."""
        documents = params.get("documents")
        metadatas = params.get("metadatas")
        ids = params.get("ids")
        
        if not documents:
            return {"success": False, "error": "Documents parameter is required"}
        
        return await self.interface.execute_operation(
            "vector_index",
            {
                "documents": documents,
                "metadatas": metadatas,
                "ids": ids
            }
        )
    
    async def _hybrid_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform hybrid search combining vector and keyword search."""
        query = params.get("query")
        filter_dict = params.get("filter")
        n_results = params.get("n_results", 10)
        
        if not query:
            return {"success": False, "error": "Query parameter is required"}
        
        return await self.interface.execute_operation(
            "hybrid_search",
            {
                "query": query,
                "filter": filter_dict,
                "n_results": n_results
            }
        )
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request from MCP."""
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
            return {
                "success": False,
                "error": f"Error executing tool: {str(e)}"
            }


class SymbolicReasoningTool:
    """MCP tool for symbolic reasoning operations."""
    
    def __init__(self):
        """Initialize with the symbolic reasoning interface."""
        if not symbolic_reasoning_available:
            raise ImportError(
                "Symbolic reasoning dependencies not available. "
                "Install with pip install 'hanzo-aci[symbolic]'"
            )
        
        self.interface = SymbolicReasoningInterface()
        self.tools = {
            "parse_file": self._parse_file,
            "find_symbols": self._find_symbols,
            "find_references": self._find_references,
            "analyze_dependencies": self._analyze_dependencies
        }
    
    async def _parse_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a file into an AST."""
        file_path = params.get("file_path")
        
        if not file_path:
            return {"success": False, "error": "File path parameter is required"}
        
        return await self.interface.execute_operation(
            "parse_file",
            {"file_path": file_path}
        )
    
    async def _find_symbols(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Find symbols in a file."""
        file_path = params.get("file_path")
        symbol_type = params.get("symbol_type")
        
        if not file_path:
            return {"success": False, "error": "File path parameter is required"}
        
        return await self.interface.execute_operation(
            "find_symbols",
            {
                "file_path": file_path,
                "symbol_type": symbol_type
            }
        )
    
    async def _find_references(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Find references to a symbol in a file."""
        file_path = params.get("file_path")
        symbol_name = params.get("symbol_name")
        
        if not file_path or not symbol_name:
            return {"success": False, "error": "File path and symbol name parameters are required"}
        
        return await self.interface.execute_operation(
            "find_references",
            {
                "file_path": file_path,
                "symbol_name": symbol_name
            }
        )
    
    async def _analyze_dependencies(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze dependencies between symbols in a file."""
        file_path = params.get("file_path")
        
        if not file_path:
            return {"success": False, "error": "File path parameter is required"}
        
        return await self.interface.execute_operation(
            "analyze_dependencies",
            {"file_path": file_path}
        )
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request from MCP."""
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
            return {
                "success": False,
                "error": f"Error executing tool: {str(e)}"
            }


class MCPServerManager:
    """Mock MCP server manager for demonstration purposes."""
    
    def __init__(self):
        """Initialize the MCP server manager."""
        self.servers = {}
    
    def register_server(self, name: str, server):
        """Register a server with MCP."""
        self.servers[name] = server
        print(f"Registered server: {name}")
    
    async def call_server(self, server_name: str, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on a server."""
        if server_name not in self.servers:
            return {
                "success": False,
                "error": f"Unknown server: {server_name}",
                "available_servers": list(self.servers.keys())
            }
        
        server = self.servers[server_name]
        
        return await server.process_request({
            "tool": tool_name,
            "params": params
        })
    
    async def call_parallel(self, calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Call multiple tools in parallel."""
        tasks = []
        
        for call in calls:
            server_name = call.get("server")
            tool_name = call.get("tool")
            params = call.get("params", {})
            
            if not server_name or not tool_name:
                continue
            
            task = asyncio.create_task(
                self.call_server(server_name, tool_name, params)
            )
            tasks.append(task)
        
        return await asyncio.gather(*tasks)


class LLMCodeExplorer:
    """Example LLM-based code explorer using parallel tools."""
    
    def __init__(self):
        """Initialize the LLM code explorer."""
        # Set up MCP
        self.mcp = MCPServerManager()
        
        # Register the specialized tools if available
        try:
            self.vector_search_tool = VectorSearchTool()
            self.mcp.register_server("vector-search", self.vector_search_tool)
        except ImportError as e:
            print(f"Vector search not available: {e}")
            self.vector_search_tool = None
        
        try:
            self.symbolic_reasoning_tool = SymbolicReasoningTool()
            self.mcp.register_server("symbolic-reason", self.symbolic_reasoning_tool)
        except ImportError as e:
            print(f"Symbolic reasoning not available: {e}")
            self.symbolic_reasoning_tool = None
    
    async def analyze_code_file(self, file_path: str, search_query: str = None):
        """Analyze a code file using both tools in parallel."""
        calls = []
        
        # Add symbolic reasoning call
        if self.symbolic_reasoning_tool:
            calls.append({
                "server": "symbolic-reason",
                "tool": "find_symbols",
                "params": {"file_path": file_path}
            })
        
        # Add vector search call if query provided
        if self.vector_search_tool and search_query:
            # First, ensure the collection is loaded
            await self.mcp.call_server(
                "vector-search",
                "load_collection",
                {"path": os.path.dirname(file_path)}
            )
            
            # Then add the search call
            calls.append({
                "server": "vector-search",
                "tool": "vector_search",
                "params": {"query": search_query, "n_results": 5}
            })
        
        # Execute calls in parallel
        if not calls:
            return {"success": False, "error": "No tools available"}
        
        results = await self.mcp.call_parallel(calls)
        
        # Combine results
        combined_results = {
            "success": True,
            "file_path": file_path,
            "analysis": {}
        }
        
        for i, call in enumerate(calls):
            server = call["server"]
            tool = call["tool"]
            combined_results["analysis"][f"{server}_{tool}"] = results[i]
        
        return combined_results


async def run_demo(file_path: str, search_query: str = None):
    """Run a demonstration of the code analyzer."""
    print("\n=== Hanzo ACI Specialized Modules Demo ===")
    
    # Create the LLM code explorer
    explorer = LLMCodeExplorer()
    
    # Analyze the file
    print(f"\nAnalyzing file: {file_path}")
    if search_query:
        print(f"With search query: {search_query}")
    
    result = await explorer.analyze_code_file(file_path, search_query)
    
    # Print the result
    print("\nAnalysis results:")
    print(json.dumps(result, indent=2))
    
    print("\nDemo complete.")


def main():
    """Main entry point for the example."""
    parser = argparse.ArgumentParser(description="Hanzo ACI Specialized Modules Example")
    
    parser.add_argument(
        "file_path",
        help="Path to the code file to analyze"
    )
    
    parser.add_argument(
        "--search",
        help="Optional semantic search query"
    )
    
    args = parser.parse_args()
    
    # Check if either vector search or symbolic reasoning is available
    if not vector_search_available and not symbolic_reasoning_available:
        print("Error: Neither vector search nor symbolic reasoning modules are available.")
        print("Please install at least one of the following:")
        print("  pip install 'hanzo-aci[vectordb]'")
        print("  pip install 'hanzo-aci[symbolic]'")
        return 1
    
    # Check if file exists
    if not os.path.exists(args.file_path):
        print(f"Error: File not found: {args.file_path}")
        return 1
    
    try:
        asyncio.run(run_demo(args.file_path, args.search))
        return 0
    except KeyboardInterrupt:
        print("\nExample interrupted")
        return 130
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
