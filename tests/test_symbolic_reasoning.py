"""Tests for the symbolic reasoning interface."""

import os
import pytest
import tempfile
from unittest.mock import MagicMock, patch

# Use pytest.importorskip to conditionally run tests
tree_sitter = pytest.importorskip("tree_sitter", reason="Symbolic reasoning dependencies not available")

from hanzo_aci.specialized.symbolic_reasoning import SymbolicReasoningInterface


class MockNode:
    """Mock tree-sitter node for testing."""
    
    def __init__(self, type_name, start_point=(0, 0), end_point=(0, 0), 
                 start_byte=0, end_byte=0, children=None):
        self.type = type_name
        self.start_point = start_point
        self.end_point = end_point
        self.start_byte = start_byte
        self.end_byte = end_byte
        self.children = children or []
        self.parent = None
        
        # Set parent for children
        for child in self.children:
            child.parent = self


class MockTree:
    """Mock tree-sitter tree for testing."""
    
    def __init__(self, root_node):
        self.root_node = root_node


class MockQuery:
    """Mock tree-sitter query for testing."""
    
    def __init__(self, captures):
        self.captures = captures
    
    def captures(self, node):
        return self.captures


@pytest.fixture
def mock_tree_sitter_parser():
    """Create a mock tree-sitter parser."""
    parser = MagicMock()
    
    # Create a simple syntax tree
    identifier_node = MockNode("identifier", start_point=(1, 4), end_point=(1, 15),
                              start_byte=12, end_byte=23)
    function_node = MockNode("function_definition", start_point=(1, 0), end_point=(5, 0),
                            start_byte=8, end_byte=100, children=[identifier_node])
    root_node = MockNode("module", start_point=(0, 0), end_point=(10, 0),
                        start_byte=0, end_byte=200, children=[function_node])
    
    # Create a tree with the root node
    tree = MockTree(root_node)
    
    # Configure parser to return the tree
    parser.parse.return_value = tree
    
    return parser


@pytest.fixture
def mock_language():
    """Create a mock tree-sitter language."""
    language = MagicMock()
    return language


@pytest.fixture
def symbolic_reasoning_interface(mock_tree_sitter_parser, mock_language):
    """Create a symbolic reasoning interface with mocks."""
    with patch("hanzo_aci.specialized.symbolic_reasoning._is_symbolic_available", return_value=True):
        interface = SymbolicReasoningInterface()
        interface._parser = mock_tree_sitter_parser
        interface._languages = {"python": mock_language}
        return interface


@pytest.mark.asyncio
async def test_is_available(symbolic_reasoning_interface):
    """Test that the symbolic reasoning interface is available."""
    with patch("hanzo_aci.specialized.symbolic_reasoning._is_symbolic_available", return_value=True):
        result = await symbolic_reasoning_interface.is_available()
        assert result is True


@pytest.mark.asyncio
async def test_ensure_running(symbolic_reasoning_interface):
    """Test that ensure_running returns success."""
    with patch("hanzo_aci.specialized.symbolic_reasoning._is_symbolic_available", return_value=True):
        result = await symbolic_reasoning_interface.ensure_running()
        assert result["success"] is True


@pytest.mark.asyncio
async def test_get_capabilities(symbolic_reasoning_interface):
    """Test that get_capabilities returns capabilities."""
    with patch("hanzo_aci.specialized.symbolic_reasoning._is_symbolic_available", return_value=True):
        result = await symbolic_reasoning_interface.get_capabilities()
        assert result["available"] is True
        assert "operations" in result
        assert "languages" in result


@pytest.mark.asyncio
async def test_parse_file(symbolic_reasoning_interface, mock_tree_sitter_parser):
    """Test parsing a file."""
    # Create a temporary Python file
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w") as temp_file:
        temp_file.write("def example_function():\n    return 'Hello, World!'")
        temp_file.flush()
        
        # Mock file reading
        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = b"def example_function():\n    return 'Hello, World!'"
            
            # Call the parse_file operation
            result = await symbolic_reasoning_interface.execute_operation(
                "parse_file",
                {"file_path": temp_file.name}
            )
            
            # Verify the result
            assert result["success"] is True
            assert "root_node" in result
            assert result["language"] == "py"
            
            # Verify the parser was called
            mock_tree_sitter_parser.parse.assert_called_once()


