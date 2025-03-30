"""Native implementation of computer interface tools.

This module provides direct implementations of computer interactions without
relying on external tools like MCP or Claude Code.
"""

import os
import sys
import tempfile
import subprocess
import platform
import asyncio
import logging
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from hanzo_aci.interface import ComputerInterface

logger = logging.getLogger(__name__)


class NativeComputerInterface(ComputerInterface):
    """Native implementation of the computer interface.
    
    This implementation uses direct system calls to interact with the computer
    rather than relying on external tools.
    """
    
    def __init__(self, permit_all: bool = False):
        """Initialize the native computer interface.
        
        Args:
            permit_all: If True, bypass permission checks for all operations.
                This is dangerous and should only be used in controlled environments.
        """
        self._permit_all = permit_all
        self._permissions = {}
        
        # Path for storing screenshots
        self._screenshot_dir = os.path.join(tempfile.gettempdir(), "hanzo_aci_screenshots")
        os.makedirs(self._screenshot_dir, exist_ok=True)
    
    async def is_available(self) -> bool:
        """Check if the native interface is available.
        
        The native interface is always available, but some operations
        may not be supported on all platforms.
        
        Returns:
            Always returns True
        """
        return True
    
    async def ensure_running(self) -> Dict[str, Any]:
        """Ensure that the native interface is ready to use.
        
        The native interface doesn't need to be started, so this is a no-op.
        
        Returns:
            Success status
        """
        return {
            "success": True,
            "message": "Native interface is always available."
        }
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get information about the native interface capabilities.
        
        Returns:
            Dictionary with information about available operations
        """
        # Determine capabilities based on the platform
        system = platform.system()
        
        # Define base capabilities available on all platforms
        capabilities = {
            "file_operations": [
                "list_files",
                "read_file",
                "write_file"
            ],
            "command_operations": [
                "run_command"
            ],
            "system_operations": []
        }
        
        # Add platform-specific capabilities
        if system == "Darwin":  # macOS
            capabilities["system_operations"].extend([
                "take_screenshot",
                "clipboard_get",
                "clipboard_set",
                "open_application",
                "file_explorer"
            ])
        elif system == "Linux":
            capabilities["system_operations"].extend([
                "take_screenshot",
                "clipboard_get",
                "clipboard_set"
            ])
            # Check for specific desktop environments
            desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
            if desktop in ["gnome", "kde", "xfce"]:
                capabilities["system_operations"].extend([
                    "open_application",
                    "file_explorer"
                ])
        elif system == "Windows":
            capabilities["system_operations"].extend([
                "take_screenshot",
                "clipboard_get",
                "clipboard_set",
                "open_application",
                "file_explorer"
            ])
        
        return {
            "available": True,
            "platform": system,
            "capabilities": capabilities
        }
    
    def _check_permission(self, operation: str, path: Optional[str] = None) -> bool:
        """Check if an operation is permitted.
        
        Args:
            operation: The operation to check
            path: Optional path for file operations
            
        Returns:
            True if the operation is permitted, False otherwise
        """
        if self._permit_all:
            return True
        
        # Check if we have a permission entry for this operation
        if operation in self._permissions:
            if path:
                # Check if we have permission for this path
                for allowed_path in self._permissions[operation]:
                    if path.startswith(allowed_path):
                        return True
                return False
            else:
                # General permission for this operation
                return self._permissions[operation] is True
        
        # Default to asking for permission
        return False
    
    def grant_permission(self, operation: str, path: Optional[str] = None) -> None:
        """Grant permission for an operation.
        
        Args:
            operation: The operation to permit
            path: Optional path to restrict the permission to
        """
        if path:
            if operation not in self._permissions:
                self._permissions[operation] = []
            self._permissions[operation].append(path)
        else:
            self._permissions[operation] = True
    
    async def execute_operation(
        self,
        operation: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an operation natively.
        
        Args:
            operation: The operation to execute
            params: Parameters for the operation
            
        Returns:
            Operation result
        """
        # Map operations to handlers
        operation_map = {
            "list_files": self._list_files,
            "read_file": self._read_file,
            "write_file": self._write_file,
            "take_screenshot": self._take_screenshot,
            "run_command": self._run_command,
            "clipboard_get": self._clipboard_get,
            "clipboard_set": self._clipboard_set,
            "open_application": self._open_application,
            "file_explorer": self._file_explorer,
            "get_environment": self._get_environment
        }
        
        # Check if the operation is supported
        if operation not in operation_map:
            return {
                "success": False,
                "error": f"Operation not supported: {operation}"
            }
        
        # Execute the operation
        return await operation_map[operation](params)
    
    async def _list_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List files in a directory."""
        path = params.get("path", ".")
        
        # Check permission
        if not self._check_permission("list_files", path):
            return {
                "success": False,
                "error": f"Permission denied for listing files in {path}"
            }
        
        try:
            # Check if the path exists
            if not os.path.exists(path):
                return {
                    "success": False,
                    "error": f"Path does not exist: {path}"
                }
            
            # List files and directories
            entries = os.listdir(path)
            result = {
                "success": True,
                "files": [],
                "directories": []
            }
            
            for entry in entries:
                entry_path = os.path.join(path, entry)
                if os.path.isfile(entry_path):
                    result["files"].append(entry)
                elif os.path.isdir(entry_path):
                    result["directories"].append(entry)
            
            return result
        except Exception as e:
            logger.error(f"Error listing files in {path}: {str(e)}")
            return {
                "success": False,
                "error": f"Error listing files: {str(e)}"
            }
    
    async def _read_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read a file."""
        path = params.get("path")
        if not path:
            return {
                "success": False,
                "error": "Path is required for read_file operation"
            }
        
        # Check permission
        if not self._check_permission("read_file", path):
            return {
                "success": False,
                "error": f"Permission denied for reading file {path}"
            }
        
        try:
            # Check if the file exists
            if not os.path.exists(path):
                return {
                    "success": False,
                    "error": f"File does not exist: {path}"
                }
            
            # Read the file
            with open(path, "r") as f:
                content = f.read()
            
            return {
                "success": True,
                "content": content
            }
        except UnicodeDecodeError:
            # Try reading as binary
            try:
                with open(path, "rb") as f:
                    content = f.read()
                
                return {
                    "success": True,
                    "content": f"Binary content: {len(content)} bytes",
                    "binary": True,
                    "size": len(content)
                }
            except Exception as e:
                logger.error(f"Error reading file {path}: {str(e)}")
                return {
                    "success": False,
                    "error": f"Error reading file: {str(e)}"
                }
        except Exception as e:
            logger.error(f"Error reading file {path}: {str(e)}")
            return {
                "success": False,
                "error": f"Error reading file: {str(e)}"
            }
    
    async def _write_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Write to a file."""
        path = params.get("path")
        content = params.get("content")
        if not path or content is None:
            return {
                "success": False,
                "error": "Path and content are required for write_file operation"
            }
        
        # Check permission
        if not self._check_permission("write_file", path):
            return {
                "success": False,
                "error": f"Permission denied for writing to file {path}"
            }
        
        try:
            # Create parent directories if needed
            parent_dir = os.path.dirname(path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
            
            # Write the file
            with open(path, "w") as f:
                f.write(content)
            
            return {
                "success": True,
                "message": f"File written: {path}"
            }
        except Exception as e:
            logger.error(f"Error writing to file {path}: {str(e)}")
            return {
                "success": False,
                "error": f"Error writing file: {str(e)}"
            }
    
    async def _take_screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Take a screenshot."""
        # Check permission
        if not self._check_permission("take_screenshot"):
            return {
                "success": False,
                "error": "Permission denied for taking screenshots"
            }
        
        try:
            # Create a filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            output_path = os.path.join(self._screenshot_dir, filename)
            
            # Detect platform
            system = platform.system()
            
            if system == "Darwin":  # macOS
                process = await asyncio.create_subprocess_exec(
                    "screencapture", "-x", output_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            elif system == "Linux":
                # Try different screenshot tools
                if shutil.which("gnome-screenshot"):
                    process = await asyncio.create_subprocess_exec(
                        "gnome-screenshot", "-f", output_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                elif shutil.which("import"):
                    process = await asyncio.create_subprocess_exec(
                        "import", "-window", "root", output_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                else:
                    return {
                        "success": False,
                        "error": "No screenshot tool available on this system"
                    }
            elif system == "Windows":
                # On Windows, PowerShell can take screenshots
                script = f"""
                Add-Type -AssemblyName System.Windows.Forms
                Add-Type -AssemblyName System.Drawing
                $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
                $bitmap = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height
                $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
                $graphics.CopyFromScreen($screen.X, $screen.Y, 0, 0, $screen.Size)
                $bitmap.Save('{output_path}')
                """
                with tempfile.NamedTemporaryFile(suffix=".ps1", delete=False) as f:
                    f.write(script.encode())
                    ps_script = f.name
                
                process = await asyncio.create_subprocess_exec(
                    "powershell", "-ExecutionPolicy", "Bypass", "-File", ps_script,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                # Clean up the script file
                try:
                    os.unlink(ps_script)
                except:
                    pass
            else:
                return {
                    "success": False,
                    "error": f"Screenshots not supported on {system}"
                }
            
            # Wait for the process to complete
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return {
                    "success": False,
                    "error": f"Screenshot failed: {stderr.decode()}"
                }
            
            return {
                "success": True,
                "screenshot_path": output_path
            }
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            return {
                "success": False,
                "error": f"Error taking screenshot: {str(e)}"
            }
    
    async def _run_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Run a shell command."""
        command = params.get("command")
        cwd = params.get("cwd")
        
        if not command:
            return {
                "success": False,
                "error": "Command is required for run_command operation"
            }
        
        # Check permission
        if not self._check_permission("run_command"):
            return {
                "success": False,
                "error": "Permission denied for running commands"
            }
        
        try:
            # Set up the working directory
            if cwd and not os.path.exists(cwd):
                return {
                    "success": False,
                    "error": f"Working directory does not exist: {cwd}"
                }
            
            # Determine the shell to use
            shell = platform.system() == "Windows"
            
            # Run the command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                shell=shell
            )
            
            # Wait for the process to complete
            stdout, stderr = await process.communicate()
            
            # Decode the output
            stdout_str = stdout.decode(errors="replace")
            stderr_str = stderr.decode(errors="replace")
            
            return {
                "success": process.returncode == 0,
                "exit_code": process.returncode,
                "stdout": stdout_str,
                "stderr": stderr_str
            }
        except Exception as e:
            logger.error(f"Error running command: {str(e)}")
            return {
                "success": False,
                "error": f"Error running command: {str(e)}"
            }
    
    async def _clipboard_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get clipboard contents."""
        # Check permission
        if not self._check_permission("clipboard_get"):
            return {
                "success": False,
                "error": "Permission denied for accessing clipboard"
            }
        
        try:
            # Detect platform
            system = platform.system()
            
            if system == "Darwin":  # macOS
                process = await asyncio.create_subprocess_exec(
                    "pbpaste",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    return {
                        "success": False,
                        "error": f"Clipboard access failed: {stderr.decode()}"
                    }
                
                content = stdout.decode(errors="replace")
            elif system == "Linux":
                # Try different clipboard tools
                if shutil.which("xclip"):
                    process = await asyncio.create_subprocess_exec(
                        "xclip", "-o", "-selection", "clipboard",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                elif shutil.which("xsel"):
                    process = await asyncio.create_subprocess_exec(
                        "xsel", "--clipboard", "--output",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                else:
                    return {
                        "success": False,
                        "error": "No clipboard tool available on this system"
                    }
                
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    return {
                        "success": False,
                        "error": f"Clipboard access failed: {stderr.decode()}"
                    }
                
                content = stdout.decode(errors="replace")
            elif system == "Windows":
                # On Windows, PowerShell can access clipboard
                script = """
                Add-Type -AssemblyName System.Windows.Forms
                [System.Windows.Forms.Clipboard]::GetText()
                """
                with tempfile.NamedTemporaryFile(suffix=".ps1", delete=False) as f:
                    f.write(script.encode())
                    ps_script = f.name
                
                process = await asyncio.create_subprocess_exec(
                    "powershell", "-ExecutionPolicy", "Bypass", "-File", ps_script,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                # Clean up the script file
                try:
                    os.unlink(ps_script)
                except:
                    pass
                
                if process.returncode != 0:
                    return {
                        "success": False,
                        "error": f"Clipboard access failed: {stderr.decode()}"
                    }
                
                content = stdout.decode(errors="replace")
            else:
                return {
                    "success": False,
                    "error": f"Clipboard access not supported on {system}"
                }
            
            return {
                "success": True,
                "content": content
            }
        except Exception as e:
            logger.error(f"Error accessing clipboard: {str(e)}")
            return {
                "success": False,
                "error": f"Error accessing clipboard: {str(e)}"
            }
    
    async def _clipboard_set(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set clipboard contents."""
        text = params.get("text")
        if text is None:
            return {
                "success": False,
                "error": "Text is required for clipboard_set operation"
            }
        
        # Check permission
        if not self._check_permission("clipboard_set"):
            return {
                "success": False,
                "error": "Permission denied for modifying clipboard"
            }
        
        try:
            # Detect platform
            system = platform.system()
            
            if system == "Darwin":  # macOS
                # Create a temporary file with the content
                with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
                    f.write(text)
                    temp_file = f.name
                
                # Use pbcopy to set clipboard
                process = await asyncio.create_subprocess_exec(
                    "cat", temp_file, "|", "pbcopy",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    shell=True
                )
                
                stdout, stderr = await process.communicate()
                
                # Clean up the temporary file
                try:
                    os.unlink(temp_file)
                except:
                    pass
                
                if process.returncode != 0:
                    return {
                        "success": False,
                        "error": f"Clipboard modification failed: {stderr.decode()}"
                    }
            elif system == "Linux":
                # Create a temporary file with the content
                with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
                    f.write(text)
                    temp_file = f.name
                
                # Try different clipboard tools
                if shutil.which("xclip"):
                    process = await asyncio.create_subprocess_exec(
                        "cat", temp_file, "|", "xclip", "-selection", "clipboard",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        shell=True
                    )
                elif shutil.which("xsel"):
                    process = await asyncio.create_subprocess_exec(
                        "cat", temp_file, "|", "xsel", "--clipboard", "--input",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        shell=True
                    )
                else:
                    os.unlink(temp_file)
                    return {
                        "success": False,
                        "error": "No clipboard tool available on this system"
                    }
                
                stdout, stderr = await process.communicate()
                
                # Clean up the temporary file
                try:
                    os.unlink(temp_file)
                except:
                    pass
                
                if process.returncode != 0:
                    return {
                        "success": False,
                        "error": f"Clipboard modification failed: {stderr.decode()}"
                    }
            elif system == "Windows":
                # On Windows, PowerShell can modify clipboard
                script = f"""
                Add-Type -AssemblyName System.Windows.Forms
                [System.Windows.Forms.Clipboard]::SetText(@'
                {text}
                '@)
                """
                with tempfile.NamedTemporaryFile(suffix=".ps1", delete=False) as f:
                    f.write(script.encode())
                    ps_script = f.name
                
                process = await asyncio.create_subprocess_exec(
                    "powershell", "-ExecutionPolicy", "Bypass", "-File", ps_script,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                # Clean up the script file
                try:
                    os.unlink(ps_script)
                except:
                    pass
                
                if process.returncode != 0:
                    return {
                        "success": False,
                        "error": f"Clipboard modification failed: {stderr.decode()}"
                    }
            else:
                return {
                    "success": False,
                    "error": f"Clipboard modification not supported on {system}"
                }
            
            return {
                "success": True,
                "message": "Clipboard content set successfully"
            }
        except Exception as e:
            logger.error(f"Error modifying clipboard: {str(e)}")
            return {
                "success": False,
                "error": f"Error modifying clipboard: {str(e)}"
            }
    
    async def _open_application(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Open an application."""
        app_name = params.get("name")
        if not app_name:
            return {
                "success": False,
                "error": "Application name is required for open_application operation"
            }
        
        # Check permission
        if not self._check_permission("open_application"):
            return {
                "success": False,
                "error": "Permission denied for opening applications"
            }
        
        try:
            # Detect platform
            system = platform.system()
            
            if system == "Darwin":  # macOS
                process = await asyncio.create_subprocess_exec(
                    "open", "-a", app_name,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            elif system == "Linux":
                # Try different methods
                # First, try to execute the command directly
                process = await asyncio.create_subprocess_exec(
                    app_name,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                # If that fails, try using xdg-open
                if process.returncode != 0 and shutil.which("xdg-open"):
                    process = await asyncio.create_subprocess_exec(
                        "xdg-open", app_name,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
            elif system == "Windows":
                # On Windows, try to start the application
                process = await asyncio.create_subprocess_exec(
                    "start", app_name,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    shell=True
                )
            else:
                return {
                    "success": False,
                    "error": f"Opening applications not supported on {system}"
                }
            
            # Wait for the process to complete
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to open application: {stderr.decode()}"
                }
            
            return {
                "success": True,
                "message": f"Opened application: {app_name}"
            }
        except Exception as e:
            logger.error(f"Error opening application: {str(e)}")
            return {
                "success": False,
                "error": f"Error opening application: {str(e)}"
            }
    
    async def _file_explorer(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Open the file explorer at a specific path."""
        path = params.get("path", ".")
        
        # Check permission
        if not self._check_permission("file_explorer", path):
            return {
                "success": False,
                "error": f"Permission denied for opening file explorer at {path}"
            }
        
        try:
            # Check if the path exists
            if not os.path.exists(path):
                return {
                    "success": False,
                    "error": f"Path does not exist: {path}"
                }
            
            # Detect platform
            system = platform.system()
            
            if system == "Darwin":  # macOS
                process = await asyncio.create_subprocess_exec(
                    "open", path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            elif system == "Linux":
                # Try different file managers
                if shutil.which("xdg-open"):
                    process = await asyncio.create_subprocess_exec(
                        "xdg-open", path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                elif shutil.which("nautilus"):  # GNOME
                    process = await asyncio.create_subprocess_exec(
                        "nautilus", path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                elif shutil.which("dolphin"):  # KDE
                    process = await asyncio.create_subprocess_exec(
                        "dolphin", path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                elif shutil.which("thunar"):  # XFCE
                    process = await asyncio.create_subprocess_exec(
                        "thunar", path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                else:
                    return {
                        "success": False,
                        "error": "No file explorer available on this system"
                    }
            elif system == "Windows":
                # On Windows, we can use explorer.exe
                process = await asyncio.create_subprocess_exec(
                    "explorer", path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
            else:
                return {
                    "success": False,
                    "error": f"File explorer not supported on {system}"
                }
            
            # Wait for the process to complete
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to open file explorer: {stderr.decode()}"
                }
            
            return {
                "success": True,
                "message": f"Opened file explorer at: {path}"
            }
        except Exception as e:
            logger.error(f"Error opening file explorer: {str(e)}")
            return {
                "success": False,
                "error": f"Error opening file explorer: {str(e)}"
            }
    
    async def _get_environment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get the current environment variables."""
        # Check permission
        if not self._check_permission("get_environment"):
            return {
                "success": False,
                "error": "Permission denied for accessing environment variables"
            }
        
        try:
            # Get environment variables
            env_vars = dict(os.environ)
            
            # Remove sensitive variables
            sensitive_vars = [
                "API_KEY", "SECRET", "PASSWORD", "TOKEN", "CREDENTIAL",
                "APIKEY", "KEY", "PRIVATE", "AUTH"
            ]
            
            for var in list(env_vars.keys()):
                for sensitive in sensitive_vars:
                    if sensitive.lower() in var.lower():
                        env_vars[var] = "***REDACTED***"
            
            return {
                "success": True,
                "environment": env_vars
            }
        except Exception as e:
            logger.error(f"Error getting environment variables: {str(e)}")
            return {
                "success": False,
                "error": f"Error getting environment variables: {str(e)}"
            }


# Create a singleton instance for convenience
native_computer = NativeComputerInterface()
