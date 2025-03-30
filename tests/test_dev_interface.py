"""Tests for the Dev computer interface."""

import os
import pytest
import tempfile
from unittest.mock import MagicMock, patch

from hanzo_aci.integrations.dev import DevComputerInterface, DevManager


@pytest.fixture
def mock_dev_manager():
    """Create a mocked Dev manager."""
    manager = MagicMock(spec=DevManager)
    manager.is_available = True
    manager.get_dev_module.return_value = MagicMock()
    manager.initialize_dev.return_value = {"success": True, "message": "Initialized"}
    return manager


@pytest.fixture
def dev_interface(mock_dev_manager):
    """Create a Dev interface with a mocked manager."""
    interface = DevComputerInterface(manager=mock_dev_manager)
    interface.dev = mock_dev_manager.get_dev_module()
    return interface


@pytest.mark.asyncio
async def test_is_available(dev_interface, mock_dev_manager):
    """Test that availability depends on the manager."""
    result = await dev_interface.is_available()
    assert result is True
    
    # Test unavailable
    mock_dev_manager.is_available = False
    result = await dev_interface.is_available()
    assert result is False


@pytest.mark.asyncio
async def test_ensure_running(dev_interface, mock_dev_manager):
    """Test ensuring that the interface is running."""
    mock_dev_manager.initialize_dev = MagicMock(return_value={"success": True, "message": "Initialized"})
    
    result = await dev_interface.ensure_running()
    assert result["success"] is True
    mock_dev_manager.initialize_dev.assert_called_once()
    
    # Test unavailable
    mock_dev_manager.is_available = False
    result = await dev_interface.ensure_running()
    assert result["success"] is False
    assert "not available" in result["error"]


@pytest.mark.asyncio
async def test_get_capabilities(dev_interface, mock_dev_manager):
    """Test getting capabilities when available."""
    result = await dev_interface.get_capabilities()
    assert result["available"] is True
    assert result["backend"] == "dev"
    assert "capabilities" in result
    
    # Test unavailable
    mock_dev_manager.is_available = False
    result = await dev_interface.get_capabilities()
    assert result["available"] is False


@pytest.mark.asyncio
async def test_execute_operation_unavailable(dev_interface, mock_dev_manager):
    """Test executing an operation when the dev module is not available."""
    mock_dev_manager.is_available = False
    
    result = await dev_interface.execute_operation("list_files", {"path": "."})
    assert result["success"] is False
    assert "not available" in result["error"]


@pytest.mark.asyncio
async def test_execute_operation_not_supported(dev_interface):
    """Test executing an unsupported operation."""
    result = await dev_interface.execute_operation("unsupported_operation", {})
    assert result["success"] is False
    assert "not supported" in result["error"]
    assert "available_operations" in result


@pytest.mark.asyncio
async def test_list_files(dev_interface):
    """Test listing files operation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create some test files
        open(os.path.join(temp_dir, "test1.txt"), "w").close()
        open(os.path.join(temp_dir, "test2.txt"), "w").close()
        os.mkdir(os.path.join(temp_dir, "subdir"))
        
        # Patch the _list_files method to use the actual implementation 
        # rather than the mocked one
        with patch.object(dev_interface, "_list_files", wraps=dev_interface._list_files):
            result = await dev_interface.execute_operation("list_files", {"path": temp_dir})
        
        assert result["success"] is True
        assert "test1.txt" in result["files"]
        assert "test2.txt" in result["files"]
        assert "subdir" in result["directories"]


@pytest.mark.asyncio
async def test_read_write_file(dev_interface):
    """Test reading and writing files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test.txt")
        test_content = "This is a test file."
        
        # Test writing
        with patch.object(dev_interface, "_write_file", wraps=dev_interface._write_file):
            write_result = await dev_interface.execute_operation(
                "write_file", {"path": test_file, "content": test_content}
            )
        
        assert write_result["success"] is True
        assert os.path.exists(test_file)
        
        # Test reading
        with patch.object(dev_interface, "_read_file", wraps=dev_interface._read_file):
            read_result = await dev_interface.execute_operation(
                "read_file", {"path": test_file}
            )
        
        assert read_result["success"] is True
        assert read_result["content"] == test_content


@pytest.mark.asyncio
async def test_edit_file(dev_interface):
    """Test editing a file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = os.path.join(temp_dir, "test.txt")
        initial_content = "Line 1\nLine 2\nLine 3\n"
        
        # Create the file
        with open(test_file, "w") as f:
            f.write(initial_content)
        
        # Test editing
        edits = [
            {"oldText": "Line 2\n", "newText": "Modified Line 2\n"}
        ]
        
        with patch.object(dev_interface, "_edit_file", wraps=dev_interface._edit_file):
            edit_result = await dev_interface.execute_operation(
                "edit_file", {"path": test_file, "edits": edits}
            )
        
        assert edit_result["success"] is True
        
        # Verify content
        with open(test_file, "r") as f:
            content = f.read()
        
        assert content == "Line 1\nModified Line 2\nLine 3\n"


@pytest.mark.asyncio
async def test_run_command(dev_interface):
    """Test running a command."""
    with patch.object(dev_interface, "_run_command", wraps=dev_interface._run_command):
        result = await dev_interface.execute_operation(
            "run_command", {"command": "echo 'Hello, World!'"}
        )
    
    assert result["success"] is True
    assert "Hello, World!" in result["stdout"]
    assert result["returncode"] == 0


@pytest.mark.asyncio
async def test_vector_operations(dev_interface):
    """Test vector operations."""
    # Mock vector_search implementation
    async def mock_vector_search(params):
        return {
            "success": True,
            "results": [
                {"source": "example.py", "content": "Example content", "similarity": 0.95}
            ]
        }
    
    # Mock vector_index implementation
    async def mock_vector_index(params):
        return {
            "success": True,
            "indexed_files": 5,
            "message": f"Indexed {params.get('path')} (recursive={params.get('recursive', True)})"
        }
    
    dev_interface._vector_search = mock_vector_search
    dev_interface._vector_index = mock_vector_index
    
    # Test vector search
    search_result = await dev_interface.execute_operation(
        "vector_search",
        {"query_text": "example", "project_dir": "."}
    )
    
    assert search_result["success"] is True
    assert len(search_result["results"]) > 0
    
    # Test vector index
    index_result = await dev_interface.execute_operation(
        "vector_index",
        {"path": ".", "recursive": True}
    )
    
    assert index_result["success"] is True
    assert index_result["indexed_files"] > 0


@pytest.mark.asyncio
async def test_symbol_operations(dev_interface):
    """Test symbol operations."""
    # Mock symbol_find implementation
    async def mock_symbol_find(params):
        return {
            "success": True,
            "symbols": [
                {"name": "example_function", "type": "function", "file": "example.py", "line": 10}
            ]
        }
    
    # Mock symbol_search implementation
    async def mock_symbol_search(params):
        return {
            "success": True,
            "symbols": [
                {"name": "example_function", "type": "function", "file": "example.py", "line": 10}
            ]
        }
    
    dev_interface._symbol_find = mock_symbol_find
    dev_interface._symbol_search = mock_symbol_search
    
    # Test symbol find
    find_result = await dev_interface.execute_operation(
        "symbol_find",
        {"path": ".", "symbol_name": "example_function"}
    )
    
    assert find_result["success"] is True
    assert len(find_result["symbols"]) > 0
    
    # Test symbol search
    search_result = await dev_interface.execute_operation(
        "symbol_search",
        {"pattern": "example", "path": "."}
    )
    
    assert search_result["success"] is True
    assert len(search_result["symbols"]) > 0
