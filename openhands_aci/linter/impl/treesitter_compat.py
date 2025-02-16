"""Compatibility layer for tree-sitter-languages with tree-sitter 0.24.0."""

import tree_sitter_python
import tree_sitter_ruby
from tree_sitter import Language, Parser


LANGUAGE_MODULES = {
    'python': tree_sitter_python,
    'ruby': tree_sitter_ruby,
}


def get_language(language):
    if language not in LANGUAGE_MODULES:
        raise ValueError(f'Language {language} not supported')
    return Language(LANGUAGE_MODULES[language].language())


def get_parser(language):
    language = get_language(language)
    parser = Parser(language)
    return parser