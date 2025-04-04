# Default target
all: install test

.PHONY: all install install-dev install-test reinstall uninstall test test-cov lint format clean build publish

# ANSI color codes
GREEN=$(shell tput -Txterm setaf 2)
YELLOW=$(shell tput -Txterm setaf 3)
RED=$(shell tput -Txterm setaf 1)
BLUE=$(shell tput -Txterm setaf 6)
RESET=$(shell tput -Txterm sgr0)

# Variables
PYTHON_VERSION = 3.13
SRC_DIR = hanzo_aci
TEST_DIR = tests

# Install the package in development mode
install:
	@echo "$(YELLOW)Installing hanzo-aci...$(RESET)"
	@uv pip install -e .
	@echo "$(GREEN)Installation complete.$(RESET)"

# Install with development dependencies
install-dev:
	@echo "$(YELLOW)Installing development dependencies...$(RESET)"
	@uv pip install -e ".[dev]"
	@echo "$(GREEN)Development dependencies installed.$(RESET)"

# Install with test dependencies
install-test:
	@echo "$(YELLOW)Installing test dependencies...$(RESET)"
	@uv pip install -e ".[dev]"
	@echo "$(GREEN)Test dependencies installed.$(RESET)"

# Uninstall the package
uninstall:
	@echo "$(YELLOW)Uninstalling package...$(RESET)"
	@uv pip uninstall -y hanzo-aci
	@echo "$(GREEN)Uninstallation complete.$(RESET)"

# Reinstall the package
reinstall: uninstall install
	@echo "$(GREEN)Reinstallation complete.$(RESET)"

# Run tests
test: install-test
	@echo "$(YELLOW)Running tests...$(RESET)"
	@python -m pytest $(TEST_DIR)
	@echo "$(GREEN)Tests complete.$(RESET)"

# Run tests with coverage
test-cov: install-test
	@echo "$(YELLOW)Running tests with coverage...$(RESET)"
	@python -m pytest --cov=$(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)Tests with coverage complete.$(RESET)"

# Run linters
lint: install-dev
	@echo "$(YELLOW)Running linters...$(RESET)"
	@python -m ruff check $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)Linting complete.$(RESET)"

# Format code
format: install-dev
	@echo "$(YELLOW)Formatting code...$(RESET)"
	@python -m ruff format $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)Formatting complete.$(RESET)"

# Clean build artifacts
clean:
	@echo "$(YELLOW)Cleaning build artifacts...$(RESET)"
	@rm -rf build/ dist/ *.egg-info/ .pytest_cache/ htmlcov/ .coverage 2>/dev/null || true
	@find . -name "__pycache__" -type d -exec rm -rf {} +
	@echo "$(GREEN)Cleaning complete.$(RESET)"

# Build package distributions
build: clean
	@echo "$(YELLOW)Building package...$(RESET)"
	@uv pip install build
	@uv run python -m build
	@echo "$(GREEN)Build complete. Distributions in 'dist/' directory.$(RESET)"

# Upload package to PyPI
publish: build
	@echo "$(YELLOW)Publishing package to PyPI...$(RESET)"
	@uv pip install twine
	@uv run twine upload dist/*
	@echo "$(GREEN)Publishing to PyPI complete.$(RESET)"

# Display help
help:
	@echo "$(BLUE)Usage: make [target]$(RESET)"
	@echo ""
	@echo "Targets:"
	@echo "  $(GREEN)all$(RESET)          - Install dependencies and run tests"
	@echo "  $(GREEN)install$(RESET)      - Install package in development mode"
	@echo "  $(GREEN)install-dev$(RESET)  - Install package with development dependencies"
	@echo "  $(GREEN)install-test$(RESET) - Install package with test dependencies"
	@echo "  $(GREEN)test$(RESET)         - Run tests"
	@echo "  $(GREEN)test-cov$(RESET)     - Run tests with coverage"
	@echo "  $(GREEN)lint$(RESET)         - Run linters"
	@echo "  $(GREEN)format$(RESET)       - Format code"
	@echo "  $(GREEN)clean$(RESET)        - Clean build artifacts"
	@echo "  $(GREEN)build$(RESET)        - Build package distributions"
	@echo "  $(GREEN)publish$(RESET)      - Publish package to PyPI"
	@echo "  $(GREEN)help$(RESET)         - Display this help message"
