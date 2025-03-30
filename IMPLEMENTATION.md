# Hanzo ACI Implementation Details

This document provides an overview of the Hanzo ACI (Abstract Computer Interface) implementation.

## Overview

Hanzo ACI is designed to provide a unified interface for AI assistants to interact with the computer. It supports multiple backends, including:

1. **Native Backend**: Direct system calls for computer operations
2. **MCP Backend**: Integration with Hanzo MCP for server-based operations
3. **Claude Code Backend**: Integration with Claude Code CLI for AI-assisted operations

The library is designed to be easy to use, with a clean API that abstracts away the details of the underlying implementation.

## Key Components

### 1. Interface Definition

The core of the library is the `ComputerInterface` abstract base class in `hanzo_aci/interface.py`. This defines the API that all backends must implement, including:

- File operations (read, write, list)
- Command execution
- Application control
- Clipboard management
- Screenshot capturing

### 2. Backend Implementations

- **Native Backend** (`hanzo_aci/tools/native.py`): Direct system calls for operations
- **MCP Backend** (`hanzo_aci/integrations/mcp.py`): Integration with Hanzo MCP
- **Claude Code Backend** (`hanzo_aci/integrations/claude_code.py`): Integration with Claude Code

### 3. Concrete Implementation

The `ConcreteComputerInterface` in `hanzo_aci/concrete.py` provides a high-level implementation that:

- Automatically selects the best available backend
- Provides a unified API for all operations
- Handles fallbacks when preferred backends are not available

### 4. CLI Tool

The `hanzo-aci` command-line tool in `hanzo_aci/cli.py` provides:

- Direct access to computer operations
- A stdio mode for integration with AI assistants
- Backend selection and configuration

## Integration Approaches

### With MCP

The MCP integration works by connecting to the computer-use MCP server, which provides:

- Server management (start, stop, restart)
- Tool discovery and execution
- Consistent error handling

### With Claude Code

The Claude Code integration works by executing the Claude Code CLI with:

- Natural language commands for operations
- JSON parsing for structured responses
- Temporary file handling for complex operations

### With AI Assistants

AI assistants can use Hanzo ACI in several ways:

1. **Direct Python API**: Import and use the library in Python code
2. **CLI Tool**: Execute `hanzo-aci` commands from a subprocess
3. **Stdio Interface**: Use the stdio mode for a JSON-based protocol

## Examples

The repository includes several examples:

- **Getting Started** (`examples/getting_started.py`): Basic usage of the API
- **Basic Usage** (`examples/basic_usage.py`): More detailed API usage
- **Integration Example** (`examples/integration_example.py`): A complete AI assistant example

## Future Improvements

Future versions of Hanzo ACI could include:

1. **More Backends**: Support for additional platforms and tools
2. **Enhanced Security**: More granular permission controls
3. **GUI Integration**: Direct interaction with graphical interfaces
4. **Remote Operations**: Support for remote computers
5. **Extended Capabilities**: More advanced computer operations

## Integration with Claude Desktop and MCP

The library is designed to work seamlessly with both Claude Desktop and Hanzo MCP:

- **Claude Desktop**: Uses the stdio interface for JSON-based communication
- **Hanzo MCP**: Uses the MCP server for computer operations

This creates a complete ecosystem for AI-assisted development, where:

1. Claude Desktop provides the AI assistant interface
2. Hanzo MCP provides the server infrastructure
3. Hanzo ACI provides the unified computer interface

Together, these tools enable powerful AI-assisted development workflows that can interact with the computer in a safe and controlled way.
