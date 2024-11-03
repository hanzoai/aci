"""Type analysis module for Oh-Viewer"""

import ast
from dataclasses import dataclass
import re
from typing import Dict, List, Optional, Set, Tuple
from tree_sitter import Node, Tree


@dataclass
class TypeInfo:
  """Type information for a symbol"""

  name: str
  type_hint: Optional[str] = None
  inferred_type: Optional[str] = None
  possible_types: Set[str] = None

  def __post_init__(self):
    if self.possible_types is None:
      self.possible_types = set()


class TypeAnalyzer:
  """Analyzes and infers types in code"""

  def __init__(self, language_support):
    self.language_support = language_support
    self.type_cache: Dict[str, Dict[str, TypeInfo]] = {}

  def analyze_file(self, file_path: str, content: str) -> Dict[str, TypeInfo]:
    """Analyze types in a file"""
    language = self.language_support.get_language_by_extension(file_path)
    if not language:
      return {}

    if file_path in self.type_cache:
      return self.type_cache[file_path]

    types = {}

    if language == 'python':
      types = self._analyze_python(content)
    elif language in ['javascript', 'typescript']:
      types = self._analyze_javascript(content)
    # Add more language analyzers here

    self.type_cache[file_path] = types
    return types

  def _analyze_python(self, content: str) -> Dict[str, TypeInfo]:
    """Analyze Python types using ast and type hints"""
    types = {}

    try:
      tree = ast.parse(content)
      for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign):
          # Handle type annotations
          if isinstance(node.target, ast.Name):
            type_info = TypeInfo(
                name=node.target.id,
                type_hint=ast.unparse(node.annotation),
            )
            types[node.target.id] = type_info

        elif isinstance(node, ast.FunctionDef):
          # Handle function return types and arguments
          return_type = None
          if node.returns:
            return_type = ast.unparse(node.returns)

          type_info = TypeInfo(
              name=node.name,
              type_hint=f'Callable[...] -> {return_type}'
              if return_type
              else 'Callable',
          )
          types[node.name] = type_info

          # Handle arguments
          for arg in node.args.args:
            if arg.annotation:
              arg_type = ast.unparse(arg.annotation)
              types[arg.arg] = TypeInfo(
                  name=arg.arg,
                  type_hint=arg_type,
              )

        elif isinstance(node, ast.ClassDef):
          # Handle class definitions
          bases = [ast.unparse(base) for base in node.bases]
          type_info = TypeInfo(
              name=node.name,
              type_hint='type',
              possible_types=set(bases) if bases else {'object'},
          )
          types[node.name] = type_info

    except Exception as e:
      print(f'Error analyzing Python types: {e}')

    return types

  def _analyze_javascript(self, content: str) -> Dict[str, TypeInfo]:
    """Analyze JavaScript/TypeScript types"""
    types = {}

    # Look for JSDoc comments and TypeScript annotations
    type_patterns = [
        r'@type\s+{([^}]+)}',  # JSDoc @type
        r'@param\s+{([^}]+)}\s+(\w+)',  # JSDoc @param
        r'@returns?\s+{([^}]+)}',  # JSDoc @returns
        r':\s*([A-Za-z<>[\]|]+)\s*[=;]',  # TypeScript type annotations
    ]

    for pattern in type_patterns:
      for match in re.finditer(pattern, content):
        if len(match.groups()) == 2:  # @param case
          type_str, name = match.groups()
          types[name] = TypeInfo(
              name=name,
              type_hint=type_str,
          )
        else:
          type_str = match.group(1)
          # Extract variable name from context
          prev_line = content[: match.start()].splitlines()[-1]
          var_match = re.search(r'\b(\w+)\s*:', prev_line)
          if var_match:
            name = var_match.group(1)
            types[name] = TypeInfo(
                name=name,
                type_hint=type_str,
            )

    return types

  def infer_type(self, node: Node, content: str) -> Optional[str]:
    """Infer type from usage context"""
    if not node:
      return None

    parent = node.parent
    if not parent:
      return None

    # Infer from assignment
    if parent.type == 'assignment':
      right_node = parent.child_by_field_name('right')
      if right_node:
        if right_node.type == 'string':
          return 'str'
        elif right_node.type in ['integer', 'float']:
          return 'number'
        elif right_node.type == 'array':
          return 'array'
        elif right_node.type == 'dictionary':
          return 'object'
        elif right_node.type == 'true' or right_node.type == 'false':
          return 'boolean'

    # Infer from function call
    elif parent.type == 'call':
      func_name = parent.child_by_field_name('function')
      if func_name:
        if func_name.text.decode() in ['str', 'int', 'float', 'list', 'dict']:
          return func_name.text.decode()

    return None

  def get_type_info(self, file_path: str, symbol: str) -> Optional[TypeInfo]:
    """Get type information for a symbol"""
    types = self.type_cache.get(file_path, {})
    return types.get(symbol)
