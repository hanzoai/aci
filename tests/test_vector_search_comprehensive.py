"""Comprehensive tests for the vector search interface."""

import os
import json
import pytest
import tempfile
from unittest.mock import MagicMock, patch, AsyncMock

# Use importorskip to conditionally run these tests
chromadb = pytest.importorskip("chromadb", reason="Vector database dependencies not available")
numpy = pytest.importorskip("numpy", reason="Numpy dependency not available")

from hanzo_aci.specialized.vector_search import VectorSearchInterface, _is_vectordb_available


class MockChromaCollection:
    """Mock ChromaDB collection for testing."""
    
    def __init__(self, name="test_collection"):
        """Initialize with a name."""
        self.name = name
        self.docs = []
        self.metadatas = []
        self.ids = []
    
    def add(self, documents, metadatas=None, ids=None):
        """Add documents to the collection."""
        self.docs.extend(documents)
        if metadatas:
            self.metadatas.extend(metadatas)
        if ids:
            self.ids.extend(ids)
    
    def query(self, query_texts, n_results=10, where=None, where_document=None):
        """Query the collection."""
        # Simple mock implementation that returns the first n_results
        n = min(n_results, len(self.docs))
        return {
            "documents": [self.docs[:n]],
            "metadatas": [self.metadatas[:n] if self.metadatas else [{}] * n],
            "distances": [[0.1 * i for i in range(n)]],
            "ids": [self.ids[:n] if self.ids else [f"id{i}" for i in range(n)]]
        }


class MockChromaClient:
    """Mock ChromaDB client for testing."""
    
    def __init__(self):
        """Initialize with collections."""
        self.collections = {}
    
    def get_or_create_collection(self, name):
        """Get or create a collection by name."""
        if name not in self.collections:
            self.collections[name] = MockChromaCollection(name)
        return self.collections[name]


@pytest.fixture
def vector_search_interface():
    """Create a vector search interface with a mock client."""
    with patch("chromadb.Client", return_value=MockChromaClient()):
        interface = VectorSearchInterface()
        interface._available = True
        interface._init_client()
        return interface


@pytest.mark.asyncio
async def test_is_vectordb_available():
    """Test checking if vector database dependencies are available."""
    with patch("importlib.util.find_spec", return_value=True):
        assert _is_vectordb_available() is True
    
    with patch("importlib.util.find_spec", return_value=None):
        assert _is_vectordb_available() is False


@pytest.mark.asyncio
async def test_init():
    """Test initialization with and without a collection path."""
    # Test with no collection path
    with patch("chromadb.Client", return_value=MockChromaClient()):
        interface = VectorSearchInterface()
        assert interface._client is None
        assert interface._collection is None
    
    # Test with collection path
    with patch("chromadb.Client", return_value=MockChromaClient()):
        with patch.object(VectorSearchInterface, "load_collection") as mock_load:
            interface = VectorSearchInterface("/path/to/collection")
            mock_load.assert_called_once_with("/path/to/collection")


@pytest.mark.asyncio
async def test_init_client():
    """Test initializing the ChromaDB client."""
    # Test when dependencies are available
    mock_client = MockChromaClient()
    with patch("chromadb.Client", return_value=mock_client):
        interface = VectorSearchInterface()
        interface._available = True
        interface._init_client()
        assert interface._client is not None
    
    # Test when dependencies are not available
    interface = VectorSearchInterface()
    interface._available = False
    interface._init_client()
    assert interface._client is None
    
    # Test when client initialization fails
    with patch("chromadb.Client", side_effect=Exception("Client error")):
        interface = VectorSearchInterface()
        interface._available = True
        interface._init_client()
        assert interface._client is None


@pytest.mark.asyncio
async def test_load_collection():
    """Test loading a collection."""
    # Test when dependencies are not available
    interface = VectorSearchInterface()
    interface._available = False
    result = interface.load_collection("/path/to/collection")
    assert result["success"] is False
    assert "not available" in result["error"]
    
    # Test when client is not initialized
    interface = VectorSearchInterface()
    interface._available = True
    interface._client = None
    with patch.object(interface, "_init_client") as mock_init:
        mock_init.return_value = None
        result = interface.load_collection("/path/to/collection")
        assert result["success"] is False
        assert "Failed to initialize" in result["error"]
    
    # Test successful loading
    mock_client = MockChromaClient()
    mock_collection = mock_client.get_or_create_collection("test_collection")
    
    interface = VectorSearchInterface()
    interface._available = True
    interface._client = mock_client
    
    result = interface.load_collection("/path/to/collection")
    assert result["success"] is True
    assert "collection" in result
    assert interface._collection is not None
    
    # Test loading with error
    interface = VectorSearchInterface()
    interface._available = True
    interface._client = mock_client
    with patch.object(mock_client, "get_or_create_collection", side_effect=Exception("Collection error")):
        result = interface.load_collection("/path/to/collection")
        assert result["success"] is False
        assert "Collection error" in result["error"]


