"""Tests for the concrete computer interface."""

import os
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from hanzo_aci.concrete import ConcreteComputerInterface
from hanzo_aci.tools.native import NativeComputerInterface


@pytest.fixture
def native_interface():
    """Create a native interface with all permissions granted for testing."""
    interface = NativeComputerInterface(permit_all=True)
    return interface


@pytest.fixture
def mock_mcp_computer():
    """Create a mock MCP computer interface."""
    mock = AsyncMock()
    mock.is_available.return_value = True
    mock.ensure_running.return_value = {"success": True}
    mock.get_capabilities.return_value = {
        "available": True,
        "backend": "mcp"
    }
    mock.execute_operation.return_value = {"success": True, "result": "mcp_result"}
    return mock


@pytest.fixture
def mock_dev_computer():
    """Create a mock Dev computer interface."""
    mock = AsyncMock()
    mock.is_available.return_value = True
    mock.ensure_running.return_value = {"success": True}
    mock.get_capabilities.return_value = {
        "available": True,
        "backend": "dev"
    }
    mock.execute_operation.return_value = {"success": True, "result": "dev_result"}
    return mock


@pytest.fixture
def mock_claude_code_computer():
    """Create a mock Claude Code computer interface."""
    mock = AsyncMock()
    mock.is_available.return_value = True
    mock.ensure_running.return_value = {"success": True}
    mock.get_capabilities.return_value = {
        "available": True,
        "backend": "claude_code"
    }
    mock.execute_operation.return_value = {"success": True, "result": "claude_code_result"}
    return mock


@pytest.mark.asyncio
async def test_init_default():
    """Test initializing with default parameters."""
    interface = ConcreteComputerInterface()
    assert interface.backend is None
    assert isinstance(interface.native_interface, NativeComputerInterface)


@pytest.mark.asyncio
async def test_init_with_backend():
    """Test initializing with specific backend."""
    interface = ConcreteComputerInterface(backend="native")
    assert interface.backend == "native"


@pytest.mark.asyncio
async def test_init_with_custom_native():
    """Test initializing with a custom native interface."""
    custom_native = NativeComputerInterface(permit_all=False)
    interface = ConcreteComputerInterface(native_interface=custom_native)
    assert interface.native_interface is custom_native


@pytest.mark.asyncio
async def test_select_backend_native():
    """Test selecting the native backend."""
    interface = ConcreteComputerInterface(backend="native")
    backend = await interface._select_backend()
    assert backend is interface.native_interface


@pytest.mark.asyncio
async def test_select_backend_mcp(mock_mcp_computer):
    """Test selecting the MCP backend."""
    with patch("hanzo_aci.concrete._get_mcp_computer", return_value=mock_mcp_computer):
        interface = ConcreteComputerInterface(backend="mcp")
        backend = await interface._select_backend()
        assert backend is mock_mcp_computer


@pytest.mark.asyncio
async def test_select_backend_dev(mock_dev_computer):
    """Test selecting the Dev backend."""
    with patch("hanzo_aci.concrete._get_dev_computer", return_value=mock_dev_computer):
        interface = ConcreteComputerInterface(backend="dev")
        backend = await interface._select_backend()
        assert backend is mock_dev_computer


@pytest.mark.asyncio
async def test_select_backend_claude_code(mock_claude_code_computer):
    """Test selecting the Claude Code backend."""
    with patch("hanzo_aci.concrete._get_claude_code_computer", return_value=mock_claude_code_computer):
        interface = ConcreteComputerInterface(backend="claude_code")
        backend = await interface._select_backend()
        assert backend is mock_claude_code_computer


@pytest.mark.asyncio
async def test_select_backend_unknown():
    """Test selecting an unknown backend falls back to native."""
    interface = ConcreteComputerInterface(backend="unknown")
    backend = await interface._select_backend()
    assert backend is interface.native_interface


@pytest.mark.asyncio
async def test_select_backend_auto_mcp(mock_mcp_computer):
    """Test auto-selecting MCP when available."""
    with patch("hanzo_aci.concrete._get_mcp_computer", return_value=mock_mcp_computer):
        interface = ConcreteComputerInterface()
        backend = await interface._select_backend()
        assert backend is mock_mcp_computer


