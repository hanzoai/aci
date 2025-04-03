"""Command execution tools for Hanzo ACI.

This module provides tools for executing shell commands and scripts with
comprehensive error handling and security controls.
"""

import asyncio
import os
import subprocess
import sys
from typing import Dict, List, Optional, Tuple, Any, final

from hanzo_aci.tools.common.permissions import PermissionManager


@final
class CommandResult:
    """Represents the result of a command execution."""

    def __init__(
        self,
        return_code: int = 0,
        stdout: str = "",
        stderr: str = "",
        error_message: Optional[str] = None,
    ):
        """Initialize a command result.

        Args:
            return_code: The command's return code (0 for success)
            stdout: Standard output from the command
            stderr: Standard error from the command
            error_message: Optional error message for failure cases
        """
        self.return_code: int = return_code
        self.stdout: str = stdout
        self.stderr: str = stderr
        self.error_message: Optional[str] = error_message

    @property
    def is_success(self) -> bool:
        """Check if the command executed successfully.

        Returns:
            True if the command succeeded, False otherwise
        """
        return self.return_code == 0

    def format_output(self, include_exit_code: bool = True) -> str:
        """Format the command output as a string.

        Args:
            include_exit_code: Whether to include the exit code in the output

        Returns:
            Formatted output string
        """
        result_parts: List[str] = []

        # Add error message if present
        if self.error_message:
            result_parts.append(f"Error: {self.error_message}")

        # Add exit code if requested and not zero (for non-errors)
        if include_exit_code and (self.return_code != 0 or not self.error_message):
            result_parts.append(f"Exit code: {self.return_code}")

        # Add stdout if present
        if self.stdout:
            result_parts.append(f"STDOUT:\n{self.stdout}")

        # Add stderr if present
        if self.stderr:
            result_parts.append(f"STDERR:\n{self.stderr}")

        # Join with newlines
        return "\n\n".join(result_parts)


@final
class CommandExecutor:
    """Executes shell commands and scripts with security controls."""
    
    def __init__(self, permission_manager: PermissionManager, verbose: bool = False) -> None:
        """Initialize the command executor.
        
        Args:
            permission_manager: The permission manager to use for path validation
            verbose: Whether to enable verbose output
        """
        self.permission_manager = permission_manager
        self.verbose = verbose
        self.excluded_commands = ["rm", "rmdir", "dd"]
        
    def is_command_allowed(self, command: str) -> bool:
        """Check if a command is allowed to be executed.
        
        Args:
            command: The command to check
            
        Returns:
            True if the command is allowed, False otherwise
        """
        # Simple check for dangerous commands
        words = command.split()
        if not words:
            return False
            
        base_command = words[0]
        
        # Check against excluded commands
        if base_command in self.excluded_commands:
            return False
            
        return True
        
    async def run_command(self, tool_context: Any, command: str, cwd: str, use_login_shell: bool = True) -> str:
        """Run a shell command.
        
        Args:
            tool_context: The tool context
            command: The command to run
            cwd: Working directory for the command
            use_login_shell: Whether to use login shell
            
        Returns:
            Command output as a JSON string
        """
        if not self.is_command_allowed(command):
            return await tool_context.success(
                f"Command not allowed: {command}",
                {
                    "success": False,
                    "error": f"Command not allowed for security reasons: {command}"
                }
            )
            
        if not self.permission_manager.is_path_allowed(cwd):
            return await tool_context.success(
                f"Path not allowed: {cwd}",
                {
                    "success": False,
                    "error": f"Path not allowed for security reasons: {cwd}"
                }
            )
            
        try:
            # Execute the command
            result = await self.execute_command(command, cwd, use_login_shell)
            
            if result.is_success:
                return await tool_context.success(
                    "Command executed successfully",
                    {
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "exit_code": result.return_code
                    }
                )
            else:
                return await tool_context.success(
                    "Command execution failed",
                    {
                        "success": False,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "error": result.error_message or f"Exit code {result.return_code}",
                        "exit_code": result.return_code
                    }
                )
        except Exception as e:
            return await tool_context.success(
                "Command execution error",
                {
                    "success": False,
                    "error": str(e)
                }
            )
    
    async def execute_command(
        self, 
        command: str, 
        cwd: Optional[str] = None,
        use_login_shell: bool = True,
        timeout: float = 30.0
    ) -> CommandResult:
        """Execute a command in a subprocess.
        
        Args:
            command: The command to execute
            cwd: Working directory for the command
            use_login_shell: Whether to use login shell
            timeout: Timeout in seconds
            
        Returns:
            CommandResult with the execution results
        """
        try:
            # Prepare the shell command
            if use_login_shell:
                # Get the user's shell
                shell = os.environ.get("SHELL", "/bin/bash")
                full_command = f"{shell} -l -c '{command}'"
            else:
                full_command = command
            
            if self.verbose:
                print(f"Executing: {full_command}")
                if cwd:
                    print(f"Working directory: {cwd}")
            
            # Execute the command
            process = await asyncio.create_subprocess_shell(
                full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
                
                stdout = stdout_bytes.decode("utf-8", errors="replace")
                stderr = stderr_bytes.decode("utf-8", errors="replace")
                
                return CommandResult(
                    return_code=process.returncode or 0,
                    stdout=stdout,
                    stderr=stderr
                )
            except asyncio.TimeoutError:
                # Kill the process if it times out
                try:
                    process.kill()
                except ProcessLookupError:
                    pass  # Process already terminated
                
                return CommandResult(
                    return_code=-1,
                    error_message=f"Command timed out after {timeout} seconds: {command}"
                )
        except Exception as e:
            return CommandResult(
                return_code=1,
                error_message=f"Error executing command: {str(e)}"
            )
    
    async def run_script(
        self, 
        tool_context: Any, 
        script: str, 
        cwd: str, 
        interpreter: str = "bash",
        use_login_shell: bool = True
    ) -> str:
        """Run a script with the specified interpreter.
        
        Args:
            tool_context: The tool context
            script: The script content
            cwd: Working directory for the script
            interpreter: The interpreter to use
            use_login_shell: Whether to use login shell
            
        Returns:
            Script output as a JSON string
        """
        if not self.permission_manager.is_path_allowed(cwd):
            return await tool_context.success(
                f"Path not allowed: {cwd}",
                {
                    "success": False,
                    "error": f"Path not allowed for security reasons: {cwd}"
                }
            )
            
        try:
            # Create a temporary file for the script
            import tempfile
            
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=f".{interpreter}") as temp:
                temp_path = temp.name
                temp.write(script)
            
            try:
                # Make the script executable
                os.chmod(temp_path, 0o755)
                
                # Execute the script
                command = f"{interpreter} {temp_path}"
                result = await self.execute_command(command, cwd, use_login_shell)
                
                if result.is_success:
                    return await tool_context.success(
                        "Script executed successfully",
                        {
                            "stdout": result.stdout,
                            "stderr": result.stderr,
                            "exit_code": result.return_code
                        }
                    )
                else:
                    return await tool_context.success(
                        "Script execution failed",
                        {
                            "success": False,
                            "stdout": result.stdout,
                            "stderr": result.stderr,
                            "error": result.error_message or f"Exit code {result.return_code}",
                            "exit_code": result.return_code
                        }
                    )
            finally:
                # Clean up the temporary file
                try:
                    os.unlink(temp_path)
                except:
                    pass
        except Exception as e:
            return await tool_context.success(
                "Script execution error",
                {
                    "success": False,
                    "error": str(e)
                }
            )
