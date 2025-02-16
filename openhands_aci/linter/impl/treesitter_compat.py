"""Compatibility layer for tree-sitter-languages with tree-sitter 0.24.0."""

import importlib.util
from tree_sitter import Language, Parser


def get_language_module(language):
    """Try to import the tree-sitter module for a given language."""
    module_name = f'tree_sitter_{language}'
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        raise ImportError(
            f'Language {language} is not supported because {module_name} is not installed. '
            f'You can install it with:\n\n    pip install {module_name}\n'
        )
    return importlib.util.module_from_spec(spec)


def get_language(language):
    """Get a Language object for the given language name."""
    try:
        module = get_language_module(language)
        spec = module.__spec__
        spec.loader.exec_module(module)
        return Language(module.language())
    except ImportError as e:
        raise ValueError(str(e)) from e


def get_parser(language):
    """Get a Parser object for the given language name."""
    language = get_language(language)
    parser = Parser(language)
    return parser