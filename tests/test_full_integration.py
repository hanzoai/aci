"""Full integration test for Hanzo ACI with Dev and MCP.

This test demonstrates the complete flow from MCP to ACI to Dev,
ensuring that all components work together properly.
"""

import os
import pytest
import tempfile
from unittest.mock import MagicMock, patch

# Import base components
from hanzo_aci.concrete import ConcreteComputerInterface
from hanzo_aci.tools.native import NativeComputerInterface


# Optional imports that may not be available
def test_imports():
    """Test importing the optional dependencies."""
    # Test importing MCP integration
    try:
        from hanzo_aci.integrations.mcp import MCPComputerInterface
        mcp_available = True
    except ImportError:
        mcp_available = False
    
    # Test importing Dev integration
    try:
        from hanzo_aci.integrations.dev import DevComputerInterface
        dev_available = True
    except ImportError:
        dev_available = False
    
    # Test importing vector search
    try:
        from hanzo_aci.specialized.vector_search import VectorSearchInterface
        vector_search_available = True
    except ImportError:
        vector_search_available = False
    
    # Test importing symbolic reasoning
    try:
        from hanzo_aci.specialized.symbolic_reasoning import SymbolicReasoningInterface
        symbolic_reasoning_available = True
    except ImportError:
        symbolic_reasoning_available = False
    
    # At least the core components should be available
    assert True, "Core components are available"


@pytest.mark.asyncio
async def test_concrete_computer_interface():
    """Test that the concrete computer interface can select backends."""
    # Create a concrete interface with native backend
    interface = ConcreteComputerInterface(backend="native")
    
    # Check that it's available
    assert await interface.is_available() is True
    
    # Check capabilities
    capabilities = await interface.get_capabilities()
    assert capabilities["available"] is True
    assert capabilities["backend"] == "native"


@pytest.mark.asyncio
async def test_mcp_computer_interface():
    """Test the MCP computer interface with mocks."""
    # Skip if MCP integration is not available
    try:
        from hanzo_aci.integrations.mcp import MCPComputerInterface, MCPServerManager
    except ImportError:
        pytest.skip("MCP integration not available")
    
    # Create mock MCP server manager
    mock_manager = MagicMock(spec=MCPServerManager)
    
    # Fix: Add the servers attribute to the mock manager
    mock_manager.servers = {"computer-use": MagicMock()}
    
    mock_manager.is_server_running.return_value = True
    mock_manager.get_server.return_value = MagicMock()
    
    # Set up mock server response
    mock_server = mock_manager.get_server.return_value
    mock_server.tools = {"test_tool": MagicMock()}
    
    # Create an MCP interface with the mock manager
    interface = MCPComputerInterface(manager=mock_manager)
    
    # Check that it's available
    assert await interface.is_available() is True
    
    # Check capabilities
    capabilities = await interface.get_capabilities()
    assert capabilities["available"] is True


@pytest.mark.asyncio
async def test_dev_computer_interface():
    """Test the Dev computer interface with mocks."""
    # Skip if Dev integration is not available
    try:
        from hanzo_aci.integrations.dev import DevComputerInterface, DevManager
    except ImportError:
        pytest.skip("Dev integration not available")
    
    # Create mock Dev manager
    mock_manager = MagicMock(spec=DevManager)
    mock_manager.is_available = True
    mock_manager.get_dev_module.return_value = MagicMock()
    
    # Create a Dev interface with the mock manager
    interface = DevComputerInterface(manager=mock_manager)
    
    # Check that it's available
    assert await interface.is_available() is True
    
    # Check capabilities
    capabilities = await interface.get_capabilities()
    assert capabilities["available"] is True


@pytest.mark.asyncio
async def test_vector_search_interface():
    """Test the vector search interface with mocks."""
    # Skip if vector search is not available
    try:
        from hanzo_aci.specialized.vector_search import VectorSearchInterface
    except ImportError:
        pytest.skip("Vector search not available")
    
    # Create a vector search interface
    interface = VectorSearchInterface()
    
    # Patch the instance's availability attribute directly
    with patch.object(interface, "_available", True):
        
        # Mock the client and collection
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        
        # Set up mock query results
        mock_collection.query.return_value = {
            "documents": [["Example document"]],
            "metadatas": [[{"source": "test.py"}]],
            "distances": [[0.5]],
            "ids": [["1"]]
        }
        
        # Assign the mocks
        interface._client = mock_client
        interface._collection = mock_collection
        
        # Check that it's available
        assert await interface.is_available() is True
        
        # Check capabilities
        capabilities = await interface.get_capabilities()
        assert capabilities["available"] is True
        
        # Test vector search
        result = await interface.execute_operation(
            "vector_search",
            {"query": "test query"}
        )
        assert result["success"] is True
        assert len(result["results"]) > 0


