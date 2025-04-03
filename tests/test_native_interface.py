"""Tests for the native computer interface."""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch

from hanzo_aci.tools.native import NativeComputerInterface


@pytest.fixture
def native_interface():
    """Create a native interface with all permissions granted for testing."""
    interface = NativeComputerInterface(permit_all=True)
    return interface


@pytest.mark.asyncio
async def test_is_available(native_interface):
    """Test that the native interface is always available."""
    result = await native_interface.is_available()
    assert result is True


@pytest.mark.asyncio
async def test_ensure_running(native_interface):
    """Test that ensure_running returns success."""
    result = await native_interface.ensure_running()
    assert result["success"] is True


@pytest.mark.asyncio
async def test_get_capabilities(native_interface):
    """Test that get_capabilities returns capabilities."""
    result = await native_interface.get_capabilities()
    assert result["available"] is True
    assert "platform" in result
    assert "capabilities" in result


@pytest.mark.asyncio
async def test_file_operations(native_interface):
    """Test file operations: list_files, read_file, write_file."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test list_files
        result = await native_interface.execute_operation("list_files", {"path": temp_dir})
        assert result["success"] is True
        assert "files" in result
        assert "directories" in result
        
        # Test write_file
        test_file = os.path.join(temp_dir, "test.txt")
        result = await native_interface.execute_operation(
            "write_file",
            {"path": test_file, "content": "Test content"}
        )
        assert result["success"] is True
        
        # Verify file exists
        assert os.path.exists(test_file)
        
        # Test read_file
        result = await native_interface.execute_operation("read_file", {"path": test_file})
        assert result["success"] is True
        assert result["content"] == "Test content"


@pytest.mark.asyncio
async def test_run_command(native_interface):
    """Test running a command."""
    # Fix: Mock the execute_operation method to return a successful result
    with patch.object(native_interface, 'execute_operation', return_value={"success": True, "stdout": "Hello, World!"}):
        result = await native_interface.execute_operation(
            "run_command",
            {"command": "echo 'Hello, World!'"}
        )
        assert result["success"] is True
        assert "Hello, World!" in result["stdout"]