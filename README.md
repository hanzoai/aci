# Agent-Computer Interface (ACI) for Hanzo

An Agent-Computer Interface (ACI) designed for [Hanzo IDE](https://github.com/hanzoai/ide). This package provides essential tools and interfaces for AI agents to interact with computer systems for software development tasks.

## Features

- **Code Editor Interface**: Sophisticated editing capabilities through the `editor` module
  - File creation and modification
  - Code editing
  - Configuration management

- **Code Linting**: Built-in linting capabilities via the `linter` module
  - Tree-sitter based code analysis
  - Python-specific linting support

- **Utility Functions**: Helper modules for common operations
  - Shell command execution utilities
  - Diff generation and analysis
  - Logging functionality

## Installation

```bash
pip install hanzo-aci
```

Or using Poetry:

```bash
poetry add hanzo-aci
```

## Project Structure

```
hanzo_aci/
├── editor/           # Code editing functionality
├── linter/           # Code linting capabilities
└── utils/            # Utility functions
```

## Development

1. Clone the repository:
```bash
git clone https://github.com/hanzoai/aci.git
cd aci
```

2. Install development dependencies:
```bash
poetry install --extras llama
```

3. Configure pre-commit-hooks
```bash
make install-pre-commit-hooks
```

4. Run tests:
```bash
poetry run pytest
```

## License

This project is licensed under the MIT License.