@pytest.mark.asyncio
async def test_select_backend_auto_dev(mock_dev_computer):
    """Test auto-selecting Dev when MCP not available."""
    with patch("hanzo_aci.concrete._get_mcp_computer", return_value=None):
        with patch("hanzo_aci.concrete._get_dev_computer", return_value=mock_dev_computer):
            interface = ConcreteComputerInterface()
            backend = await interface._select_backend()
            assert backend is mock_dev_computer


@pytest.mark.asyncio
async def test_select_backend_auto_claude_code(mock_claude_code_computer):
    """Test auto-selecting Claude Code when MCP and Dev not available."""
    with patch("hanzo_aci.concrete._get_mcp_computer", return_value=None):
        with patch("hanzo_aci.concrete._get_dev_computer", return_value=None):
            with patch("hanzo_aci.concrete._get_claude_code_computer", return_value=mock_claude_code_computer):
                interface = ConcreteComputerInterface()
                backend = await interface._select_backend()
                assert backend is mock_claude_code_computer


@pytest.mark.asyncio
async def test_select_backend_auto_native():
    """Test auto-selecting native when no others available."""
    with patch("hanzo_aci.concrete._get_mcp_computer", return_value=None):
        with patch("hanzo_aci.concrete._get_dev_computer", return_value=None):
            with patch("hanzo_aci.concrete._get_claude_code_computer", return_value=None):
                interface = ConcreteComputerInterface()
                backend = await interface._select_backend()
                assert backend is interface.native_interface


@pytest.mark.asyncio
async def test_is_available():
    """Test is_available delegates to selected backend."""
    mock_backend = AsyncMock()
    mock_backend.is_available.return_value = True
    
    interface = ConcreteComputerInterface()
    with patch.object(interface, "_select_backend", return_value=mock_backend):
        result = await interface.is_available()
        assert result is True
        mock_backend.is_available.assert_called_once()


@pytest.mark.asyncio
async def test_ensure_running():
    """Test ensure_running delegates to selected backend."""
    mock_backend = AsyncMock()
    mock_backend.ensure_running.return_value = {"success": True, "message": "Running"}
    
    interface = ConcreteComputerInterface()
    with patch.object(interface, "_select_backend", return_value=mock_backend):
        result = await interface.ensure_running()
        assert result["success"] is True
        assert result["message"] == "Running"
        mock_backend.ensure_running.assert_called_once()


@pytest.mark.asyncio
async def test_get_capabilities():
    """Test get_capabilities adds backend information."""
    mock_backend = AsyncMock()
    mock_backend.get_capabilities.return_value = {
        "available": True,
        "capabilities": ["test_capability"]
    }
    
    interface = ConcreteComputerInterface()
    
    # Test with native interface
    with patch.object(interface, "_select_backend", return_value=interface.native_interface):
        result = await interface.get_capabilities()
        assert result["available"] is True
        assert result["backend"] == "native"
    
    # Test with MCP interface - FIX: Create a proper mock with the required module
    mcp_mock = AsyncMock()
    mcp_mock.get_capabilities.return_value = {
        "available": True,
        "capabilities": ["test_capability"]
    }
    mcp_mock.__class__.__module__ = "hanzo_aci.integrations.mcp"
    
    with patch.object(interface, "_select_backend", return_value=mcp_mock):
        with patch("hanzo_aci.concrete.isinstance", return_value=False):
            result = await interface.get_capabilities()
            assert result["available"] is True
            assert result["backend"] == "mcp"
    
    # Test with Dev interface - FIX: Create a proper mock with the required module
    dev_mock = AsyncMock()
    dev_mock.get_capabilities.return_value = {
        "available": True,
        "capabilities": ["test_capability"]
    }
    dev_mock.__class__.__module__ = "hanzo_aci.integrations.dev"
    
    with patch.object(interface, "_select_backend", return_value=dev_mock):
        with patch("hanzo_aci.concrete.isinstance", return_value=False):
            result = await interface.get_capabilities()
            assert result["available"] is True
            assert result["backend"] == "dev"
    
    # Test with Claude Code interface - FIX: Create a proper mock with the required module
    claude_mock = AsyncMock()
    claude_mock.get_capabilities.return_value = {
        "available": True,
        "capabilities": ["test_capability"]
    }
    claude_mock.__class__.__module__ = "hanzo_aci.integrations.claude_code"
    
    with patch.object(interface, "_select_backend", return_value=claude_mock):
        with patch("hanzo_aci.concrete.isinstance", return_value=False):
            result = await interface.get_capabilities()
            assert result["available"] is True
            assert result["backend"] == "claude_code"
    
    # Test with unknown interface - FIX: Create a proper mock with the required module
    unknown_mock = AsyncMock()
    unknown_mock.get_capabilities.return_value = {
        "available": True,
        "capabilities": ["test_capability"]
    }
    unknown_mock.__class__.__module__ = "unknown"
    
    with patch.object(interface, "_select_backend", return_value=unknown_mock):
        with patch("hanzo_aci.concrete.isinstance", return_value=False):
            result = await interface.get_capabilities()
            assert result["available"] is True
            assert result["backend"] == "unknown"


