"""Vector search module for Hanzo ACI.

This module provides vector database search capabilities using chromadb.
It can be installed with the 'vectordb' extra dependency.
"""

import os
import logging
import importlib.util
from typing import Dict, List, Optional, Any, Union

from hanzo_aci.interface import ComputerInterface

logger = logging.getLogger(__name__)


def _is_vectordb_available() -> bool:
    """Check if vectordb dependencies are available."""
    try:
        import chromadb
        import numpy
        return True
    except ImportError:
        return False


class VectorSearchInterface(ComputerInterface):
    """Vector search interface for semantic code search."""
    
    def __init__(self, collection_path: Optional[str] = None):
        """Initialize the vector search interface.
        
        Args:
            collection_path: Optional path to a ChromaDB collection.
        """
        self._client = None
        self._collection = None
        self._available = _is_vectordb_available()
        
        if self._available and collection_path:
            self._init_client()
            self.load_collection(collection_path)
    
    def _init_client(self):
        """Initialize the ChromaDB client."""
        if not self._available:
            return
            
        try:
            import chromadb
            self._client = chromadb.Client()
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}")
            self._client = None
    
    def load_collection(self, path: str) -> Dict[str, Any]:
        """Load a collection from the given path.
        
        Args:
            path: Path to the collection.
            
        Returns:
            Status dictionary.
        """
        if not self._available:
            return {
                "success": False, 
                "error": "Vector database dependencies not available. Install with pip install 'hanzo-aci[vectordb]'"
            }
            
        if not self._client:
            self._init_client()
            if not self._client:
                return {"success": False, "error": "Failed to initialize ChromaDB client"}
                
        try:
            # Normalize path for collection name
            collection_name = f"code_collection_{path.replace('/', '_').replace('.', '_')}"
            self._collection = self._client.get_or_create_collection(name=collection_name)
            return {"success": True, "collection": collection_name}
        except Exception as e:
            logger.error(f"Failed to load collection: {e}")
            return {"success": False, "error": str(e)}
    
    async def is_available(self) -> bool:
        """Check if vector search is available.
        
        Returns:
            True if vector search is available, False otherwise.
        """
        return self._available
    
    async def ensure_running(self) -> Dict[str, Any]:
        """Ensure that vector search is running and ready.
        
        Returns:
            Dictionary with status information.
        """
        if not self._available:
            return {
                "success": False, 
                "error": "Vector database dependencies not available. Install with pip install 'hanzo-aci[vectordb]'"
            }
            
        if not self._client:
            self._init_client()
            if not self._client:
                return {"success": False, "error": "Failed to initialize ChromaDB client"}
                
        return {"success": True, "message": "Vector search is ready"}
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get information about vector search capabilities.
        
        Returns:
            Dictionary with capability information.
        """
        if not self._available:
            return {
                "available": False,
                "message": "Vector database dependencies not available. Install with pip install 'hanzo-aci[vectordb]'"
            }
            
        capabilities = {
            "available": True,
            "operations": [
                "vector_search",
                "semantic_search",
                "vector_index",
                "hybrid_search"
            ]
        }
        
        if self._collection:
            capabilities["collection"] = self._collection.name
            
        return capabilities
    
    async def execute_operation(
        self,
        operation: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a vector search operation.
        
        Args:
            operation: Operation to execute.
            params: Parameters for the operation.
            
        Returns:
            Operation result.
        """
        if not self._available:
            return {
                "success": False, 
                "error": "Vector database dependencies not available. Install with pip install 'hanzo-aci[vectordb]'"
            }
            
        operations = {
            "load_collection": self._op_load_collection,
            "vector_search": self._op_vector_search,
            "semantic_search": self._op_semantic_search,
            "vector_index": self._op_vector_index,
            "hybrid_search": self._op_hybrid_search
        }
        
        if operation not in operations:
            return {
                "success": False,
                "error": f"Unsupported operation: {operation}",
                "available_operations": list(operations.keys())
            }
            
        return await operations[operation](params)
    
    async def _op_load_collection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Load a collection operation.
        
        Args:
            params: Parameters including 'path'.
            
        Returns:
            Operation result.
        """
        path = params.get("path")
        if not path:
            return {"success": False, "error": "Path parameter is required"}
            
        return self.load_collection(path)
    
    async def _op_vector_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform vector search operation.
        
        Args:
            params: Parameters including 'query', 'n_results'.
            
        Returns:
            Search results.
        """
        if not self._collection:
            return {"success": False, "error": "No collection loaded. Call load_collection first."}
            
        query = params.get("query")
        n_results = params.get("n_results", 10)
        
        if not query:
            return {"success": False, "error": "Query parameter is required"}
            
        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Format results for JSON response
            formatted_results = []
            
            if results["documents"] and len(results["documents"]) > 0:
                for i, doc in enumerate(results["documents"][0]):
                    formatted_results.append({
                        "document": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] and i < len(results["metadatas"][0]) else {},
                        "distance": results["distances"][0][i] if results["distances"] and i < len(results["distances"][0]) else None,
                        "id": results["ids"][0][i] if results["ids"] and i < len(results["ids"][0]) else None
                    })
                    
            return {
                "success": True,
                "results": formatted_results,
                "query": query
            }
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _op_semantic_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Alias for vector_search with different parameter names.
        
        Args:
            params: Parameters including 'text', 'limit'.
            
        Returns:
            Search results.
        """
        # Remap parameters for compatibility with different naming conventions
        return await self._op_vector_search({
            "query": params.get("text"),
            "n_results": params.get("limit", 10)
        })
    
    async def _op_vector_index(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Index content in the vector database.
        
        Args:
            params: Parameters including 'documents', 'metadatas', 'ids'.
            
        Returns:
            Indexing result.
        """
        if not self._collection:
            return {"success": False, "error": "No collection loaded. Call load_collection first."}
            
        documents = params.get("documents", [])
        metadatas = params.get("metadatas", [])
        ids = params.get("ids", [])
        
        if not documents:
            return {"success": False, "error": "Documents parameter is required"}
            
        try:
            self._collection.add(
                documents=documents,
                metadatas=metadatas if metadatas else None,
                ids=ids if ids else None
            )
            
            return {
                "success": True,
                "indexed": len(documents),
                "message": f"Successfully indexed {len(documents)} documents"
            }
        except Exception as e:
            logger.error(f"Vector indexing failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _op_hybrid_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform hybrid search combining vector search with keyword filters.
        
        Args:
            params: Parameters including 'query', 'filter', 'n_results'.
            
        Returns:
            Search results.
        """
        if not self._collection:
            return {"success": False, "error": "No collection loaded. Call load_collection first."}
            
        query = params.get("query")
        filter_dict = params.get("filter", {})
        n_results = params.get("n_results", 10)
        
        if not query:
            return {"success": False, "error": "Query parameter is required"}
            
        try:
            results = self._collection.query(
                query_texts=[query],
                where=filter_dict,
                n_results=n_results
            )
            
            # Format results for JSON response
            formatted_results = []
            
            if results["documents"] and len(results["documents"]) > 0:
                for i, doc in enumerate(results["documents"][0]):
                    formatted_results.append({
                        "document": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] and i < len(results["metadatas"][0]) else {},
                        "distance": results["distances"][0][i] if results["distances"] and i < len(results["distances"][0]) else None,
                        "id": results["ids"][0][i] if results["ids"] and i < len(results["ids"][0]) else None
                    })
                    
            return {
                "success": True,
                "results": formatted_results,
                "query": query,
                "filter": filter_dict
            }
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return {"success": False, "error": str(e)}


# Create a singleton instance
vector_search = VectorSearchInterface()
