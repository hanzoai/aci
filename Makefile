.PHONY: install test clean format lint build dev-install

# Install in development mode
install:
	pip install -e .

# Install in development mode with all dependencies
dev-install:
	pip install -e ".[dev,mcp,all]"

# Run tests
test:
	pytest tests/

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf **/__pycache__/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage

# Format code
format:
	black hanzo_aci/ tests/ examples/

# Run linting
lint:
	ruff hanzo_aci/ tests/ examples/

# Build package
build: clean
	python -m build

# Run the CLI
run:
	python -m hanzo_aci.cli

# Run the example
example:
	python examples/getting_started.py

# Run the integration example
integration:
	python examples/integration_example.py --mode demo

# Run the basic usage example
basic:
	python examples/basic_usage.py
