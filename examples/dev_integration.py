#!/usr/bin/env python3
"""Example demonstrating the integration between Hanzo ACI and Hanzo Dev.

This example shows how Hanzo ACI can utilize the capabilities of Hanzo Dev
for advanced computer interaction, symbolic reasoning, vector search, and
other dev tools.
"""

import os
import sys
import json
import asyncio
import argparse
import tempfile
from typing import Dict, Any, List, Optional, Union

from hanzo_aci import ComputerInterface
from hanzo_aci.concrete import ConcreteComputerInterface


class DevAssistantExample:
    """Example Assistant that uses the ACI-Dev integration."""
    
    def __init__(self, backend: str = "dev"):
        """Initialize the Dev assistant.
        
        Args:
            backend: Backend to use (dev by default)
        """
        self.computer = ConcreteComputerInterface(backend=backend)
        
        # Directory to store assistant files
        self.temp_dir = tempfile.mkdtemp(prefix="hanzo_aci_dev_assistant_")
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
            "name": "Hanzo ACI-Dev Assistant",
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
        import shutil
        shutil.rmtree(self.temp_dir)
    
    async def process_request(self, request: str) -> str:
        """Process a request from the user.
        
        Args:
            request: User request string
            
        Returns:
            Response to the user
        """
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
        
        elif "analyze project" in request:
            project_dir = os.getcwd()
            # Extract project path if provided
            if "in" in request:
                project_dir = request.split("in", 1)[1].strip()
            
            result = await self.computer.analyze_project(project_dir)
            if result.get("success", False):
                project_info = result.get("project", {})
                return f"Project analysis for {project_dir}:\n{json.dumps(project_info, indent=2)}"
            else:
                return f"Error analyzing project: {result.get('error')}"
        
        elif "search vector" in request or "vector search" in request:
            parts = request.split("for", 1)
            query = parts[1].strip() if len(parts) > 1 else ""
            project_dir = os.getcwd()
            
            result = await self.computer.vector_search(query, project_dir)
            if result.get("success", False):
                search_results = result.get("results", [])
                return f"Vector search results for '{query}':\n{json.dumps(search_results, indent=2)}"
            else:
                return f"Error searching vector store: {result.get('error')}"
        
        elif "index vector" in request or "vector index" in request:
            path = os.getcwd()
            # Extract path if provided
            if "path" in request:
                path = request.split("path", 1)[1].strip()
            
            result = await self.computer.vector_index(path)
            if result.get("success", False):
                return f"Vector indexing result:\n{result.get('message', '')}"
            else:
                return f"Error indexing: {result.get('error')}"
        
        elif "find symbol" in request:
            parts = request.split("find symbol", 1)
            symbol_name = parts[1].strip() if len(parts) > 1 else ""
            path = os.getcwd()
            
            result = await self.computer.symbol_find(path, symbol_name)
            if result.get("success", False):
                symbols = result.get("symbols", [])
                return f"Symbol search results for '{symbol_name}':\n{json.dumps(symbols, indent=2)}"
            else:
                return f"Error finding symbols: {result.get('error')}"
        
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
        
        elif "edit file" in request:
            # Parse the request for filename and edits
            parts = request.split("replace", 1)
            filename = parts[0].replace("edit file", "", 1).strip()
            
            if len(parts) < 2 or "with" not in parts[1]:
                return "Invalid edit format. Use: edit file <filename> replace <old_text> with <new_text>"
            
            replace_parts = parts[1].split("with", 1)
            old_text = replace_parts[0].strip()
            new_text = replace_parts[1].strip() if len(replace_parts) > 1 else ""
            
            # Get the full file path
            file_path = os.path.join(self.temp_dir, filename)
            if not os.path.exists(file_path):
                file_path = os.path.join(os.getcwd(), filename)
                if not os.path.exists(file_path):
                    return f"File not found: {filename}"
            
            # Prepare edits
            edits = [
                {"oldText": old_text, "newText": new_text}
            ]
            
            # Execute edit
            result = await self.computer.execute_operation(
                "edit_file", {"path": file_path, "edits": edits}
            )
            
            if result.get("success", False):
                return f"File edited successfully: {file_path}"
            else:
                return f"Error editing file: {result.get('error')}"
        
        elif "capabilities" in request:
            return f"Computer capabilities:\n{json.dumps(self.capabilities, indent=2)}"
        
        elif "help" in request:
            return """
Available commands:
- list files [in <directory>]
- run command <command>
- analyze project [in <directory>]
- search vector for <query>
- index vector [path <path>]
- find symbol <symbol_name>
- create file <filename> with content <content>
- read file <filename>
- edit file <filename> replace <old_text> with <new_text>
- capabilities
- help
- exit
"""
        
        elif "exit" in request:
            return "Exiting assistant..."
        
        else:
            return "I don't understand that command. Type 'help' for a list of available commands."


async def run_interactive_assistant():
    """Run an interactive session with the Dev assistant."""
    assistant = DevAssistantExample()
    await assistant.startup()
    
    print("\n=== Hanzo ACI-Dev Interactive Assistant ===")
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


async def run_automated_demo():
    """Run an automated demo of the Dev assistant."""
    print("\n=== Hanzo ACI-Dev Automated Demo ===")
    
    assistant = DevAssistantExample()
    await assistant.startup()
    
    # List of demo commands to run
    commands = [
        "capabilities",
        "list files",
        "create file test.py with content def example_function():\n    \"\"\"Example function for symbol finding.\"\"\"\n    return 'Hello, World!'",
        "read file test.py",
        "analyze project",
        "index vector",
        "search vector for function",
        "find symbol example_function",
        "edit file test.py replace Hello, World! with Greetings from Hanzo Dev!",
        "read file test.py"
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
    """Main entry point for the Dev integration example."""
    parser = argparse.ArgumentParser(description="Hanzo ACI-Dev Integration Example")
    
    parser.add_argument(
        "--mode",
        choices=["interactive", "demo"],
        default="interactive",
        help="Run mode (default: interactive)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.mode == "interactive":
            asyncio.run(run_interactive_assistant())
        else:
            asyncio.run(run_automated_demo())
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
