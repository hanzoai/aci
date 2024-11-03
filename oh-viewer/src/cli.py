#!/usr/bin/env python3

import json
import os
import sys
import click
from src.core import FileViewer


@click.group()
def cli():
  """Oh-Viewer: A command line file viewer with code intelligence."""
  pass


@cli.command()
@click.argument('path')
def explore(path):
  """Explore a directory structure."""
  viewer = FileViewer(workspace_path=os.path.dirname(os.path.abspath(path)))
  structure = viewer.get_directory_structure(path)
  print(json.dumps(structure, indent=2))


@cli.command()
@click.argument('filepath')
@click.option('--start-line', '-s', type=int, help='Start line number')
@click.option('--end-line', '-e', type=int, help='End line number')
def view(filepath, start_line, end_line):
  """View content of a file."""
  viewer = FileViewer(workspace_path=os.path.dirname(os.path.abspath(filepath)))
  if viewer.load_file(filepath):
    content = viewer.view_content(
        start_line - 1 if start_line else None, end_line if end_line else None
    )
    print('\n'.join(content))


@cli.command()
@click.argument('filepath')
@click.argument('symbol')
def find_def(filepath, symbol):
  """Find definition of a symbol, with support for cross-file definitions."""
  viewer = FileViewer(workspace_path=os.path.dirname(os.path.abspath(filepath)))
  if viewer.load_file(filepath):
    target = viewer.find_definition(symbol)
    if target:
      content = viewer.jump_to_target(target)
      print('\n'.join(content))
    else:
      print(f"No definition found for '{symbol}'")


@cli.command()
@click.argument('filepath')
@click.argument('symbol')
def find_refs(filepath, symbol):
  """Find all references to a symbol across files."""
  viewer = FileViewer(workspace_path=os.path.dirname(os.path.abspath(filepath)))
  if viewer.load_file(filepath):
    references = viewer.find_references(symbol)
    if references:
      print(f"Found {len(references)} references to '{symbol}':")
      for ref in references:
        content = viewer.jump_to_target(ref)
        print('\n' + '-' * 40 + '\n')
        print('\n'.join(content))
    else:
      print(f"No references found for '{symbol}'")


@cli.command()
@click.argument('filepath')
@click.argument('symbol')
def symbol_info(filepath, symbol):
  """Get comprehensive information about a symbol."""
  viewer = FileViewer(workspace_path=os.path.dirname(os.path.abspath(filepath)))
  if viewer.load_file(filepath):
    info = viewer.get_symbol_info(symbol)
    if info:
      print(json.dumps(info, indent=2))
    else:
      print(f"No information found for '{symbol}'")


if __name__ == '__main__':
  cli()
