# Hanzo ACI (Abstract Computer Interface)

Hanzo ACI is a foundational library that provides comprehensive computer interaction capabilities for AI assistants. It serves as the core layer for tools like Hanzo MCP, Hanzo Dev, and Hanzo Code, providing unified access to file operations, application control, vector databases, symbolic search, and other advanced features.

## Architecture

```
                     ┌───────────────────────┐
                     │      AI Assistant      │
                     └──────────┬─────────────┘
                                │
         ┌─────────────────────┼──────────────────────┐
         │                     │                       │
         ▼                     ▼                       ▼
┌─────────────────┐   ┌─────────────────┐   ┌──────────────────┐
│   Hanzo Code    │   │   Claude Code   │   │     Hanzo MCP     │
│    CLI Tool     │   │  (3rd party)    │   │  (Meta Protocol)  │
└────────┬────────┘   └────────┬────────┘   └────────┬─────────┘
         │                     │                      │
         └─────────────────────┼──────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                │                              │
                ▼                              ▼
┌───────────────────────────┐      ┌─────────────────────────┐
│  Hanzo ACI (Core Library) │◄────►│  Hanzo Dev (Advanced)   │
└───────────────────────────┘      └─────────────────────────┘
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────┐ ┌───────────────┐ ┌──────────────────────┐  │
│  │ File Operations │ │ Command Tools │ │ Application Control  │  │
│  └────────────────┘ └───────────────┘ └──────────────────────┘  │
│                                                                  │
│  ┌────────────────┐ ┌───────────────┐ ┌──────────────────────┐  │
│  │ Vector Storage │ │ Symbol Search │ │ Project Analysis     │  │
│  └────────────────┘ └───────────────┘ └──────────────────────┘  │
│                                                                  │
│  ┌────────────────┐ ┌───────────────┐ ┌──────────────────────┐  │
│  │ Jupyter Tools  │ │ Browser Tools │ │ Permission System    │  │
│  └────────────────┘ └───────────────┘ └──────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                       Computer Resources                          │
└──────────────────────────────────────────────────────────────────┘
```

## Key Features

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
## Integration with Hanzo Dev

```python
from hanzo_aci.integrations.dev import DevComputerInterface

# Use with Hanzo Dev for advanced reasoning capabilities
interface = DevComputerInterface()

# Get all symbols in a project
symbols = await interface.symbol_find("/path/to/project")

# Use vector search for semantic code understanding
results = await interface.vector_search("function to process payments", "/path/to/project")
```
## Specialized Modules

Hanzo ACI provides specialized modules for specific code analysis and AI capabilities:

### Vector Search

```python
from hanzo_aci.specialized.vector_search import VectorSearchInterface

# Create a vector search interface
vector_search = VectorSearchInterface()

# Load a collection
await vector_search.execute_operation("load_collection", {"path": "/path/to/project"})

# Search for semantically similar code
results = await vector_search.execute_operation(
    "vector_search",
    {"query": "function to process payments", "n_results": 5}
)

# Index new content
await vector_search.execute_operation(
    "vector_index",
    {"documents": ["def payment():", "class Payment:"], "metadatas": [{...}, {...}]}
)
```

### Symbolic Reasoning

```python
from hanzo_aci.specialized.symbolic_reasoning import SymbolicReasoningInterface

# Create a symbolic reasoning interface
symbolic = SymbolicReasoningInterface()

# Find all symbols in a file
symbols = await symbolic.execute_operation(
    "find_symbols",
    {"file_path": "/path/to/file.py"}
)

# Find references to a specific function
references = await symbolic.execute_operation(
    "find_references",
    {"file_path": "/path/to/file.py", "symbol_name": "process_payment"}
)

# Analyze dependencies between symbols
dependencies = await symbolic.execute_operation(
    "analyze_dependencies",
    {"file_path": "/path/to/file.py"}
)
```

## Using with MCP

Both the vector search and symbolic reasoning modules can be exposed as separate tools through MCP:

```python
from hanzo_mcp.tools.mcp_manager import MCPServerManager
from hanzo_aci.specialized.vector_search import VectorSearchInterface
from hanzo_aci.specialized.symbolic_reasoning import SymbolicReasoningInterface

# Create MCP server manager
manager = MCPServerManager()

# Create specialized tools
vector_search = VectorSearchInterface()
symbolic = SymbolicReasoningInterface()

# Register the tools with MCP
manager.register_server("vector-search", vector_search)
manager.register_server("symbolic-reason", symbolic)

# Now LLMs can use these tools in parallel through MCP
```

## Installation Options

Hanzo ACI is designed to be installed with the components you need:

```bash
# Install the core package
pip install hanzo-aci

# Install with Hanzo Dev integration
pip install 'hanzo-aci[hanzo-dev]'

# Install with vector database support
pip install 'hanzo-aci[vectordb]'

# Install with symbolic reasoning support
pip install 'hanzo-aci[symbolic]'

# Install with MCP integration
pip install 'hanzo-aci[mcp]'

# Install with all components
pip install 'hanzo-aci[all]'
```
