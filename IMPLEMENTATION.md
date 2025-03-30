# Hanzo ACI Implementation Details

This document provides an overview of the Hanzo ACI (Abstract Computer Interface) implementation.

## Overview

Hanzo ACI is designed as a foundational library that provides comprehensive computer interaction capabilities. It serves as the underlying layer for both Hanzo MCP and Hanzo Code, allowing AI assistants to interact with the computer in a controlled and secure manner.

The key architectural principle is that ACI is the core component that implements direct computer interaction, while MCP and Code act as consumers of this functionality.

## Key Components

### 1. Core Computer Interface

The `ComputerInterface` abstract base class in `hanzo_aci/interface.py` defines the fundamental API that all computer operations must implement, including:

- File operations (read, write, list)
- Command execution
- Application control
- Clipboard management
- Screenshot capturing
- Vector storage and search
- Symbol and code analysis
- Project analysis

### 2. Advanced Features

ACI includes advanced features that were previously in MCP:

- **Vector Database**: Embedding and retrieval of code and content
- **Symbolic Search**: Code structure analysis and symbol search
- **Project Analysis**: Code dependency and structure analysis
- **Jupyter Tools**: Notebook operations and execution
- **Browser Tools**: Web automation capabilities

### 3. Implementation Layers

The implementation follows a layered approach:

- **Core Interface**: Defines the API contract
- **Native Implementation**: Direct system calls for operations
- **Permission System**: Security layer for controlled access
- **Specialized Tools**: Implements advanced features

## Consumer Applications

### Hanzo MCP (Meta Context Protocol)

MCP is refactored to be a meta-protocol that uses ACI for computer interactions. This simplifies MCP to focus on:

- Protocol management
- Server orchestration
- Tool registry and discovery
- API interfaces for AI assistants

### Hanzo Code

The Hanzo Code CLI tool uses ACI directly to:

- Edit files on the computer
- Execute commands
- Control applications
- Leverage advanced features like vector search

## Integration Approaches

### ACI Usage in MCP

MCP imports ACI and uses it for:

- File operations through the `dev` tool
- Computer interface through the `computer_use` tool
- Vector storage and search capabilities
- Code analysis and symbolic search

### ACI Usage in Hanzo Code

Hanzo Code imports ACI directly to:

- Edit files on the local system
- Execute commands
- Control applications
- Access advanced analysis features

### Independent ACI Usage

ACI can also be used independently by:

- AI assistants that need direct computer access
- Development tools that need computer interaction
- Testing and automation frameworks

## Testing Strategy

The testing approach for ACI includes:

1. **Unit Tests**: For individual components and features
2. **Integration Tests**: For interactions between features
3. **System Tests**: For end-to-end workflows
4. **Consumer Tests**: For MCP and Code integration

## Security Considerations

Security is a primary concern, with several layers of protection:

1. **Permission System**: Granular control over allowed operations
2. **Path Validation**: Prevention of path traversal attacks
3. **Command Sanitization**: Safe execution of shell commands
4. **Content Validation**: Checking file content before operations

## Future Directions

Future development of ACI could include:

1. **Expanded Integration**: Support for more AI platforms
2. **Remote Computer Control**: Network-based computer interaction
3. **Enhanced Security**: More sophisticated permission models
4. **Performance Optimization**: Faster operations for large projects
5. **UI Interaction**: More sophisticated GUI automation

## Conclusion

Hanzo ACI provides a solid foundation for computer interaction capabilities, with MCP and Hanzo Code building upon this foundation to deliver their respective functionality. This architecture ensures a clean separation of concerns, with ACI handling the direct computer interaction while the consuming applications focus on their specific use cases.
