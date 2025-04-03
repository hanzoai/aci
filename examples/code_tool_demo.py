#!/usr/bin/env python3
"""Demo application for the Hanzo Code Tool.

This demo showcases the capabilities of the Hanzo Code Tool integration with ACI.
It provides a CLI and stdio interface for editing and interacting with code.
"""

import argparse
import asyncio
import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

from hanzo_aci.tools.code_cli import CodeCLI


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Hanzo Code Tool Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run in stdio mode (default)
  python code_tool_demo.py

  # List a directory tree
  python code_tool_demo.py directory_tree --path /path/to/project

  # Read a file
  python code_tool_demo.py read --paths /path/to/file.py

  # Run a command
  python code_tool_demo.py run_command --command "ls -la" --cwd /path/to/dir

  # Analyze a project
  python code_tool_demo.py analyze_project --project_dir /path/to/project
        """
    )
    
    # Global options
    parser.add_argument(
        "--allow-path",
        action="append",
        dest="allowed_paths",
        help="Add an allowed path (can be specified multiple times)",
    )
    
    parser.add_argument(
        "--project-dir",
        dest="project_dir",
        help="Set the project directory",
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Enable verbose output",
    )
    
    # Create subparsers for operations
    subparsers = parser.add_subparsers(dest="operation", help="Operation to perform")
    
    # File operations
    read_parser = subparsers.add_parser("read", help="Read file(s)")
    read_parser.add_argument("--paths", nargs="+", required=True, help="File path(s) to read")
    
    write_parser = subparsers.add_parser("write", help="Write to a file")
    write_parser.add_argument("--path", required=True, help="File path to write to")
    write_parser.add_argument("--content", required=True, help="Content to write")
    
    edit_parser = subparsers.add_parser("edit", help="Edit a file")
    edit_parser.add_argument("--path", required=True, help="File path to edit")
    edit_parser.add_argument("--edits", required=True, help="JSON string of edits (list of oldText/newText pairs)")
    edit_parser.add_argument("--dry-run", action="store_true", help="Perform a dry run")
    
    tree_parser = subparsers.add_parser("directory_tree", help="Get directory tree")
    tree_parser.add_argument("--path", required=True, help="Directory path to get tree for")
    tree_parser.add_argument("--depth", type=int, default=3, help="Maximum depth")
    tree_parser.add_argument("--include-filtered", action="store_true", help="Include filtered directories")
    
    info_parser = subparsers.add_parser("get_file_info", help="Get file information")
    info_parser.add_argument("--path", required=True, help="File path to get info for")
    
    search_parser = subparsers.add_parser("search_content", help="Search for content in files")
    search_parser.add_argument("--pattern", required=True, help="Pattern to search for")
    search_parser.add_argument("--path", required=True, help="Path to search in")
    search_parser.add_argument("--file-pattern", default="*", help="File pattern to match")
    
    find_replace_parser = subparsers.add_parser("find_replace", help="Find and replace content in files")
    find_replace_parser.add_argument("--pattern", required=True, help="Sed pattern to use (e.g., s/foo/bar/g)")
    find_replace_parser.add_argument("--path", required=True, help="Directory to perform replacement in")
    find_replace_parser.add_argument("--dry-run", action="store_true", help="Perform a dry run")
    
    # Command operations
    run_cmd_parser = subparsers.add_parser("run_command", help="Run a shell command")
    run_cmd_parser.add_argument("--command", required=True, help="Command to run")
    run_cmd_parser.add_argument("--cwd", required=True, help="Working directory")
    run_cmd_parser.add_argument("--use-login-shell", action="store_true", default=True, help="Use login shell")
    
    run_script_parser = subparsers.add_parser("run_script", help="Run a script")
    run_script_parser.add_argument("--script", required=True, help="Script content")
    run_script_parser.add_argument("--cwd", required=True, help="Working directory")
    run_script_parser.add_argument("--interpreter", default="bash", help="Script interpreter")
    run_script_parser.add_argument("--use-login-shell", action="store_true", default=True, help="Use login shell")
    
    # Project operations
    analyze_parser = subparsers.add_parser("analyze_project", help="Analyze a project")
    analyze_parser.add_argument("--project_dir", required=True, help="Project directory")
    
    # Default to stdio mode if no operation is specified
    parser.set_defaults(operation=None)
    
    return parser.parse_args()


async def main_async() -> int:
    """Main async entry point.
    
    Returns:
        Exit code
    """
    args = parse_args()
    
    print("Initializing Hanzo Code Tool Demo...")
    
    # Initialize CLI
    cli = CodeCLI(
        allowed_paths=args.allowed_paths,
        project_dir=args.project_dir,
        verbose=args.verbose
    )
    
    print("Hanzo Code Tool Demo initialized.")
    
    # Run in stdio mode if no operation is specified
    if args.operation is None:
        print("Starting stdio mode. Send commands as JSON objects, one per line.")
        print("Format: {\"operation\": \"<operation>\", \"args\": {...}}")
        print("Press Ctrl+C to exit.")
        await cli.stdio_mode()
        return 0
    
    print(f"Executing operation: {args.operation}")
    
    # Convert args to dict for operation
    args_dict = vars(args)
    
    # Remove global options
    for opt in ["allowed_paths", "project_dir", "verbose", "operation"]:
        if opt in args_dict:
            del args_dict[opt]
    
    # Special handling for edits in edit operation
    if args.operation == "edit" and "edits" in args_dict:
        try:
            args_dict["edits"] = json.loads(args_dict["edits"])
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in --edits parameter")
            return 1
    
    # Run CLI command
    return await cli.run_cli_command(args.operation, args_dict)


def main() -> int:
    """Main entry point.
    
    Returns:
        Exit code
    """
    print("Starting Hanzo Code Tool Demo...")
    
    loop = asyncio.get_event_loop()
    try:
        return loop.run_until_complete(main_async())
    except KeyboardInterrupt:
        print("Operation interrupted by user")
        return 130
    finally:
        loop.close()


if __name__ == "__main__":
    sys.exit(main())
