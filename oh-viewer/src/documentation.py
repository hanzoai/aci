"""Documentation extraction module for Oh-Viewer"""

import ast
from dataclasses import dataclass
import re
from typing import Dict, List, Optional


@dataclass
class DocString:
  """Represents a documentation string"""

  summary: str
  description: Optional[str] = None
  params: Dict[str, str] = None
  returns: Optional[str] = None
  raises: List[str] = None
  examples: List[str] = None

  def __post_init__(self):
    if self.params is None:
      self.params = {}
    if self.raises is None:
      self.raises = []
    if self.examples is None:
      self.examples = []


class DocumentationExtractor:
  """Extracts and parses documentation from code"""

  def __init__(self, language_support):
    self.language_support = language_support
    self.doc_cache: Dict[str, Dict[str, DocString]] = {}

  def extract_docs(self, file_path: str, content: str) -> Dict[str, DocString]:
    """Extract documentation from a file"""
    language = self.language_support.get_language_by_extension(file_path)
    if not language:
      return {}

    if file_path in self.doc_cache:
      return self.doc_cache[file_path]

    docs = {}

    if language == 'python':
      docs = self._extract_python_docs(content)
    elif language in ['javascript', 'typescript']:
      docs = self._extract_js_docs(content)
    elif language == 'java':
      docs = self._extract_javadoc(content)
    # Add more language doc extractors here

    self.doc_cache[file_path] = docs
    return docs

  def _extract_python_docs(self, content: str) -> Dict[str, DocString]:
    """Extract Python docstrings"""
    docs = {}

    try:
      tree = ast.parse(content)
      for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
          doc = ast.get_docstring(node)
          if doc:
            docs[node.name if hasattr(node, 'name') else '__module__'] = (
                self._parse_docstring(doc)
            )
    except Exception as e:
      print(f'Error extracting Python docs: {e}')

    return docs

  def _parse_docstring(self, docstring: str) -> DocString:
    """Parse a docstring into structured documentation"""
    lines = docstring.split('\n')
    summary = lines[0].strip()

    doc = DocString(summary=summary)
    current_section = 'description'
    current_param = None
    description_lines = []

    for line in lines[1:]:
      line = line.strip()

      if not line:
        continue

      # Check for section markers
      if line.startswith('Args:') or line.startswith('Parameters:'):
        current_section = 'params'
        continue
      elif line.startswith('Returns:'):
        current_section = 'returns'
        continue
      elif line.startswith('Raises:'):
        current_section = 'raises'
        continue
      elif line.startswith('Example:') or line.startswith('Examples:'):
        current_section = 'examples'
        continue

      # Process line based on section
      if current_section == 'description':
        description_lines.append(line)

      elif current_section == 'params':
        param_match = re.match(r'\s*(\w+)\s*:\s*(.+)', line)
        if param_match:
          current_param = param_match.group(1)
          doc.params[current_param] = param_match.group(2)
        elif current_param and line.startswith(' '):
          doc.params[current_param] += ' ' + line.strip()

      elif current_section == 'returns':
        if not doc.returns:
          doc.returns = line
        else:
          doc.returns += ' ' + line

      elif current_section == 'raises':
        exception_match = re.match(r'\s*(\w+)\s*:\s*(.+)', line)
        if exception_match:
          doc.raises.append(
              f'{exception_match.group(1)}: {exception_match.group(2)}'
          )
        else:
          doc.raises.append(line)

      elif current_section == 'examples':
        doc.examples.append(line)

    if description_lines:
      doc.description = '\n'.join(description_lines).strip()

    return doc

  def _extract_js_docs(self, content: str) -> Dict[str, DocString]:
    """Extract JSDoc comments"""
    docs = {}

    # Match JSDoc blocks
    jsdoc_pattern = r'/\*\*\s*(.*?)\s*\*/'
    matches = re.finditer(jsdoc_pattern, content, re.DOTALL)

    for match in matches:
      doc_block = match.group(1)

      # Clean up the doc block
      lines = [line.strip().lstrip('*') for line in doc_block.split('\n')]

      # Get the associated symbol name
      end_pos = match.end()
      next_line = content[end_pos : content.find('\n', end_pos)].strip()
      symbol_match = re.search(
          r'(function|class|const|let|var)\s+(\w+)', next_line
      )

      if symbol_match:
        symbol_name = symbol_match.group(2)
        docs[symbol_name] = self._parse_jsdoc(lines)

    return docs

  def _parse_jsdoc(self, lines: List[str]) -> DocString:
    """Parse JSDoc comment into structured documentation"""
    doc = DocString(summary='')
    current_section = 'summary'
    current_param = None

    for line in lines:
      line = line.strip()
      if not line:
        continue

      # Parse JSDoc tags
      if line.startswith('@param'):
        current_section = 'params'
        param_match = re.match(r'@param\s+{([^}]+)}\s+(\w+)\s*(.*)', line)
        if param_match:
          type_str, name, desc = param_match.groups()
          doc.params[name] = f'{type_str}: {desc}'
          current_param = name

      elif line.startswith('@returns'):
        current_section = 'returns'
        returns_match = re.match(r'@returns?\s+{([^}]+)}\s*(.*)', line)
        if returns_match:
          type_str, desc = returns_match.groups()
          doc.returns = f'{type_str}: {desc}'

      elif line.startswith('@throws'):
        current_section = 'raises'
        throws_match = re.match(r'@throws\s+{([^}]+)}\s*(.*)', line)
        if throws_match:
          type_str, desc = throws_match.groups()
          doc.raises.append(f'{type_str}: {desc}')

      elif line.startswith('@example'):
        current_section = 'examples'

      else:
        # Handle continuation of previous section
        if current_section == 'summary' and not doc.summary:
          doc.summary = line
        elif current_section == 'params' and current_param:
          doc.params[current_param] += ' ' + line
        elif current_section == 'returns' and doc.returns:
          doc.returns += ' ' + line
        elif current_section == 'examples':
          doc.examples.append(line)
        else:
          # Treat as description if no tag is active
          if doc.description:
            doc.description += '\n' + line
          else:
            doc.description = line

    return doc

  def _extract_javadoc(self, content: str) -> Dict[str, DocString]:
    """Extract Javadoc comments"""
    docs = {}

    # Match Javadoc blocks
    javadoc_pattern = r'/\*\*\s*(.*?)\s*\*/'
    matches = re.finditer(javadoc_pattern, content, re.DOTALL)

    for match in matches:
      doc_block = match.group(1)

      # Clean up the doc block
      lines = [line.strip().lstrip('*') for line in doc_block.split('\n')]

      # Get the associated symbol name
      end_pos = match.end()
      next_line = content[end_pos : content.find('\n', end_pos)].strip()
      symbol_match = re.search(
          r'(class|interface|enum|public|private|protected)\s+\w+\s+(\w+)',
          next_line,
      )

      if symbol_match:
        symbol_name = symbol_match.group(2)
        docs[symbol_name] = self._parse_javadoc(lines)

    return docs

  def _parse_javadoc(self, lines: List[str]) -> DocString:
    """Parse Javadoc comment into structured documentation"""
    doc = DocString(summary='')
    current_section = 'summary'
    current_param = None

    for line in lines:
      line = line.strip()
      if not line:
        continue

      # Parse Javadoc tags
      if line.startswith('@param'):
        current_section = 'params'
        param_match = re.match(r'@param\s+(\w+)\s*(.*)', line)
        if param_match:
          name, desc = param_match.groups()
          doc.params[name] = desc
          current_param = name

      elif line.startswith('@return'):
        current_section = 'returns'
        returns_match = re.match(r'@returns?\s*(.*)', line)
        if returns_match:
          doc.returns = returns_match.group(1)

      elif line.startswith('@throws'):
        current_section = 'raises'
        throws_match = re.match(r'@throws\s+(\w+)\s*(.*)', line)
        if throws_match:
          type_str, desc = throws_match.groups()
          doc.raises.append(f'{type_str}: {desc}')

      else:
        # Handle continuation of previous section
        if current_section == 'summary' and not doc.summary:
          doc.summary = line
        elif current_section == 'params' and current_param:
          doc.params[current_param] += ' ' + line
        elif current_section == 'returns' and doc.returns:
          doc.returns += ' ' + line
        else:
          # Treat as description if no tag is active
          if doc.description:
            doc.description += '\n' + line
          else:
            doc.description = line

    return doc

  def get_documentation(
      self, file_path: str, symbol: str
  ) -> Optional[DocString]:
    """Get documentation for a symbol"""
    docs = self.doc_cache.get(file_path, {})
    return docs.get(symbol)
