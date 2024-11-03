"""Core functionality for Oh-Viewer"""

from dataclasses import dataclass
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .code_intelligence import CodeIntelligence, SymbolLocation
from .documentation import DocumentationExtractor
from .language_support import LanguageSupport
from .type_analyzer import TypeAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class JumpTarget:
  """Represents a location to jump to"""

  file_path: str
  line: int
  column: int
  symbol: str
  kind: str  # 'definition', 'reference', 'implementation'


class FileViewer:
  """Main file viewer class with code intelligence features"""

  def __init__(self, workspace_path: str = None):
    self.current_file = None
    self.current_position = 0
    self.lines = []
    self.workspace_path = workspace_path or os.getcwd()

    # Initialize components
    self.language_support = LanguageSupport()
    self.type_analyzer = TypeAnalyzer(self.language_support)
    self.code_intelligence = CodeIntelligence(
        self.language_support,
        self.type_analyzer,
        workspace_root=self.workspace_path,
    )
    self.doc_extractor = DocumentationExtractor(self.language_support)

    # Index workspace
    if workspace_path:
      self.code_intelligence.index_workspace(workspace_path)

  def load_file(self, filepath: str) -> bool:
    """Load a file into the viewer"""
    try:
      with open(filepath, 'r') as f:
        self.content = f.read()
        self.lines = self.content.splitlines()
      self.current_file = filepath
      self.current_position = 0

      # Analyze file
      self.type_analyzer.analyze_file(filepath, self.content)
      self.doc_extractor.extract_docs(filepath, self.content)

      return True
    except Exception as e:
      logger.error(f'Error loading file: {e}')
      return False

  def get_directory_structure(
      self, path: str = None, max_depth: int = None
  ) -> Dict:
    """Return a dictionary representing the directory structure"""
    path = path or self.workspace_path
    result = {}
    try:
      path = Path(path)
      if path.is_file():
        return str(path)
      elif path.is_dir():
        for item in path.iterdir():
          if item.name.startswith('.'):
            continue
          if max_depth is not None and len(item.parts) > max_depth:
            continue
          if item.is_file():
            result[item.name] = str(item)
          elif item.is_dir():
            result[item.name] = self.get_directory_structure(item, max_depth)
    except Exception as e:
      logger.error(f'Error reading directory: {e}')
    return result

  def view_content(
      self, start_line: int = None, end_line: int = None
  ) -> List[str]:
    """View content of the current file with optional line range"""
    if not self.lines:
      return ['No file loaded']

    if start_line is None:
      start_line = self.current_position
    if end_line is None:
      end_line = min(start_line + 20, len(self.lines))

    content = []
    for i, line in enumerate(
        self.lines[start_line:end_line], start=start_line + 1
    ):
      content.append(f'{i:4d} | {line}')
    return content

  def scroll_up(self, lines: int = 10) -> List[str]:
    """Scroll up by specified number of lines"""
    self.current_position = max(0, self.current_position - lines)
    return self.view_content()

  def scroll_down(self, lines: int = 10) -> List[str]:
    """Scroll down by specified number of lines"""
    self.current_position = min(
        len(self.lines) - 1, self.current_position + lines
    )
    return self.view_content()

  def find_definition(self, symbol: str) -> Optional[JumpTarget]:
    """Find definition of a symbol, possibly in another file"""
    if not self.current_file:
      return None

    location = self.code_intelligence.find_definition(symbol, self.current_file)
    if location:
      return JumpTarget(
          file_path=location.file_path,
          line=location.line,
          column=location.column,
          symbol=symbol,
          kind='definition',
      )
    return None

  def find_references(self, symbol: str) -> List[JumpTarget]:
    """Find all references to a symbol across files"""
    if not self.current_file:
      return []

    references = []
    for location in self.code_intelligence.find_references(
        symbol, self.current_file
    ):
      references.append(
          JumpTarget(
              file_path=location.file_path,
              line=location.line,
              column=location.column,
              symbol=symbol,
              kind='reference',
          )
      )
    return references

  def jump_to_target(self, target: JumpTarget) -> List[str]:
    """Jump to a target location, possibly in another file"""
    if target.file_path != self.current_file:
      if not self.load_file(target.file_path):
        return [f'Failed to load file: {target.file_path}']

    self.current_position = target.line - 1
    content = self.view_content(
        self.current_position, self.current_position + 10
    )

    # Add context about the jump
    header = (
        f"Jumped to {target.kind} of '{target.symbol}' in {target.file_path}"
    )
    return [header, '-' * len(header)] + content

  def get_symbol_info(self, symbol: str, line: int = None) -> Dict:
    """Get comprehensive information about a symbol"""
    if not self.current_file:
      return {}

    info = {
        'symbol': symbol,
        'type': None,
        'documentation': None,
        'definition': None,
        'references': [],
    }

    # Get type information
    type_info = self.type_analyzer.get_type_info(self.current_file, symbol)
    if type_info:
      info['type'] = {
          'type_hint': type_info.type_hint,
          'inferred_type': type_info.inferred_type,
          'possible_types': (
              list(type_info.possible_types)
              if type_info.possible_types
              else None
          ),
      }

    # Get documentation
    doc = self.doc_extractor.get_documentation(self.current_file, symbol)
    if doc:
      info['documentation'] = {
          'summary': doc.summary,
          'description': doc.description,
          'params': doc.params,
          'returns': doc.returns,
          'raises': doc.raises,
          'examples': doc.examples,
      }

    # Get definition
    definition = self.find_definition(symbol)
    if definition:
      info['definition'] = {
          'file': definition.file_path,
          'line': definition.line,
          'column': definition.column,
      }

    # Get references
    references = self.find_references(symbol)
    if references:
      info['references'] = [
          {'file': ref.file_path, 'line': ref.line, 'column': ref.column}
          for ref in references
      ]

    return info
