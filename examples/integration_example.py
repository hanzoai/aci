#!/usr/bin/env python3
"""Integration example for Hanzo ACI.

This example demonstrates how to use Hanzo ACI with different backends
and how to integrate it with AI assistants.
"""

import os
import sys
import json
import asyncio
import argparse
import tempfile
from typing import Dict, Any, List, Optional, Union

from hanzo_aci import computer
from hanzo_aci.concrete import ConcreteComputerInterface


class AIAssistantExample:
    """Example AI assistant that uses the computer interface."""
    
    def __init__(self, backend: Optional[str] = None):
        """Initialize the AI assistant.
        
        Args:
            backend: Optional backend to use (native, mcp, or claude_code)
        """
        if backend:
            self.computer = ConcreteComputerInterface(backend=backend)
        else:
            self.computer = computer
        
        # Directory to store the assistant's files
        self.temp_dir = tempfile.mkdtemp(prefix="hanzo_aci_assistant_")
        print(f"Created temporary directory: {self.temp_dir}")
    
    async def startup(self):
        """Initialize the assistant."""
        # Ensure the computer interface is running
        await self.computer.ensure_running()
        
        # Get capabilities
        self.capabilities = await self.computer.get_capabilities()
        print(f"Using backend: {self.capabilities.get('backend', 'unknown')}")
        
        # Create a workspace file
        workspace_file = os.path.join(self.temp_dir, "workspace.json")
        workspace_data = {
            "name": "Hanzo ACI Assistant",
            "created_at": "2025-03-30T12:00:00Z",
            "backend": self.capabilities.get("backend", "unknown"),
            "capabilities": self.capabilities
        }
        
        await self.computer.write_file(
            workspace_file, 
            json.dumps(workspace_data, indent=2)
        )
        print(f"Created workspace file: {workspace_file}")
    
    async def shutdown(self):
        """Clean up the assistant."""
        print(f"Cleaning up temporary directory: {self.temp_dir}")
        # In a real application, you might want to keep the temp directory
        # but for this example we'll remove it
        import shutil
        shutil.rmtree(self.temp_dir)
    
    async def process_request(self, request: str) -> str:
        """Process a request from the user.
        
        Args:
            request: User request string
            
        Returns:
            Response to the user
        """
        # In a real assistant, this would involve NLP and other AI capabilities
        # but for this example we'll just handle a few simple commands
        
        request = request.strip().lower()
        
        if "list files" in request:
            dir_path = os.getcwd()
            # Extract directory path if provided
            if "in" in request:
                dir_path = request.split("in", 1)[1].strip()
            
            result = await self.computer.list_files(dir_path)
            if result.get("success", False):
                files = result.get("files", [])
                dirs = result.get("directories", [])
                return f"Files in {dir_path}:\n- Files: {', '.join(files)}\n- Directories: {', '.join(dirs)}"
            else:
                return f"Error listing files: {result.get('error')}"
        
        elif "run command" in request:
            cmd = request.replace("run command", "", 1).strip()
            result = await self.computer.run_command(cmd)
            if result.get("success", False):
                return f"Command output:\n{result.get('stdout', '')}"
            else:
                return f"Error running command: {result.get('error')}"
        
        elif "take screenshot" in request:
            result = await self.computer.take_screenshot()
            if result.get("success", False):
                screenshot_path = result.get("screenshot_path")
                # In a real assistant, you might want to display the screenshot
                # or upload it somewhere, but for this example we'll just return the path
                return f"Screenshot taken and saved to: {screenshot_path}"
            else:
                return f"Error taking screenshot: {result.get('error')}"
        
        elif "open application" in request:
            app_name = request.replace("open application", "", 1).strip()
            result = await self.computer.open_application(app_name)
            if result.get("success", False):
                return f"Opened application: {app_name}"
            else:
                return f"Error opening application: {result.get('error')}"
        
        elif "create file" in request:
            # Parse the request for filename and content
            parts = request.split("with content", 1)
            filename = parts[0].replace("create file", "", 1).strip()
            content = parts[1].strip() if len(parts) > 1 else ""
            
            # Create the file
            file_path = os.path.join(self.temp_dir, filename)
            result = await self.computer.write_file(file_path, content)
            if result.get("success", False):
                return f"Created file: {file_path}"
            else:
                return f"Error creating file: {result.get('error')}"
        
        elif "read file" in request:
            filename = request.replace("read file", "", 1).strip()
            file_path = os.path.join(self.temp_dir, filename)
            
            # Try to read from temp dir first, then current dir
            result = await self.computer.read_file(file_path)
            if not result.get("success", False):
                # Try current directory
                file_path = os.path.join(os.getcwd(), filename)
                result = await self.computer.read_file(file_path)
            
            if result.get("success", False):
                return f"Content of {file_path}:\n{result.get('content')}"
            else:
                return f"Error reading file: {result.get('error')}"
        
        elif "get clipboard" in request:
            result = await self.computer.clipboard_get()
            if result.get("success", False):
                return f"Clipboard content:\n{result.get('content')}"
            else:
                return f"Error getting clipboard: {result.get('error')}"
        
        elif "set clipboard" in request:
            content = request.replace("set clipboard", "", 1).strip()
            result = await self.computer.clipboard_set(content)
            if result.get("success", False):
                return f"Clipboard content set to: {content}"
            else:
                return f"Error setting clipboard: {result.get('error')}"
        
        elif "capabilities" in request:
            return f"Computer capabilities:\n{json.dumps(self.capabilities, indent=2)}"
        
        elif "help" in request:
            return """
Available commands:
- list files [in <directory>]
- run command <command>
- take screenshot
- open application <app_name>
- create file <filename> with content <content>
- read file <filename>
- get clipboard
- set clipboard <content>
- capabilities
- help
- exit
"""
        
        elif "exit" in request:
            return "Exiting assistant..."
        
        else:
            return "I don't understand that command. Type 'help' for a list of available commands."


