"""Language support module for Oh-Viewer"""

import os
from pathlib import Path
import subprocess
from typing import Dict, List, Optional
from tree_sitter import Language, Parser


class LanguageSupport:
  """Manages multiple programming language support using tree-sitter"""

  LANGUAGE_CONFIGS = {
      'python': {
          'extensions': ['.py'],
          'repo': 'tree-sitter-python',
          'scope_markers': ['def', 'class', 'with', 'if', 'for', 'while'],
      },
      'javascript': {
          'extensions': ['.js', '.jsx', '.ts', '.tsx'],
          'repo': 'tree-sitter-javascript',
          'scope_markers': ['function', 'class', 'if', 'for', 'while'],
      },
      'go': {
          'extensions': ['.go'],
          'repo': 'tree-sitter-go',
          'scope_markers': ['func', 'type', 'if', 'for'],
      },
      'rust': {
          'extensions': ['.rs'],
          'repo': 'tree-sitter-rust',
          'scope_markers': ['fn', 'struct', 'impl', 'if', 'for', 'while'],
      },
      'cpp': {
          'extensions': ['.cpp', '.hpp', '.h', '.cc'],
          'repo': 'tree-sitter-cpp',
          'scope_markers': [
              'class',
              'struct',
              'namespace',
              'if',
              'for',
              'while',
          ],
      },
      'java': {
          'extensions': ['.java'],
          'repo': 'tree-sitter-java',
          'scope_markers': ['class', 'interface', 'if', 'for', 'while'],
      },
  }

  def __init__(self):
    self.parsers: Dict[str, Parser] = {}
    self.languages: Dict[str, Language] = {}
    self._load_languages()

  def _check_tree_sitter_cli(self) -> bool:
    """Check if tree-sitter CLI is installed"""
    try:
      subprocess.run(
          ['tree-sitter', '--version'],
          check=True,
          stdout=subprocess.PIPE,
          stderr=subprocess.PIPE,
      )
      return True
    except (subprocess.CalledProcessError, FileNotFoundError):
      print('tree-sitter CLI not found. Please install it using:')
      print('npm install -g tree-sitter-cli')
      return False

  def _build_parser(self, lang_dir: Path) -> None:
    """Build a parser using the new tree-sitter API"""
    if not (lang_dir / 'src').exists():
      return

    if not self._check_tree_sitter_cli():
      return

    # Navigate to language directory and build
    cwd = os.getcwd()
    os.chdir(str(lang_dir))
    try:
      subprocess.run(['tree-sitter', 'generate'], check=True)
      subprocess.run(['tree-sitter', 'test'], check=True)
    except subprocess.CalledProcessError as e:
      print(f'Failed to build parser: {e}')
    finally:
      os.chdir(cwd)

  def _load_languages(self):
    """Load all supported languages using the new tree-sitter API"""
    parsers_path = Path('/workspace/tree-sitter-parsers')

    for lang, config in self.LANGUAGE_CONFIGS.items():
      repo_path = parsers_path / config['repo']
      if not repo_path.exists():
        continue

      try:
        # Build the parser if needed
        self._build_parser(repo_path)

        # Load the language using the new API
        parser = Parser()
        # Look for the compiled library
        lib_path = repo_path / 'build' / 'languages.so'

        if lib_path.exists():
          try:
            # Try the new API first
            lang_lib = Language.load(str(lib_path))
          except (AttributeError, TypeError):
            # Fall back to the old API if needed
            lang_lib = Language(str(lib_path), lang)

          parser.set_language(lang_lib)
          self.languages[lang] = lang_lib
          self.parsers[lang] = parser
        else:
          print(
              f'Language library not found for {lang}. Please ensure'
              ' tree-sitter-cli is installed and the language is built.'
          )
      except Exception as e:
        print(f'Failed to load {lang}: {e}')

  def get_language_by_extension(self, file_path: str) -> Optional[str]:
    """Determine language from file extension"""
    ext = os.path.splitext(file_path)[1].lower()
    for lang, config in self.LANGUAGE_CONFIGS.items():
      if ext in config['extensions']:
        return lang
    return None

  def get_parser(self, language: str) -> Optional[Parser]:
    """Get parser for a specific language"""
    return self.parsers.get(language)

  def get_scope_markers(self, language: str) -> List[str]:
    """Get scope markers for a language"""
    return self.LANGUAGE_CONFIGS.get(language, {}).get('scope_markers', [])