@pytest.mark.asyncio
async def test_find_symbols(symbolic_reasoning_interface, mock_tree_sitter_parser):
    """Test finding symbols in a file."""
    # Create a temporary Python file
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w") as temp_file:
        temp_file.write("def example_function():\n    return 'Hello, World!'")
        temp_file.flush()
        
        # Mock file reading
        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = b"def example_function():\n    return 'Hello, World!'"
            
            # Mock Query class
            captures = [(
                MockNode("identifier", start_byte=4, end_byte=20),
                "name"
            )]
            query_instance = MockQuery(captures)
            
            with patch("tree_sitter.Query", return_value=query_instance):
                # Call the find_symbols operation
                result = await symbolic_reasoning_interface.execute_operation(
                    "find_symbols",
                    {"file_path": temp_file.name}
                )
                
                # Verify the result
                assert result["success"] is True
                assert "symbols" in result
                assert len(result["symbols"]) > 0


@pytest.mark.asyncio
async def test_find_references(symbolic_reasoning_interface, mock_tree_sitter_parser):
    """Test finding references to a symbol."""
    # Create a temporary Python file
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w") as temp_file:
        content = "def example_function():\n    return 'Hello, World!'\n\nexample_function()"
        temp_file.write(content)
        temp_file.flush()
        
        # Mock file reading
        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = content.encode('utf-8')
            
            # Mock Query class
            captures = [
                (MockNode("identifier", start_point=(0, 4), end_point=(0, 20), 
                         start_byte=4, end_byte=20), "id"),
                (MockNode("identifier", start_point=(3, 0), end_point=(3, 16), 
                         start_byte=50, end_byte=66), "id")
            ]
            query_instance = MockQuery(captures)
            
            with patch("tree_sitter.Query", return_value=query_instance):
                # Mock content.find method
                with patch("bytes.find", return_value=70):
                    # Call the find_references operation
                    result = await symbolic_reasoning_interface.execute_operation(
                        "find_references",
                        {
                            "file_path": temp_file.name,
                            "symbol_name": "example_function"
                        }
                    )
                    
                    # Verify the result
                    assert result["success"] is True
                    assert "references" in result
                    assert len(result["references"]) > 0


@pytest.mark.asyncio
async def test_analyze_dependencies(symbolic_reasoning_interface):
    """Test analyzing dependencies between symbols."""
    # Create a temporary Python file
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w") as temp_file:
        content = """
def helper_function():
    return 'Helper'

def main_function():
    result = helper_function()
    return result
"""
        temp_file.write(content)
        temp_file.flush()
        
        # Mock the find_symbols operation
        async def mock_find_symbols(params):
            return {
                "success": True,
                "symbols": [
                    {
                        "name": "helper_function",
                        "type": "function",
                        "line": 2,
                        "start_byte": 1,
                        "end_byte": 40
                    },
                    {
                        "name": "main_function",
                        "type": "function",
                        "line": 5,
                        "start_byte": 42,
                        "end_byte": 110
                    }
                ]
            }
        
        symbolic_reasoning_interface._op_find_symbols = mock_find_symbols
        
        # Mock the file reading
        with patch("builtins.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = content.encode('utf-8')
            mock_open.return_value.__enter__.return_value = mock_file
            
            # Call the analyze_dependencies operation
            result = await symbolic_reasoning_interface.execute_operation(
                "analyze_dependencies",
                {"file_path": temp_file.name}
            )
            
            # Verify the result
            assert result["success"] is True
            assert "dependencies" in result
            # We expect to find that main_function depends on helper_function
            assert any(d["from"] == "main_function" and d["to"] == "helper_function" 
                      for d in result["dependencies"])


@pytest.mark.asyncio
async def test_unsupported_operation(symbolic_reasoning_interface):
    """Test that an unsupported operation returns an error."""
    result = await symbolic_reasoning_interface.execute_operation(
        "unsupported_operation",
        {}
    )
    
    assert result["success"] is False
    assert "error" in result
    assert "available_operations" in result