async def run_interactive_assistant(backend: Optional[str] = None):
    """Run an interactive session with the AI assistant.
    
    Args:
        backend: Optional backend to use (native, mcp, or claude_code)
    """
    assistant = AIAssistantExample(backend=backend)
    await assistant.startup()
    
    print("\n=== Hanzo ACI Interactive Assistant ===")
    print("Type 'help' for a list of available commands. Type 'exit' to quit.")
    
    while True:
        try:
            # Get input from the user
            request = input("\nUser: ")
            
            # Exit if requested
            if request.strip().lower() == "exit":
                break
            
            # Process the request
            response = await assistant.process_request(request)
            print(f"\nAssistant: {response}")
            
            # Exit if the assistant indicates it's exiting
            if "Exiting assistant..." in response:
                break
        
        except KeyboardInterrupt:
            print("\nInterrupted by user. Exiting...")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
    
    # Clean up
    await assistant.shutdown()
    print("\nAssistant session ended.")


async def run_automated_demo(backend: Optional[str] = None):
    """Run an automated demo of the AI assistant.
    
    Args:
        backend: Optional backend to use (native, mcp, or claude_code)
    """
    print("\n=== Hanzo ACI Automated Demo ===")
    
    assistant = AIAssistantExample(backend=backend)
    await assistant.startup()
    
    # List of demo commands to run
    commands = [
        "capabilities",
        "list files",
        "run command echo 'Hello from Hanzo ACI!'",
        "create file test.txt with content This is a test file created by Hanzo ACI",
        "read file test.txt",
        "take screenshot",
        "get clipboard",
        "set clipboard This text was set by Hanzo ACI",
        "get clipboard"
    ]
    
    for command in commands:
        print(f"\nUser: {command}")
        response = await assistant.process_request(command)
        print(f"Assistant: {response}")
        # Pause between commands for readability
        await asyncio.sleep(1)
    
    # Clean up
    await assistant.shutdown()
    print("\nAutomated demo completed.")


def main():
    """Main entry point for the integration example."""
    parser = argparse.ArgumentParser(description="Hanzo ACI Integration Example")
    
    parser.add_argument(
        "--backend",
        choices=["native", "mcp", "claude_code"],
        help="Backend to use (default: auto-detect)"
    )
    
    parser.add_argument(
        "--mode",
        choices=["interactive", "demo"],
        default="interactive",
        help="Run mode (default: interactive)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.mode == "interactive":
            asyncio.run(run_interactive_assistant(args.backend))
        else:
            asyncio.run(run_automated_demo(args.backend))
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
