"""Tests for the vector search interface."""

import os
import pytest
import tempfile
from unittest.mock import MagicMock, patch

# Use pytest.importorskip to conditionally run tests
chromadb = pytest.importorskip("chromadb", reason="Vector database dependencies not available")

from hanzo_aci.specialized.vector_search import VectorSearchInterface


@pytest.fixture
def mock_chromadb_client():
    """Create a mock ChromaDB client."""
    client = MagicMock()
    collection = MagicMock()
    client.get_or_create_collection.return_value = collection
    return client, collection


@pytest.fixture
def vector_search_interface(mock_chromadb_client):
    """Create a vector search interface with a mock client."""
    client, collection = mock_chromadb_client
    
    # Patch the chromadb.Client constructor to return our mock
    with patch("chromadb.Client", return_value=client):
        interface = VectorSearchInterface()
        interface._client = client
        interface._collection = collection
        return interface


@pytest.mark.asyncio
async def test_is_available(vector_search_interface):
    """Test that the vector search interface is available."""
    with patch("hanzo_aci.specialized.vector_search._is_vectordb_available", return_value=True):
        result = await vector_search_interface.is_available()
        assert result is True


@pytest.mark.asyncio
async def test_ensure_running(vector_search_interface):
    """Test that ensure_running returns success."""
    with patch("hanzo_aci.specialized.vector_search._is_vectordb_available", return_value=True):
        result = await vector_search_interface.ensure_running()
        assert result["success"] is True


@pytest.mark.asyncio
async def test_get_capabilities(vector_search_interface):
    """Test that get_capabilities returns capabilities."""
    with patch("hanzo_aci.specialized.vector_search._is_vectordb_available", return_value=True):
        result = await vector_search_interface.get_capabilities()
        assert result["available"] is True
        assert "operations" in result


@pytest.mark.asyncio
async def test_load_collection(vector_search_interface, mock_chromadb_client):
    """Test loading a collection."""
    client, collection = mock_chromadb_client
    
    # Set the collection name property
    collection.name = "test_collection"
    
    # Call the load_collection operation
    result = await vector_search_interface.execute_operation(
        "load_collection",
        {"path": "/path/to/collection"}
    )
    
    # Verify the result
    assert result["success"] is True
    assert result["collection"] == "test_collection"
    
    # Verify the client method was called
    client.get_or_create_collection.assert_called_once()


@pytest.mark.asyncio
async def test_vector_search(vector_search_interface, mock_chromadb_client):
    """Test vector search operation."""
    client, collection = mock_chromadb_client
    
    # Mock the query results
    collection.query.return_value = {
        "documents": [["doc1", "doc2"]],
        "metadatas": [[{"source": "file1"}, {"source": "file2"}]],
        "distances": [[0.1, 0.2]],
        "ids": [["id1", "id2"]]
    }
    
    # Call the vector_search operation
    result = await vector_search_interface.execute_operation(
        "vector_search",
        {"query": "test query", "n_results": 2}
    )
    
    # Verify the result
    assert result["success"] is True
    assert len(result["results"]) == 2
    assert result["results"][0]["document"] == "doc1"
    assert result["results"][1]["document"] == "doc2"
    
    # Verify the collection method was called
    collection.query.assert_called_once_with(
        query_texts=["test query"],
        n_results=2
    )


@pytest.mark.asyncio
async def test_hybrid_search(vector_search_interface, mock_chromadb_client):
    """Test hybrid search operation."""
    client, collection = mock_chromadb_client
    
    # Mock the query results
    collection.query.return_value = {
        "documents": [["doc1", "doc2"]],
        "metadatas": [[{"source": "file1"}, {"source": "file2"}]],
        "distances": [[0.1, 0.2]],
        "ids": [["id1", "id2"]]
    }
    
    # Call the hybrid_search operation
    result = await vector_search_interface.execute_operation(
        "hybrid_search",
        {"query": "test query", "filter": {"source": "file1"}, "n_results": 2}
    )
    
    # Verify the result
    assert result["success"] is True
    assert len(result["results"]) == 2
    
    # Verify the collection method was called with the filter
    collection.query.assert_called_once_with(
        query_texts=["test query"],
        where={"source": "file1"},
        n_results=2
    )


@pytest.mark.asyncio
async def test_vector_index(vector_search_interface, mock_chromadb_client):
    """Test vector index operation."""
    client, collection = mock_chromadb_client
    
    # Call the vector_index operation
    result = await vector_search_interface.execute_operation(
        "vector_index",
        {"documents": ["doc1", "doc2"], "metadatas": [{"source": "file1"}, {"source": "file2"}]}
    )
    
    # Verify the result
    assert result["success"] is True
    assert result["indexed"] == 2
    
    # Verify the collection method was called
    collection.add.assert_called_once_with(
        documents=["doc1", "doc2"],
        metadatas=[{"source": "file1"}, {"source": "file2"}],
        ids=None
    )
