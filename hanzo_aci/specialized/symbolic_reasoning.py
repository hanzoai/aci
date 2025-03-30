"""Symbolic reasoning module for Hanzo ACI.

This module provides symbolic code reasoning capabilities using tree-sitter.
It can be installed with the 'symbolic' extra dependency.
"""

import os
import logging
import importlib.util
from typing import Dict, List, Optional, Any, Union

from hanzo_aci.interface import ComputerInterface

logger = logging.getLogger(__name__)


def _is_symbolic_available() -> bool:
    """Check if symbolic reasoning dependencies are available."""
    try:
        import tree_sitter
        return True
    except ImportError:
        return False


class SymbolicReasoningInterface(ComputerInterface):
    """Symbolic reasoning interface for code analysis."""
    
    def __init__(self):
        """Initialize the symbolic reasoning interface."""
        self._available = _is_symbolic_available()
        self._parser = None
        self._languages = {}
        
        if self._available:
            self._init_parser()
            self._load_languages()
    
    def _init_parser(self):
        """Initialize the tree-sitter parser."""
        if not self._available:
            return
            
        try:
            import tree_sitter
            self._parser = tree_sitter.Parser()
        except Exception as e:
            logger.error(f"Failed to initialize tree-sitter parser: {e}")
            self._parser = None
    
    def _load_languages(self):
        """Load language-specific parsers."""
        if not self._available or not self._parser:
            return
            
        # Try to load installed language libraries
        languages_to_try = {
            "python": "tree_sitter_python",
            "javascript": "tree_sitter_javascript",
            "go": "tree_sitter_go",
            "rust": "tree_sitter_rust"
        }
        
        for lang_name, module_name in languages_to_try.items():
            try:
                if importlib.util.find_spec(module_name):
                    module = importlib.import_module(module_name)
                    if hasattr(module, "language"):
                        self._languages[lang_name] = module.language()
                        logger.debug(f"Loaded language: {lang_name}")
            except Exception as e:
                logger.debug(f"Failed to load language {lang_name}: {e}")
    
    def _get_language_for_file(self, file_path: str):
        """Get the appropriate language for a file based on extension.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            Language object or None.
        """
        if not self._available:
            return None
            
        ext = os.path.splitext(file_path)[1].lower()
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "javascript",  # Using JavaScript parser for TypeScript
            ".tsx": "javascript",
            ".go": "go",
            ".rs": "rust"
        }
        
        if ext in ext_map and ext_map[ext] in self._languages:
            return self._languages[ext_map[ext]]
            
        return None
    
    async def is_available(self) -> bool:
        """Check if symbolic reasoning is available.
        
        Returns:
            True if symbolic reasoning is available, False otherwise.
        """
        return self._available
    
    async def ensure_running(self) -> Dict[str, Any]:
        """Ensure that symbolic reasoning is running and ready.
        
        Returns:
            Dictionary with status information.
        """
        if not self._available:
            return {
                "success": False, 
                "error": "Symbolic reasoning dependencies not available. Install with pip install 'hanzo-aci[symbolic]'"
            }
            
        if not self._parser:
            self._init_parser()
            if not self._parser:
                return {"success": False, "error": "Failed to initialize tree-sitter parser"}
                
        return {"success": True, "message": "Symbolic reasoning is ready"}
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get information about symbolic reasoning capabilities.
        
        Returns:
            Dictionary with capability information.
        """
        if not self._available:
            return {
                "available": False,
                "message": "Symbolic reasoning dependencies not available. Install with pip install 'hanzo-aci[symbolic]'"
            }
            
        capabilities = {
            "available": True,
            "operations": [
                "parse_file",
                "find_symbols",
                "find_references",
                "analyze_dependencies"
            ],
            "languages": list(self._languages.keys())
        }
            
        return capabilities
    
    async def execute_operation(
        self,
        operation: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a symbolic reasoning operation.
        
        Args:
            operation: Operation to execute.
            params: Parameters for the operation.
            
        Returns:
            Operation result.
        """
        if not self._available:
            return {
                "success": False, 
                "error": "Symbolic reasoning dependencies not available. Install with pip install 'hanzo-aci[symbolic]'"
            }
            
        operations = {
            "parse_file": self._op_parse_file,
            "find_symbols": self._op_find_symbols,
            "find_references": self._op_find_references,
            "analyze_dependencies": self._op_analyze_dependencies
        }
        
        if operation not in operations:
            return {
                "success": False,
                "error": f"Unsupported operation: {operation}",
                "available_operations": list(operations.keys())
            }
            
        return await operations[operation](params)
    
    async def _op_parse_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a file and extract its syntax tree.
        
        Args:
            params: Parameters including 'file_path'.
            
        Returns:
            Parsed syntax tree information.
        """
        file_path = params.get("file_path")
        if not file_path:
            return {"success": False, "error": "File path parameter is required"}
            
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}
            
        try:
            # Get the appropriate language
            lang = self._get_language_for_file(file_path)
            if not lang:
                return {"success": False, "error": f"Unsupported file type: {file_path}"}
                
            # Set the language for the parser
            self._parser.set_language(lang)
            
            # Read the file content
            with open(file_path, 'rb') as f:
                content = f.read()
                
            # Parse the file
            tree = self._parser.parse(content)
            
            # Return a simplified representation
            return {
                "success": True,
                "file_path": file_path,
                "language": os.path.splitext(file_path)[1].lstrip('.'),
                "root_node": {
                    "type": tree.root_node.type,
                    "start_point": tree.root_node.start_point,
                    "end_point": tree.root_node.end_point,
                    "child_count": len(tree.root_node.children)
                },
                "parse_time": tree.root_node.end_byte / 1000,  # Approximate parse time in ms
                "size": len(content)
            }
        except Exception as e:
            logger.error(f"Parse file failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _op_find_symbols(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Find symbols (functions, classes, variables) in a file.
        
        Args:
            params: Parameters including 'file_path'.
            
        Returns:
            List of found symbols.
        """
        file_path = params.get("file_path")
        symbol_type = params.get("symbol_type")  # Optional filter for symbol type
        
        if not file_path:
            return {"success": False, "error": "File path parameter is required"}
            
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}
            
        try:
            # Get the appropriate language
            lang = self._get_language_for_file(file_path)
            if not lang:
                return {"success": False, "error": f"Unsupported file type: {file_path}"}
                
            # Set the language for the parser
            self._parser.set_language(lang)
            
            # Read the file content
            with open(file_path, 'rb') as f:
                content = f.read()
                
            # Parse the file
            tree = self._parser.parse(content)
            
            # Extract symbols based on language
            language_name = os.path.splitext(file_path)[1].lstrip('.')
            
            # Example simplified symbol extraction (would need language-specific implementation)
            symbols = []
            
            # Define queries based on language
            if language_name == "py":
                # Python symbols: functions and classes
                function_query = "function_definition name: (identifier) @name"
                class_query = "class_definition name: (identifier) @name"
                
                import tree_sitter
                
                # Get functions
                func_query = tree_sitter.Query(lang, function_query)
                query_captures = func_query.captures(tree.root_node)
                
                for node, tag in query_captures:
                    if tag == "name":
                        name = content[node.start_byte:node.end_byte].decode('utf-8')
                        parent = node.parent
                        start_line, start_col = parent.start_point
                        
                        if not symbol_type or symbol_type == "function":
                            symbols.append({
                                "name": name,
                                "type": "function",
                                "line": start_line + 1,
                                "column": start_col + 1,
                                "start_byte": parent.start_byte,
                                "end_byte": parent.end_byte
                            })
                
                # Get classes
                class_query = tree_sitter.Query(lang, class_query)
                query_captures = class_query.captures(tree.root_node)
                
                for node, tag in query_captures:
                    if tag == "name":
                        name = content[node.start_byte:node.end_byte].decode('utf-8')
                        parent = node.parent
                        start_line, start_col = parent.start_point
                        
                        if not symbol_type or symbol_type == "class":
                            symbols.append({
                                "name": name,
                                "type": "class",
                                "line": start_line + 1,
                                "column": start_col + 1,
                                "start_byte": parent.start_byte,
                                "end_byte": parent.end_byte
                            })
            else:
                # Simplified fallback for other languages
                # Find top-level declarations as best effort
                for child in tree.root_node.children:
                    if child.type in ["function_definition", "method_definition", "class_definition"]:
                        # Try to extract name
                        name = None
                        for c in child.children:
                            if c.type == "identifier":
                                name = content[c.start_byte:c.end_byte].decode('utf-8')
                                break
                        
                        if name:
                            symbols.append({
                                "name": name,
                                "type": child.type.replace("_definition", ""),
                                "line": child.start_point[0] + 1,
                                "column": child.start_point[1] + 1,
                                "start_byte": child.start_byte,
                                "end_byte": child.end_byte
                            })
            
            return {
                "success": True,
                "file_path": file_path,
                "language": language_name,
                "symbol_count": len(symbols),
                "symbols": symbols
            }
        except Exception as e:
            logger.error(f"Find symbols failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _op_find_references(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Find references to a symbol in a file.
        
        Args:
            params: Parameters including 'file_path' and 'symbol_name'.
            
        Returns:
            List of references to the symbol.
        """
        file_path = params.get("file_path")
        symbol_name = params.get("symbol_name")
        
        if not file_path or not symbol_name:
            return {"success": False, "error": "File path and symbol name parameters are required"}
            
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}
            
        try:
            # Get the appropriate language
            lang = self._get_language_for_file(file_path)
            if not lang:
                return {"success": False, "error": f"Unsupported file type: {file_path}"}
                
            # Set the language for the parser
            self._parser.set_language(lang)
            
            # Read the file content
            with open(file_path, 'rb') as f:
                content = f.read()
                
            # Parse the file
            tree = self._parser.parse(content)
            
            # Find references (simplified implementation)
            references = []
            
            # For each identifier node in the tree
            import tree_sitter
            
            query_string = f"(identifier) @id"
            query = tree_sitter.Query(lang, query_string)
            
            query_captures = query.captures(tree.root_node)
            for node, tag in query_captures:
                name = content[node.start_byte:node.end_byte].decode('utf-8')
                if name == symbol_name:
                    line_start = 0
                    for i, byte in enumerate(content):
                        if i >= node.start_byte:
                            break
                        if byte == ord(b'\n'):
                            line_start = i + 1
                    
                    # Extract context (line of code)
                    line_end = content.find(ord(b'\n'), node.start_byte)
                    if line_end == -1:
                        line_end = len(content)
                    
                    line = content[line_start:line_end].decode('utf-8')
                    
                    references.append({
                        "line": node.start_point[0] + 1,
                        "column": node.start_point[1] + 1,
                        "start_byte": node.start_byte,
                        "end_byte": node.end_byte,
                        "context": line.strip()
                    })
            
            return {
                "success": True,
                "file_path": file_path,
                "symbol_name": symbol_name,
                "reference_count": len(references),
                "references": references
            }
        except Exception as e:
            logger.error(f"Find references failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _op_analyze_dependencies(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze dependencies between symbols in a file.
        
        Args:
            params: Parameters including 'file_path'.
            
        Returns:
            List of dependencies between symbols.
        """
        file_path = params.get("file_path")
        
        if not file_path:
            return {"success": False, "error": "File path parameter is required"}
            
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}
            
        try:
            # First, find all symbols in the file
            symbols_result = await self._op_find_symbols({"file_path": file_path})
            if not symbols_result["success"]:
                return symbols_result
                
            symbols = symbols_result["symbols"]
            
            # Get the appropriate language
            lang = self._get_language_for_file(file_path)
            if not lang:
                return {"success": False, "error": f"Unsupported file type: {file_path}"}
                
            # Set the language for the parser
            self._parser.set_language(lang)
            
            # Read the file content
            with open(file_path, 'rb') as f:
                content = f.read()
                
            # Parse the file
            tree = self._parser.parse(content)
            
            # Find dependencies (simplified implementation)
            dependencies = []
            
            # Extract dependencies based on symbol references
            for symbol in symbols:
                # For each symbol, find references to other symbols
                symbol_name = symbol["name"]
                references_result = await self._op_find_references({
                    "file_path": file_path,
                    "symbol_name": symbol_name
                })
                
                if not references_result["success"]:
                    continue
                    
                # Find which other symbols are referenced in this symbol's definition
                symbol_body_start = symbol["start_byte"]
                symbol_body_end = symbol["end_byte"]
                
                for other_symbol in symbols:
                    if other_symbol["name"] == symbol_name:
                        continue  # Skip self-references
                        
                    # Check if this symbol's name is mentioned in the body of the original symbol
                    other_name = other_symbol["name"]
                    
                    # Simple approach: check if the name appears in the symbol body
                    body_content = content[symbol_body_start:symbol_body_end]
                    if other_name.encode('utf-8') in body_content:
                        # Found a potential dependency
                        dependencies.append({
                            "from": symbol_name,
                            "to": other_name,
                            "type": "reference"
                        })
            
            return {
                "success": True,
                "file_path": file_path,
                "symbol_count": len(symbols),
                "dependency_count": len(dependencies),
                "dependencies": dependencies
            }
        except Exception as e:
            logger.error(f"Analyze dependencies failed: {e}")
            return {"success": False, "error": str(e)}


# Create a singleton instance
symbolic_reasoning = SymbolicReasoningInterface()