@pytest.mark.asyncio
async def test_is_available():
    """Test checking if vector search is available."""
    interface = VectorSearchInterface()
    
    interface._available = True
    assert await interface.is_available() is True
    
    interface._available = False
    assert await interface.is_available() is False


@pytest.mark.asyncio
async def test_ensure_running():
    """Test ensuring vector search is running."""
    # Test when dependencies are not available
    interface = VectorSearchInterface()
    interface._available = False
    result = await interface.ensure_running()
    assert result["success"] is False
    assert "not available" in result["error"]
    
    # Test when client is not initialized
    interface = VectorSearchInterface()
    interface._available = True
    interface._client = None
    with patch.object(interface, "_init_client") as mock_init:
        mock_init.return_value = None
        result = await interface.ensure_running()
        assert result["success"] is False
        assert "Failed to initialize" in result["error"]
    
    # Test successful running
    mock_client = MockChromaClient()
    interface = VectorSearchInterface()
    interface._available = True
    interface._client = mock_client
    
    result = await interface.ensure_running()
    assert result["success"] is True
    assert "ready" in result["message"]


@pytest.mark.asyncio
async def test_get_capabilities():
    """Test getting capabilities."""
    # Test when dependencies are not available
    interface = VectorSearchInterface()
    interface._available = False
    result = await interface.get_capabilities()
    assert result["available"] is False
    assert "not available" in result["message"]
    
    # Test when dependencies are available
    interface = VectorSearchInterface()
    interface._available = True
    result = await interface.get_capabilities()
    assert result["available"] is True
    assert "operations" in result
    assert "vector_search" in result["operations"]
    assert "semantic_search" in result["operations"]
    assert "vector_index" in result["operations"]
    assert "hybrid_search" in result["operations"]
    
    # Test when collection is loaded
    interface = VectorSearchInterface()
    interface._available = True
    interface._collection = MockChromaCollection("test_collection")
    result = await interface.get_capabilities()
    assert result["available"] is True
    assert "collection" in result
    assert result["collection"] == "test_collection"


@pytest.mark.asyncio
async def test_execute_operation():
    """Test executing operations."""
    # Test when dependencies are not available
    interface = VectorSearchInterface()
    interface._available = False
    result = await interface.execute_operation("vector_search", {"query": "test"})
    assert result["success"] is False
    assert "not available" in result["error"]
    
    # Test unsupported operation
    interface = VectorSearchInterface()
    interface._available = True
    result = await interface.execute_operation("unsupported_operation", {})
    assert result["success"] is False
    assert "Unsupported operation" in result["error"]
    assert "available_operations" in result
    
    # Test supported operations
    interface = VectorSearchInterface()
    interface._available = True
    
    # Mock the operation methods
    interface._op_load_collection = AsyncMock(return_value={"success": True, "collection": "test"})
    interface._op_vector_search = AsyncMock(return_value={"success": True, "results": []})
    interface._op_semantic_search = AsyncMock(return_value={"success": True, "results": []})
    interface._op_vector_index = AsyncMock(return_value={"success": True, "indexed": 10})
    interface._op_hybrid_search = AsyncMock(return_value={"success": True, "results": []})
    
    # Test load_collection
    result = await interface.execute_operation("load_collection", {"path": "/test"})
    assert result["success"] is True
    interface._op_load_collection.assert_called_once_with({"path": "/test"})
    
    # Test vector_search
    result = await interface.execute_operation("vector_search", {"query": "test"})
    assert result["success"] is True
    interface._op_vector_search.assert_called_once_with({"query": "test"})
    
    # Test semantic_search
    result = await interface.execute_operation("semantic_search", {"text": "test"})
    assert result["success"] is True
    interface._op_semantic_search.assert_called_once_with({"text": "test"})
    
    # Test vector_index
    result = await interface.execute_operation("vector_index", {"documents": ["doc1", "doc2"]})
    assert result["success"] is True
    interface._op_vector_index.assert_called_once_with({"documents": ["doc1", "doc2"]})
    
    # Test hybrid_search
    result = await interface.execute_operation("hybrid_search", {"query": "test", "filter": {"key": "value"}})
    assert result["success"] is True
    interface._op_hybrid_search.assert_called_once_with({"query": "test", "filter": {"key": "value"}})