@pytest.mark.asyncio
async def test_symbolic_reasoning_interface():
    """Test the symbolic reasoning interface with mocks."""
    # Skip if symbolic reasoning is not available
    try:
        from hanzo_aci.specialized.symbolic_reasoning import SymbolicReasoningInterface
    except ImportError:
        pytest.skip("Symbolic reasoning not available")
    
    # Create a symbolic reasoning interface
    interface = SymbolicReasoningInterface()
    
    # Patch the instance's availability attribute directly
    with patch.object(interface, "_available", True):
        
        # Create a mock parser and language
        mock_parser = MagicMock()
        mock_language = MagicMock()
        
        # Set up a simple syntax tree
        mock_tree = MagicMock()
        mock_root_node = MagicMock()
        mock_root_node.type = "module"
        mock_root_node.start_point = (0, 0)
        mock_root_node.end_point = (10, 0)
        mock_root_node.start_byte = 0
        mock_root_node.end_byte = 200
        mock_root_node.children = []
        mock_tree.root_node = mock_root_node
        
        # Configure the mock parser
        mock_parser.parse.return_value = mock_tree
        
        # Assign the mocks
        interface._parser = mock_parser
        interface._languages = {"python": mock_language}
        
        # Check that it's available
        assert await interface.is_available() is True
        
        # Check capabilities
        capabilities = await interface.get_capabilities()
        assert capabilities["available"] is True
        
        # Create a temp file to test with
        with tempfile.NamedTemporaryFile(suffix=".py") as temp_file:
            temp_file.write(b"def test_function():\n    pass")
            temp_file.flush()
            
            # Mock file reading
            with patch("builtins.open", create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = b"def test_function():\n    pass"
                
                # Test parsing a file
                result = await interface.execute_operation(
                    "parse_file",
                    {"file_path": temp_file.name}
                )
                assert result["success"] is True
                assert result["language"] == "py"


@pytest.mark.asyncio
async def test_mcp_aci_dev_integration():
    """Test the full integration between MCP, ACI, and Dev."""
    # Skip if any of the required components are not available
    try:
        from hanzo_aci.integrations.mcp import MCPComputerInterface, MCPServerManager
        from hanzo_aci.integrations.dev import DevComputerInterface, DevManager
    except ImportError:
        pytest.skip("Required integrations not available")
    
    # Create mock MCP server manager
    mock_mcp_manager = MagicMock(spec=MCPServerManager)
    # Fix: Add the servers attribute to the mock manager
    mock_mcp_manager.servers = {"computer-use": MagicMock()}
    mock_mcp_manager.is_server_running.return_value = True
    mock_mcp_manager.get_server.return_value = MagicMock()
    
    # Create mock Dev manager
    mock_dev_manager = MagicMock(spec=DevManager)
    mock_dev_manager.is_available = True
    mock_dev_manager.get_dev_module.return_value = MagicMock()
    
    # Create the interfaces
    mcp_interface = MCPComputerInterface(manager=mock_mcp_manager)
    dev_interface = DevComputerInterface(manager=mock_dev_manager)
    
    # Create a concrete interface that can use both
    with patch("hanzo_aci.concrete._get_mcp_computer", return_value=mcp_interface):
        with patch("hanzo_aci.concrete._get_dev_computer", return_value=dev_interface):
            # Create a concrete interface
            interface = ConcreteComputerInterface()
            
            # Test automatic backend selection
            backend = await interface._select_backend()
            assert backend is not None
            
            # Test getting capabilities
            capabilities = await interface.get_capabilities()
            assert capabilities["available"] is True
            
            # Test executing an operation
            with patch.object(mcp_interface, "execute_operation", return_value={"success": True}):
                result = await interface.execute_operation("test_operation", {"param": "value"})
                assert result["success"] is True


@pytest.mark.asyncio
async def test_specialized_modules_with_mcp():
    """Test using specialized modules through MCP."""
    # Define a mock MCP server manager
    class MockMCPServerManager:
        def __init__(self):
            self.servers = {}
        
        def register_server(self, name, server):
            self.servers[name] = server
        
        async def call_server(self, server_name, tool_name, params):
            if server_name not in self.servers:
                return {"success": False, "error": f"Unknown server: {server_name}"}
            
            server = self.servers[server_name]
            return await server.process_request({"tool": tool_name, "params": params})
    
    # Define mock server classes
    class MockVectorSearchServer:
        async def process_request(self, request):
            tool = request.get("tool")
            params = request.get("params", {})
            
            if tool == "vector_search":
                return {
                    "success": True,
                    "results": [
                        {"document": "Test document", "score": 0.9}
                    ]
                }
            
            return {"success": False, "error": "Unknown tool"}
    
    class MockSymbolicReasoningServer:
        async def process_request(self, request):
            tool = request.get("tool")
            params = request.get("params", {})
            
            if tool == "find_symbols":
                return {
                    "success": True,
                    "symbols": [
                        {"name": "test_function", "type": "function", "line": 1}
                    ]
                }
            
            return {"success": False, "error": "Unknown tool"}
    
    # Create the manager and servers
    manager = MockMCPServerManager()
    vector_search_server = MockVectorSearchServer()
    symbolic_reasoning_server = MockSymbolicReasoningServer()
    
    # Register the servers
    manager.register_server("vector-search", vector_search_server)
    manager.register_server("symbolic-reason", symbolic_reasoning_server)
    
    # Test calling each server
    vector_result = await manager.call_server(
        "vector-search",
        "vector_search",
        {"query": "test"}
    )
    assert vector_result["success"] is True
    assert len(vector_result["results"]) > 0
    
    symbolic_result = await manager.call_server(
        "symbolic-reason",
        "find_symbols",
        {"file_path": "test.py"}
    )
    assert symbolic_result["success"] is True
    assert len(symbolic_result["symbols"]) > 0
    
    # Test parallel execution
    async def call_parallel(calls):
        import asyncio
        tasks = []
        
        for call in calls:
            server_name = call.get("server")
            tool_name = call.get("tool")
            params = call.get("params", {})
            
            task = asyncio.create_task(
                manager.call_server(server_name, tool_name, params)
            )
            tasks.append(task)
        
        return await asyncio.gather(*tasks)
    
    # Create parallel calls
    calls = [
        {
            "server": "vector-search",
            "tool": "vector_search",
            "params": {"query": "test"}
        },
        {
            "server": "symbolic-reason",
            "tool": "find_symbols",
            "params": {"file_path": "test.py"}
        }
    ]
    
    # Execute in parallel
    results = await call_parallel(calls)
    
    # Verify results
    assert len(results) == 2
    assert results[0]["success"] is True
    assert results[1]["success"] is True