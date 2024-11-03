# Oh-Viewer

A command line file viewer with code intelligence.

## Features

- Directory structure exploration
- File content viewing with line range support
- Symbol definition lookup with cross-file support
- Symbol reference finding across files
- Comprehensive symbol information

## Requirements

For code intelligence features, you need to have the tree-sitter CLI installed:

```bash
npm install -g tree-sitter-cli
```

## Installation

```bash
pip install oh-viewer
```

## Usage

After installation, the `oh-viewer` command will be available in your terminal:

```bash
# Explore directory structure
oh-viewer explore <path>

# View file content
oh-viewer view <filepath> [--start-line/-s LINE] [--end-line/-e LINE]

# Find symbol definition
oh-viewer find-def <filepath> <symbol>

# Find symbol references
oh-viewer find-refs <filepath> <symbol>

# Get symbol information
oh-viewer symbol-info <filepath> <symbol>
```

## Code Intelligence Setup

The code intelligence features require tree-sitter language parsers. After installing tree-sitter-cli, you'll need to:

1. Clone the language parsers you need (e.g., tree-sitter-python for Python support)
2. Build the parsers using tree-sitter CLI
3. Place the built parsers in a directory that oh-viewer can find

For example, to set up Python support:

```bash
# Create parsers directory
mkdir -p tree-sitter-parsers
cd tree-sitter-parsers

# Clone and build Python parser
git clone https://github.com/tree-sitter/tree-sitter-python
cd tree-sitter-python
tree-sitter generate
tree-sitter test
```

## License

MIT License