@pytest.mark.asyncio
async def test_op_load_collection():
    """Test the load_collection operation."""
    interface = VectorSearchInterface()
    
    # Test missing path parameter
    result = await interface._op_load_collection({})
    assert result["success"] is False
    assert "Path parameter is required" in result["error"]
    
    # Test with path parameter
    with patch.object(interface, "load_collection") as mock_load:
        mock_load.return_value = {"success": True, "collection": "test"}
        result = await interface._op_load_collection({"path": "/test"})
        assert result["success"] is True
        mock_load.assert_called_once_with("/test")


@pytest.mark.asyncio
async def test_op_vector_search(vector_search_interface):
    """Test the vector_search operation."""
    interface = vector_search_interface
    
    # Test when no collection is loaded
    interface._collection = None
    result = await interface._op_vector_search({"query": "test"})
    assert result["success"] is False
    assert "No collection loaded" in result["error"]
    
    # Test missing query parameter
    interface._collection = MockChromaCollection()
    result = await interface._op_vector_search({})
    assert result["success"] is False
    assert "Query parameter is required" in result["error"]
    
    # Test successful search
    interface._collection = MockChromaCollection()
    interface._collection.add(
        documents=["doc1", "doc2", "doc3"],
        metadatas=[{"source": "file1"}, {"source": "file2"}, {"source": "file3"}],
        ids=["id1", "id2", "id3"]
    )
    
    result = await interface._op_vector_search({"query": "test", "n_results": 2})
    assert result["success"] is True
    assert "results" in result
    assert len(result["results"]) == 2
    assert result["results"][0]["document"] == "doc1"
    assert result["results"][1]["document"] == "doc2"
    
    # Test with query error
    interface._collection = MockChromaCollection()
    with patch.object(interface._collection, "query", side_effect=Exception("Query error")):
        result = await interface._op_vector_search({"query": "test"})
        assert result["success"] is False
        assert "Query error" in result["error"]


@pytest.mark.asyncio
async def test_op_semantic_search(vector_search_interface):
    """Test the semantic_search operation (alias for vector_search)."""
    interface = vector_search_interface
    
    # Mock the vector_search operation
    interface._op_vector_search = AsyncMock(return_value={"success": True, "results": []})
    
    # Test with parameters
    result = await interface._op_semantic_search({"text": "test", "limit": 5})
    assert result["success"] is True
    interface._op_vector_search.assert_called_once_with({"query": "test", "n_results": 5})


@pytest.mark.asyncio
async def test_op_vector_index(vector_search_interface):
    """Test the vector_index operation."""
    interface = vector_search_interface
    
    # Test when no collection is loaded
    interface._collection = None
    result = await interface._op_vector_index({"documents": ["doc1", "doc2"]})
    assert result["success"] is False
    assert "No collection loaded" in result["error"]
    
    # Test missing documents parameter
    interface._collection = MockChromaCollection()
    result = await interface._op_vector_index({})
    assert result["success"] is False
    assert "Documents parameter is required" in result["error"]
    
    # Test successful indexing
    interface._collection = MockChromaCollection()
    result = await interface._op_vector_index({
        "documents": ["doc1", "doc2"],
        "metadatas": [{"source": "file1"}, {"source": "file2"}],
        "ids": ["id1", "id2"]
    })
    assert result["success"] is True
    assert "indexed" in result
    assert result["indexed"] == 2
    assert interface._collection.docs == ["doc1", "doc2"]
    assert interface._collection.metadatas == [{"source": "file1"}, {"source": "file2"}]
    assert interface._collection.ids == ["id1", "id2"]
    
    # Test with indexing error
    interface._collection = MockChromaCollection()
    with patch.object(interface._collection, "add", side_effect=Exception("Indexing error")):
        result = await interface._op_vector_index({"documents": ["doc1", "doc2"]})
        assert result["success"] is False
        assert "Indexing error" in result["error"]


