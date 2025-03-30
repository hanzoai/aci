"""Command-line interface for Hanzo ACI.

This module provides a CLI for interacting with the computer through
the Abstract Computer Interface.
"""

import os
import sys
import json
import argparse
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union

from hanzo_aci import computer
from hanzo_aci.version import __version__

logger = logging.getLogger(__name__)


async def execute_operation(args) -> None:
    """Execute an operation based on command-line arguments.
    
    Args:
        args: Command-line arguments
    """
    # Check if we need to use a specific backend
    if args.backend:
        from hanzo_aci.concrete import ConcreteComputerInterface
        global computer
        computer = ConcreteComputerInterface(backend=args.backend)
    
    # Make sure the backend is running
    await computer.ensure_running()
    
    # Process the operation
    if args.operation == "capabilities":
        capabilities = await computer.get_capabilities()
        print(json.dumps(capabilities, indent=2))
    elif args.operation == "run_command":
        result = await computer.run_command(args.command, args.cwd)
        print(json.dumps(result, indent=2))
    elif args.operation == "read_file":
        result = await computer.read_file(args.path)
        print(json.dumps(result, indent=2))
    elif args.operation == "write_file":
        content = args.content
        if args.content_file:
            with open(args.content_file, "r") as f:
                content = f.read()
        result = await computer.write_file(args.path, content)
        print(json.dumps(result, indent=2))
    elif args.operation == "list_files":
        result = await computer.list_files(args.path)
        print(json.dumps(result, indent=2))
    elif args.operation == "take_screenshot":
        result = await computer.take_screenshot()
        print(json.dumps(result, indent=2))
    elif args.operation == "open_application":
        result = await computer.open_application(args.app_name)
        print(json.dumps(result, indent=2))
    elif args.operation == "file_explorer":
        result = await computer.file_explorer(args.path)
        print(json.dumps(result, indent=2))
    elif args.operation == "clipboard_get":
        result = await computer.clipboard_get()
        print(json.dumps(result, indent=2))
    elif args.operation == "clipboard_set":
        content = args.content
        if args.content_file:
            with open(args.content_file, "r") as f:
                content = f.read()
        result = await computer.clipboard_set(content)
        print(json.dumps(result, indent=2))
    elif args.operation == "stdio":
        await stdio_mode()
    else:
        print(f"Unknown operation: {args.operation}")


async def stdio_mode() -> None:
    """Run in stdio mode, processing commands from stdin."""
    print("Running in stdio mode. Send commands as JSON objects, one per line.")
    print("Format: {\"operation\": \"<operation>\", \"params\": {...}}")
    print("Type Ctrl+C to exit.")
    
    while True:
        try:
            # Read a line from stdin
            line = sys.stdin.readline().strip()
            
            if not line:
                continue
            
            # Parse the command
            try:
                command = json.loads(line)
            except json.JSONDecodeError as e:
                result = {"success": False, "error": f"Invalid JSON: {str(e)}"}
                print(json.dumps(result))
                continue
            
            # Validate the command
            if "operation" not in command:
                result = {"success": False, "error": "Missing 'operation' field"}
                print(json.dumps(result))
                continue
            
            # Extract the operation and parameters
            operation = command.get("operation")
            params = command.get("params", {})
            
            # Execute the operation
            result = await computer.execute_operation(operation, params)
            
            # Send the result back to stdout
            print(json.dumps(result))
            sys.stdout.flush()
        
        except KeyboardInterrupt:
            break
        except Exception as e:
            result = {"success": False, "error": f"Error: {str(e)}"}
            print(json.dumps(result))
            sys.stdout.flush()


def main() -> int:
    """Main entry point for the CLI.
    
    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(
        description="Hanzo Abstract Computer Interface CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get computer capabilities
  hanzo-aci capabilities
  
  # Run a command
  hanzo-aci run_command --command "ls -la" --cwd /path/to/dir
  
  # Read a file
  hanzo-aci read_file --path /path/to/file.txt
  
  # Write to a file
  hanzo-aci write_file --path /path/to/file.txt --content "Hello, world!"
  
  # Take a screenshot
  hanzo-aci take_screenshot
  
  # Run in stdio mode (for integration with AI tools)
  hanzo-aci stdio
        """
    )
    
    # Global options
    parser.add_argument(
        "--backend",
        choices=["native", "mcp", "claude_code"],
        help="Backend to use (default: auto-detect)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"hanzo-aci {__version__}"
    )
    
    # Create subparsers for operations
    subparsers = parser.add_subparsers(
        dest="operation",
        help="Operation to perform"
    )
    
    # Capabilities
    capabilities_parser = subparsers.add_parser(
        "capabilities",
        help="Get computer capabilities"
    )
    
    # Run command
    run_command_parser = subparsers.add_parser(
        "run_command",
        help="Run a shell command"
    )
    run_command_parser.add_argument(
        "--command",
        required=True,
        help="Command to run"
    )
    run_command_parser.add_argument(
        "--cwd",
        help="Working directory"
    )
    
    # Read file
    read_file_parser = subparsers.add_parser(
        "read_file",
        help="Read a file"
    )
    read_file_parser.add_argument(
        "--path",
        required=True,
        help="Path to the file"
    )
    
    # Write file
    write_file_parser = subparsers.add_parser(
        "write_file",
        help="Write to a file"
    )
    write_file_parser.add_argument(
        "--path",
        required=True,
        help="Path to the file"
    )
    write_file_group = write_file_parser.add_mutually_exclusive_group(required=True)
    write_file_group.add_argument(
        "--content",
        help="Content to write"
    )
    write_file_group.add_argument(
        "--content-file",
        help="File containing content to write"
    )
    
    # List files
    list_files_parser = subparsers.add_parser(
        "list_files",
        help="List files in a directory"
    )
    list_files_parser.add_argument(
        "--path",
        default=".",
        help="Directory path (default: current directory)"
    )
    
    # Take screenshot
    take_screenshot_parser = subparsers.add_parser(
        "take_screenshot",
        help="Take a screenshot"
    )
    
    # Open application
    open_application_parser = subparsers.add_parser(
        "open_application",
        help="Open an application"
    )
    open_application_parser.add_argument(
        "--app-name",
        required=True,
        help="Name of the application to open"
    )
    
    # File explorer
    file_explorer_parser = subparsers.add_parser(
        "file_explorer",
        help="Open the file explorer at a specific path"
    )
    file_explorer_parser.add_argument(
        "--path",
        default=".",
        help="Path to open (default: current directory)"
    )
    
    # Clipboard get
    clipboard_get_parser = subparsers.add_parser(
        "clipboard_get",
        help="Get clipboard contents"
    )
    
    # Clipboard set
    clipboard_set_parser = subparsers.add_parser(
        "clipboard_set",
        help="Set clipboard contents"
    )
    clipboard_set_group = clipboard_set_parser.add_mutually_exclusive_group(required=True)
    clipboard_set_group.add_argument(
        "--content",
        help="Content to set"
    )
    clipboard_set_group.add_argument(
        "--content-file",
        help="File containing content to set"
    )
    
    # Stdio mode
    stdio_parser = subparsers.add_parser(
        "stdio",
        help="Run in stdio mode for integration with AI tools"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # If no operation is specified, show help
    if not args.operation:
        parser.print_help()
        return 0
    
    # Run the operation
    try:
        asyncio.run(execute_operation(args))
        return 0
    except KeyboardInterrupt:
        print("\nOperation interrupted")
        return 130
    except Exception as e:
        print(f"Error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
