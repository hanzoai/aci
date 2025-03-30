# Hanzo ACI (Abstract Computer Interface)

Hanzo ACI is a lightweight, cross-platform library that provides a consistent interface for AI assistants to interact with your computer. It's designed to be used with tools like Hanzo MCP and Claude Code, providing a unified way to perform operations like file manipulation, application control, and system automation.

## Architecture

```
┌───────────────────────────────────────────────────────────┐
│                       AI Assistant                        │
└───────────────────────────┬───────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────┐
│                       Hanzo ACI                           │
│                                                           │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────┐  │
│  │ Interface API │◄───┤Concrete Impl. │───►│Permissions│  │
│  └───────────────┘    └───────┬───────┘    └───────────┘  │
│                              │                            │
│  ┌─────────────┐  ┌──────────┴──────────┐  ┌───────────┐  │
│  │Native Backend│◄─┤   Backend Router   ├──►│MCP Backend│  │
│  └─────────────┘  └──────────┬──────────┘  └───────────┘  │
│                              │                            │
│                              │                            │
│                     ┌────────┴─────────┐                 │
│                     │ Claude Code Backend│                 │
│                     └──────────────────┘                 │
└───────────────────────────────────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────┐
│                   Computer Resources                      │
│   Files │ Applications │ Clipboard │ Shell │ Screenshots  │
└───────────────────────────────────────────────────────────┘
```

## Features

- **Unified Computer Interface**: Access computer capabilities through a consistent API
- **Multiple Integration Options**: Works with Hanzo MCP, Claude Code, and standalone usage
- **Secure by Design**: Permission-based access control for sensitive operations
- **Extensible Architecture**: Easy to add new capabilities and integrations

## Installation

```bash
# Install from pip
pip install hanzo-aci

# Install from source
git clone https://github.com/hanzo-ai/aci.git
cd aci
pip install -e .
```

## Quick Start

```python
from hanzo_aci import ComputerInterface

# Create interface instance
computer = ComputerInterface()

# Basic file operations
async def example():
    # Check capabilities
    capabilities = await computer.get_capabilities()
    print(f"Available capabilities: {capabilities}")
    
    # File operations
    files = await computer.list_files("/path/to/directory")
    
    # Application control
    result = await computer.open_application("Notes")
    
    # System operations
    clipboard = await computer.clipboard_get()
    screenshot = await computer.take_screenshot()
```

## Integration with Hanzo MCP

```python
from hanzo_aci.integrations.mcp import MCPComputerInterface

# Use with Hanzo MCP
interface = MCPComputerInterface()
await interface.ensure_running()

# Now use the same API
result = await interface.open_application("Terminal")
```

## Integration with Claude Code

```python
from hanzo_aci.integrations.claude_code import ClaudeCodeInterface

# Use with Claude Code
interface = ClaudeCodeInterface()

# Use the same unified API
result = await interface.clipboard_get()
```

## Architecture

Hanzo ACI follows a simple, layered architecture:

1. **Core Interface**: Defines the abstract API for computer interactions
2. **Integration Adapters**: Connect to different platforms (MCP, Claude Code, etc.)
3. **Tool Implementations**: Implement specific capabilities like file operations
4. **Security Layer**: Manages permissions and access control

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License

## Security

Hanzo ACI includes a permission system to control access to sensitive operations. Be careful when granting permissions and always review the code you're running.
