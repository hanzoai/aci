"""Code intelligence module for Oh-Viewer"""

from dataclasses import dataclass
import os
from pathlib import Path
import re
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class SymbolLocation:
  """Location information for a symbol."""

  file_path: str
  line: int
  column: int
  end_line: int
  end_column: int


@dataclass
class SymbolInfo:
  """Information about a symbol."""

  name: str
  kind: str  # 'function', 'class', 'variable', etc.
  location: SymbolLocation
  references: List[SymbolLocation]
  documentation: Optional[str] = None


class CodeIntelligence:
  """Provides code intelligence features."""

  def __init__(
      self, language_support, type_analyzer, workspace_root: str = None
  ):
    self.language_support = language_support
    self.type_analyzer = type_analyzer
    self.workspace_root = workspace_root or os.getcwd()
    self.symbol_cache: Dict[str, Dict[str, SymbolInfo]] = {}
    self.import_graph: Dict[str, Set[str]] = {}
    self.import_map: Dict[str, str] = {}

  def index_workspace(self, workspace_path: str):
    """Index all files in the workspace."""
    print(f"Indexing workspace: {workspace_path}")
    for root, _, files in os.walk(workspace_path):
      for file in files:
        file_path = os.path.join(root, file)
        print(f"Indexing file: {file_path}")
        self._index_file(file_path)

  def _index_file(self, file_path: str):
    """Index a single file."""
    try:
      language = self.language_support.get_language_by_extension(file_path)
      if not language:
        return

      with open(file_path, 'r') as f:
        content = f.read()

      parser = self.language_support.get_parser(language)
      if not parser:
        return

      tree = parser.parse(bytes(content, 'utf8'))

      # Index symbols
      symbols = {}
      self._collect_symbols(tree.root_node, content, file_path, symbols)
      self.symbol_cache[file_path] = symbols

      # Build import graph
      imports = self._collect_imports(tree.root_node, content, file_path)
      self.import_graph[file_path] = imports

    except Exception as e:
      print(f'Error indexing {file_path}: {e}')

  def _collect_symbols(
      self, node, content: str, file_path: str, symbols: Dict[str, SymbolInfo]
  ):
    """Collect symbols from AST."""
    if node.type in [
        'function_definition',
        'class_definition',
        'method_definition',
    ]:
      name_node = next(
          (child for child in node.children if child.type == 'identifier'), None
      )
      if name_node:
        name = name_node.text.decode()
        location = SymbolLocation(
            file_path=file_path,
            line=node.start_point[0] + 1,
            column=node.start_point[1],
            end_line=node.end_point[0] + 1,
            end_column=node.end_point[1],
        )

        symbol_info = SymbolInfo(
            name=name,
            kind=node.type.replace('_definition', ''),
            location=location,
            references=[],
        )
        symbols[name] = symbol_info

    for child in node.children:
      self._collect_symbols(child, content, file_path, symbols)

  def _collect_imports(self, node, content: str, file_path: str) -> Set[str]:
    """Collect imported files."""
    imports = set()
    if node.type == 'import_statement':
      # Handle Python-style imports
      for child in node.children:
        if child.type == 'dotted_name':
          module_path = child.text.decode().replace('.', '/')
          # Try both relative and absolute paths
          rel_path = os.path.join(os.path.dirname(file_path), module_path + '.py')
          abs_path = os.path.join(self.workspace_root, module_path + '.py')

          if os.path.exists(rel_path):
            imports.add(rel_path)
          elif os.path.exists(abs_path):
            imports.add(abs_path)

    elif node.type == 'import_from_statement':
      # Handle from ... import ...
      module = None
      for child in node.children:
        if child.type == 'dotted_name':
          module = child.text.decode()
          module_path = module.replace('.', '/')
          # Try both relative and absolute paths
          rel_path = os.path.join(os.path.dirname(file_path), module_path + '.py')
          abs_path = os.path.join(self.workspace_root, module_path + '.py')

          if os.path.exists(rel_path):
            imports.add(rel_path)
          elif os.path.exists(abs_path):
            imports.add(abs_path)
        elif child.type == 'import_from_statement' and module:
          for name in child.children:
            if name.type == 'identifier':
              self.import_map[name.text.decode()] = module_path + '.py'

    elif node.type == 'import_declaration':
      # Handle JavaScript-style imports
      source = next(
          (child for child in node.children if child.type == 'string'), None
      )
      if source:
        path = source.text.decode().strip('"\'')
        if not path.endswith('.js'):
          path += '.js'
        # Try both relative and absolute paths
        rel_path = os.path.join(os.path.dirname(file_path), path)
        abs_path = os.path.join(self.workspace_root, path)

        if os.path.exists(rel_path):
          imports.add(rel_path)
        elif os.path.exists(abs_path):
          imports.add(abs_path)

    for child in node.children:
      imports.update(self._collect_imports(child, content, file_path))

    return imports

  def find_definition(
      self, symbol: str, current_file: str
  ) -> Optional[SymbolLocation]:
    """Find definition of a symbol."""
    # Check current file first
    file_symbols = self.symbol_cache.get(current_file, {})
    if symbol in file_symbols:
      return file_symbols[symbol].location

    # Check if symbol is imported
    if symbol in self.import_map:
      imported_file = self.import_map[symbol]
      # Try both relative and absolute paths
      rel_path = os.path.join(os.path.dirname(current_file), imported_file)
      abs_path = os.path.join(self.workspace_root, imported_file)

      if os.path.exists(rel_path):
        file_symbols = self.symbol_cache.get(rel_path, {})
        if symbol in file_symbols:
          return file_symbols[symbol].location

      if os.path.exists(abs_path):
        file_symbols = self.symbol_cache.get(abs_path, {})
        if symbol in file_symbols:
          return file_symbols[symbol].location

    # Check all imported files
    for imported_file in self.import_graph.get(current_file, set()):
      file_symbols = self.symbol_cache.get(imported_file, {})
      if symbol in file_symbols:
        return file_symbols[symbol].location

    return None

  def find_references(
      self, symbol: str, current_file: str
  ) -> List[SymbolLocation]:
    """Find all references to a symbol."""
    print(f"Finding references for {symbol} in {current_file}")
    references = []

    # Find symbol definition first
    definition = self.find_definition(symbol, current_file)
    print(f"Definition found: {definition}")
    if not definition:
      return references

    def_file = definition.file_path

    # Search in all workspace files
    for root, _, files in os.walk(self.workspace_root):
      for file in files:
        if not file.endswith('.py'):  # Add more extensions as needed
          continue

        file_path = os.path.join(root, file)
        print(f"Checking file: {file_path}")

        # Check for references in this file
        refs = self._find_references_in_file(symbol, file_path)
        print(f"Found references in {file_path}: {refs}")
        references.extend(refs)

    return references

  def _find_references_in_file(
      self, symbol: str, file_path: str
  ) -> List[SymbolLocation]:
    """Find references in a single file."""
    references = []
    try:
      with open(file_path, 'r') as f:
        content = f.read()

      language = self.language_support.get_language_by_extension(file_path)
      if not language:
        return references

      parser = self.language_support.get_parser(language)
      if not parser:
        return references

      tree = parser.parse(bytes(content, 'utf8'))

      def visit(node):
        if node.type == 'identifier' and node.text.decode() == symbol:
          # Only exclude the identifier in the function/class name position
          is_definition = False
          if node.parent.type in [
              'function_definition',
              'class_definition',
              'method_definition',
          ]:
              # Check if this is the name identifier
              for child in node.parent.children:
                  if child.type == 'identifier' and child.text == node.text:
                      is_definition = True
                      break

          if not is_definition:
              references.append(
                  SymbolLocation(
                      file_path=file_path,
                      line=node.start_point[0] + 1,
                      column=node.start_point[1],
                      end_line=node.end_point[0] + 1,
                      end_column=node.end_point[1],
                  )
              )

        for child in node.children:
          visit(child)

      visit(tree.root_node)

    except Exception as e:
      print(f'Error finding references in {file_path}: {e}')

    return references

  def get_call_hierarchy(self, function: str, file_path: str) -> Dict:
    """Get call hierarchy for a function."""
    hierarchy = {'callers': [], 'callees': []}

    # Find function definition
    definition = self.find_definition(function, file_path)
    if not definition:
      return hierarchy

    # Find who calls this function
    for ref in self.find_references(function, file_path):
      if ref.file_path == definition.file_path:
        continue
      caller = self._get_enclosing_function(ref.file_path, ref.line)
      if caller:
        hierarchy['callers'].append(caller)

    # Find what this function calls
    try:
      with open(definition.file_path, 'r') as f:
        content = f.read()

      language = self.language_support.get_language_by_extension(file_path)
      if language and (parser := self.language_support.get_parser(language)):
        tree = parser.parse(bytes(content, 'utf8'))
        func_node = self._find_node_at_line(tree.root_node, definition.line)
        if func_node:
          self._collect_callees(func_node, hierarchy['callees'])
    except Exception as e:
      print(f'Error analyzing call hierarchy: {e}')

    return hierarchy

  def _get_enclosing_function(self, file_path: str, line: int) -> Optional[str]:
    """Find the function that encloses a line."""
    file_symbols = self.symbol_cache.get(file_path, {})
    for symbol in file_symbols.values():
      if (
          symbol.kind == 'function'
          and symbol.location.line <= line <= symbol.location.end_line
      ):
        return symbol.name
    return None

  def _find_node_at_line(self, node, line: int):
    """Find node at a specific line."""
    if node.start_point[0] + 1 <= line <= node.end_point[0] + 1:
      for child in node.children:
        result = self._find_node_at_line(child, line)
        if result:
          return result
      return node
    return None

  def _collect_callees(self, node, callees: List[str]):
    """Collect function calls within a node."""
    if node.type == 'call_expression':
      func = node.child_by_field_name('function')
      if func and func.type == 'identifier':
        callees.append(func.text.decode())

    for child in node.children:
      self._collect_callees(child, callees)
