#!/usr/bin/env python3
"""Basic example demonstrating the use of Hanzo ACI.

This example shows how to use the Hanzo ACI to interact with the computer
through different backends.
"""

import os
import sys
import asyncio
import argparse
from typing import Optional

from hanzo_aci import computer
from hanzo_aci.concrete import ConcreteComputerInterface


async def run_example(backend: Optional[str] = None):
    """Run the example with the specified backend.
    
    Args:
        backend: Backend to use (native, mcp, or claude_code)
    """
    # Create a computer interface with the specified backend
    if backend:
        interface = ConcreteComputerInterface(backend=backend)
    else:
        interface = computer
    
    # Ensure the backend is running
    await interface.ensure_running()
    
    # Get capabilities
    capabilities = await interface.get_capabilities()
    print(f"Using backend: {capabilities.get('backend', 'unknown')}")
    print(f"Available capabilities: {capabilities}")
    
    # List files in the current directory
    current_dir = os.getcwd()
    print(f"\nListing files in {current_dir}:")
    result = await interface.list_files(current_dir)
    if result.get("success", False):
        print(f"Files: {result.get('files', [])}")
        print(f"Directories: {result.get('directories', [])}")
    else:
        print(f"Error: {result.get('error')}")
    
    # Run a simple command
    print("\nRunning 'ls -la' command:")
    result = await interface.run_command("ls -la", current_dir)
    if result.get("success", False):
        print(f"Command output:\n{result.get('stdout', '')}")
    else:
        print(f"Error: {result.get('error')}")
    
    # Create a temporary file
    temp_file = os.path.join(current_dir, "hanzo_aci_example.txt")
    print(f"\nWriting to temporary file: {temp_file}")
    result = await interface.write_file(temp_file, "Hello from Hanzo ACI!")
    if result.get("success", False):
        print("File written successfully")
    else:
        print(f"Error: {result.get('error')}")
    
    # Read the file back
    print(f"\nReading from temporary file: {temp_file}")
    result = await interface.read_file(temp_file)
    if result.get("success", False):
        print(f"File content: {result.get('content')}")
    else:
        print(f"Error: {result.get('error')}")
    
    # Clean up the temporary file
    print(f"\nCleaning up temporary file: {temp_file}")
    os.unlink(temp_file)
    
    # Get clipboard contents (if available)
    print("\nGetting clipboard contents:")
    result = await interface.clipboard_get()
    if result.get("success", False):
        print(f"Clipboard content: {result.get('content')}")
    else:
        print(f"Error: {result.get('error')}")
    
    # Take a screenshot (if available)
    print("\nTaking a screenshot:")
    result = await interface.take_screenshot()
    if result.get("success", False):
        print(f"Screenshot saved to: {result.get('screenshot_path')}")
    else:
        print(f"Error: {result.get('error')}")
    
    print("\nExample completed successfully")


def main():
    """Main entry point for the example."""
    parser = argparse.ArgumentParser(description="Hanzo ACI example")
    
    parser.add_argument(
        "--backend",
        choices=["native", "mcp", "claude_code"],
        help="Backend to use (default: auto-detect)"
    )
    
    args = parser.parse_args()
    
    try:
        asyncio.run(run_example(args.backend))
        return 0
    except KeyboardInterrupt:
        print("\nExample interrupted")
        return 130
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