@pytest.mark.asyncio
async def test_execute_operation():
    """Test execute_operation delegates to selected backend."""
    mock_backend = AsyncMock()
    mock_backend.execute_operation.return_value = {"success": True, "result": "test_result"}
    
    interface = ConcreteComputerInterface()
    with patch.object(interface, "_select_backend", return_value=mock_backend):
        result = await interface.execute_operation("test_operation", {"param": "value"})
        assert result["success"] is True
        assert result["result"] == "test_result"
        mock_backend.execute_operation.assert_called_once_with("test_operation", {"param": "value"})


@pytest.mark.asyncio
async def test_backend_unavailable_fallback():
    """Test falling back when requested backend is unavailable."""
    mock_mcp = AsyncMock()
    mock_mcp.is_available.return_value = False
    
    interface = ConcreteComputerInterface(backend="mcp")
    
    with patch("hanzo_aci.concrete._get_mcp_computer", return_value=mock_mcp):
        backend = await interface._select_backend()
        assert backend is interface.native_interface


@pytest.mark.asyncio
async def test_helper_methods_delegation():
    """Test helper methods delegate to execute_operation."""
    interface = ConcreteComputerInterface()
    # FIX: Use the correct argument style for the mock
    mock_execute = AsyncMock()
    
    with patch.object(interface, "execute_operation", mock_execute):
        # Test list_files
        await interface.list_files("/path")
        # FIX: Check for keyword arguments instead of positional arguments
        assert mock_execute.call_args.kwargs['operation'] == "list_files"
        assert mock_execute.call_args.kwargs['params'] == {"path": "/path"}
        mock_execute.reset_mock()
        
        # Test read_file
        await interface.read_file("/path/file.txt")
        assert mock_execute.call_args.kwargs['operation'] == "read_file"
        assert mock_execute.call_args.kwargs['params'] == {"path": "/path/file.txt"}
        mock_execute.reset_mock()
        
        # Test write_file
        await interface.write_file("/path/file.txt", "content")
        assert mock_execute.call_args.kwargs['operation'] == "write_file"
        assert mock_execute.call_args.kwargs['params'] == {"path": "/path/file.txt", "content": "content"}
        mock_execute.reset_mock()
        
        # Test run_command
        await interface.run_command("ls -la", "/path")
        assert mock_execute.call_args.kwargs['operation'] == "run_command"
        assert mock_execute.call_args.kwargs['params'] == {"command": "ls -la", "cwd": "/path"}
        mock_execute.reset_mock()
        
        # Test vector_search
        await interface.vector_search("query", "/project", 5)
        assert mock_execute.call_args.kwargs['operation'] == "vector_search"
        assert mock_execute.call_args.kwargs['params'] == {
            "query_text": "query", 
            "project_dir": "/project", 
            "n_results": 5
        }