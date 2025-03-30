#!/usr/bin/env python3
"""Getting started example for Hanzo ACI.

This is a simple example demonstrating how to use Hanzo ACI.
"""

import asyncio
from hanzo_aci import computer


async def main():
    """Run the example."""
    # Check capabilities
    capabilities = await computer.get_capabilities()
    print(f"Computer capabilities: {capabilities}")
    
    # List files in the current directory
    files = await computer.list_files(".")
    print(f"Files in current directory: {files}")
    
    # Run a simple command
    result = await computer.run_command("echo 'Hello from Hanzo ACI!'")
    print(f"Command result: {result}")
    
    # Try to take a screenshot if available
    if "take_screenshot" in str(capabilities):
        screenshot = await computer.take_screenshot()
        print(f"Screenshot result: {screenshot}")


if __name__ == "__main__":
    asyncio.run(main())