@pytest.mark.asyncio
async def test_op_hybrid_search(vector_search_interface):
    """Test the hybrid_search operation."""
    interface = vector_search_interface
    
    # Test when no collection is loaded
    interface._collection = None
    result = await interface._op_hybrid_search({"query": "test"})
    assert result["success"] is False
    assert "No collection loaded" in result["error"]
    
    # Test missing query parameter
    interface._collection = MockChromaCollection()
    result = await interface._op_hybrid_search({})
    assert result["success"] is False
    assert "Query parameter is required" in result["error"]
    
    # Test successful search
    interface._collection = MockChromaCollection()
    interface._collection.add(
        documents=["doc1", "doc2", "doc3"],
        metadatas=[{"source": "file1"}, {"source": "file2"}, {"source": "file3"}],
        ids=["id1", "id2", "id3"]
    )
    
    result = await interface._op_hybrid_search({
        "query": "test",
        "filter": {"source": "file1"},
        "n_results": 2
    })
    assert result["success"] is True
    assert "results" in result
    assert "filter" in result
    assert result["filter"] == {"source": "file1"}
    
    # Test with query error
    interface._collection = MockChromaCollection()
    with patch.object(interface._collection, "query", side_effect=Exception("Query error")):
        result = await interface._op_hybrid_search({"query": "test"})
        assert result["success"] is False
        assert "Query error" in result["error"]


@pytest.mark.asyncio
async def test_real_use_case_scenario():
    """Test a real-world use case scenario."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a mock ChromaDB client and collection
        mock_client = MockChromaClient()
        mock_collection = mock_client.get_or_create_collection("test_collection")
        
        # Sample code snippets
        code_snippets = [
            "def process_payment(amount, currency):\n    return f'Processing {amount} {currency}'",
            "class Payment:\n    def __init__(self, amount):\n        self.amount = amount",
            "def calculate_tax(amount, rate):\n    return amount * rate",
            "# Function to handle refunds\ndef process_refund(payment_id):\n    return f'Refunding payment {payment_id}'",
            "# API endpoint for payments\ndef payment_api(request):\n    amount = request.get('amount')\n    return process_payment(amount, 'USD')"
        ]
        
        # Create metadata
        metadatas = [
            {"file": "payment.py", "line": 10, "type": "function"},
            {"file": "payment.py", "line": 15, "type": "class"},
            {"file": "tax.py", "line": 5, "type": "function"},
            {"file": "refund.py", "line": 12, "type": "function"},
            {"file": "api.py", "line": 25, "type": "function"}
        ]
        
        # Create sample files
        file_paths = []
        for i, snippet in enumerate(code_snippets):
            file_path = os.path.join(temp_dir, f"file_{i}.py")
            with open(file_path, "w") as f:
                f.write(snippet)
            file_paths.append(file_path)
        
        # Create the interface
        interface = VectorSearchInterface()
        interface._available = True
        interface._client = mock_client
        interface._collection = mock_collection
        
        # Index the code snippets
        await interface.execute_operation(
            "vector_index",
            {
                "documents": code_snippets,
                "metadatas": metadatas,
                "ids": [f"id_{i}" for i in range(len(code_snippets))]
            }
        )
        
        # Search for payment-related code
        search_result = await interface.execute_operation(
            "vector_search",
            {"query": "process payment", "n_results": 3}
        )
        
        # Check that the results contain payment-related code
        assert search_result["success"] is True
        assert len(search_result["results"]) == 3
        
        # There should be at least one result containing "payment" or "Payment"
        payment_results = [
            result for result in search_result["results"]
            if "payment" in result["document"].lower() or "Payment" in result["document"]
        ]
        assert len(payment_results) > 0
        
        # Try a hybrid search with a filter
        hybrid_search_result = await interface.execute_operation(
            "hybrid_search",
            {
                "query": "process payment",
                "filter": {"type": "function"},
                "n_results": 3
            }
        )
        
        # Check that the results are filtered correctly
        assert hybrid_search_result["success"] is True
        assert len(hybrid_search_result["results"]) == 3
        
        # All results should be functions
        for result in hybrid_search_result["results"]:
            assert result["metadata"]["type"] == "function"
