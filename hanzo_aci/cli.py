#!/usr/bin/env python3
"""
Hanzo Dev CLI - Unified development environment combining ACI and MCP capabilities.
"""

import argparse
import asyncio
import sys
from typing import Optional
from pathlib import Path

# Import MCP components
from hanzo_mcp.cli import main as mcp_main
from hanzo_mcp.server import HanzoServer
from hanzo_mcp.config import Settings

# Import ACI components
from hanzo_aci import file_editor, FileCache
from hanzo_aci.utils.logger import setup_logger

# Version information
__version__ = "0.3.1"


def setup_parser():
    """Set up command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Hanzo Dev - Unified AI development environment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start the development server
  hanzo-dev serve
  
  # Run in standalone mode with specific paths
  hanzo-dev --allow-path /path/to/project
  
  # Use ACI editor directly
  hanzo-dev edit file.py
  
  # Run with all tools enabled
  hanzo-dev --enable-all-tools
        """
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"hanzo-dev {__version__}"
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Serve command (default MCP server mode)
    serve_parser = subparsers.add_parser("serve", help="Start the MCP server")
    serve_parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport mode"
    )
    
    # Edit command (ACI editor)
    edit_parser = subparsers.add_parser("edit", help="Edit a file using ACI")
    edit_parser.add_argument("file", help="File to edit")
    edit_parser.add_argument("--line", type=int, help="Line number to jump to")
    
    # Index command (ACI indexing)
    index_parser = subparsers.add_parser("index", help="Index a codebase")
    index_parser.add_argument("path", help="Path to index")
    index_parser.add_argument("--output", help="Output index file")
    
    # Common MCP arguments
    parser.add_argument(
        "--allow-path",
        action="append",
        dest="allowed_paths",
        help="Paths to allow access to (can be specified multiple times)"
    )
    
    parser.add_argument(
        "--enable-all-tools",
        action="store_true",
        help="Enable all available tools"
    )
    
    parser.add_argument(
        "--enable-agent-tool",
        action="store_true",
        help="Enable the agent delegation tool"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level"
    )
    
    return parser


async def run_editor(args):
    """Run the ACI editor."""
    logger = setup_logger("hanzo-dev", args.log_level)
    
    # Initialize file cache
    cache = FileCache()
    
    # Create editor instance
    editor = file_editor
    
    # Open the file
    try:
        result = editor.open_file(args.file, line_number=args.line)
        print(result)
    except Exception as e:
        logger.error(f"Error opening file: {e}")
        return 1
    
    return 0


async def run_indexer(args):
    """Run the ACI code indexer."""
    logger = setup_logger("hanzo-dev", args.log_level)
    
    try:
        from hanzo_aci.indexing.locagent.tools import index_codebase
        
        output_path = args.output or f"{Path(args.path).name}_index.json"
        
        logger.info(f"Indexing {args.path}...")
        index_data = await index_codebase(args.path)
        
        # Save index
        import json
        with open(output_path, 'w') as f:
            json.dump(index_data, f, indent=2)
        
        logger.info(f"Index saved to {output_path}")
        return 0
        
    except Exception as e:
        logger.error(f"Error indexing codebase: {e}")
        return 1


async def run_server(args):
    """Run the unified MCP server with ACI tools."""
    # For server mode, delegate to the MCP CLI with our enhancements
    # This ensures all MCP functionality is available
    
    # Convert args to list for MCP CLI
    mcp_args = []
    
    if hasattr(args, 'allowed_paths') and args.allowed_paths:
        for path in args.allowed_paths:
            mcp_args.extend(['--allow-path', path])
    
    if hasattr(args, 'enable_all_tools') and args.enable_all_tools:
        mcp_args.append('--enable-all-tools')
    
    if hasattr(args, 'enable_agent_tool') and args.enable_agent_tool:
        mcp_args.append('--enable-agent-tool')
    
    if hasattr(args, 'log_level'):
        mcp_args.extend(['--log-level', args.log_level])
    
    # Override sys.argv for MCP CLI
    original_argv = sys.argv
    try:
        sys.argv = ['hanzo-dev'] + mcp_args
        # Run MCP main
        mcp_main()
    finally:
        sys.argv = original_argv
    
    return 0


def main():
    """Main entry point for hanzo-dev CLI."""
    parser = setup_parser()
    args = parser.parse_args()
    
    # Default to serve command if no command specified
    if not args.command:
        args.command = "serve"
    
    # Run appropriate command
    if args.command == "serve":
        return asyncio.run(run_server(args))
    elif args.command == "edit":
        return asyncio.run(run_editor(args))
    elif args.command == "index":
        return asyncio.run(run_indexer(args))
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())