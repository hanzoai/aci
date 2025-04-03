# Default target
all: install test
	@echo "$(GREEN)All tasks completed.$(RESET)"

.PHONY: all install install-dev install-all uninstall reinstall test test-cov lint format clean venv venv-check build run example basic integration help check-dependencies check-system check-python check-uv

# ANSI color codes
GREEN=$(shell tput -Txterm setaf 2)
YELLOW=$(shell tput -Txterm setaf 3)
RED=$(shell tput -Txterm setaf 1)
BLUE=$(shell tput -Txterm setaf 6)
RESET=$(shell tput -Txterm sgr0)

# Variables
PYTHON_VERSION = 3.12
VENV_NAME ?= .venv
SRC_DIR = hanzo_aci
TEST_DIR = tests
EXAMPLES_DIR = examples

# Detect OS for proper path handling
ifeq ($(OS),Windows_NT)
	VENV_ACTIVATE = $(VENV_NAME)\Scripts\activate
	VENV_PYTHON = $(VENV_NAME)\Scripts\python.exe
	VENV_PIP = $(VENV_NAME)\Scripts\pip.exe
	RM_CMD = rmdir /s /q
	CP = copy
	SEP = \\
	ACTIVATE_CMD = call
else
	VENV_ACTIVATE = $(VENV_NAME)/bin/activate
	VENV_PYTHON = $(VENV_NAME)/bin/python
	VENV_PIP = $(VENV_NAME)/bin/pip
	RM_CMD = rm -rf
	CP = cp
	SEP = /
	ACTIVATE_CMD = source
endif

# Python interpreter and package manager
PYTHON = python

# Check if uv is available, otherwise use plain pip
UV := $(shell command -v uv 2> /dev/null)
ifeq ($(UV),)
	VENV_CMD = $(PYTHON) -m venv $(VENV_NAME)
else
	VENV_CMD = uv venv create --python=$(PYTHON_VERSION) $(VENV_NAME)
endif

# System & dependency checks
check-uv:
	@echo "$(YELLOW)Checking uv installation...$(RESET)"
	@if ! command -v uv > /dev/null; then \
		echo "$(YELLOW)uv not found. Installing uv...$(RESET)"; \
		pip install uv || { echo "$(RED)Failed to install uv. Please install it manually.$(RESET)"; exit 1; }; \
		echo "$(BLUE)uv installed successfully.$(RESET)"; \
	else \
		echo "$(BLUE)uv is installed: $$(uv --version 2>&1).$(RESET)"; \
	fi

check-python:
	@echo "$(YELLOW)Checking Python $(PYTHON_VERSION) installation...$(RESET)"
	@if ! command -v python$(PYTHON_VERSION) > /dev/null; then \
		echo "$(YELLOW)Python $(PYTHON_VERSION) not found. Installing it using uv...$(RESET)"; \
		uv python install $(PYTHON_VERSION) || { echo "$(RED)Failed to install Python $(PYTHON_VERSION).$(RESET)"; exit 1; }; \
		echo "$(BLUE)Python $(PYTHON_VERSION) installed.$(RESET)"; \
	else \
		echo "$(BLUE)$$(python$(PYTHON_VERSION) --version) is installed.$(RESET)"; \
	fi

check-system:
	@echo "$(YELLOW)Checking system...$(RESET)"
	@if [ "$$(uname)" = "Darwin" ]; then \
		echo "$(BLUE)macOS detected.$(RESET)"; \
	elif [ "$$(uname)" = "Linux" ]; then \
		echo "$(BLUE)Linux detected.$(RESET)"; \
	elif [ "$$(uname -r | grep -i microsoft)" ]; then \
		echo "$(BLUE)Windows Subsystem for Linux detected.$(RESET)"; \
	else \
		echo "$(RED)Unsupported system detected. Please use macOS, Linux, or WSL.$(RESET)"; \
		exit 1; \
	fi

check-dependencies: check-system check-uv check-python
	@echo "$(GREEN)Dependencies checked successfully.$(RESET)"

# Create virtual environment
venv: check-python
	@echo "$(YELLOW)Creating virtual environment...$(RESET)"
	@rm -rf $(VENV_NAME)
	@if [ -n "$(UV)" ]; then \
		echo "$(BLUE)Using uv to create virtual environment...$(RESET)"; \
		uv venv create $(VENV_NAME) --python=$(PYTHON_VERSION); \
	else \
		echo "$(BLUE)Using venv to create virtual environment...$(RESET)"; \
		$(PYTHON) -m venv $(VENV_NAME); \
	fi
	@echo "$(GREEN)Virtual environment created.$(RESET)"
	@echo "$(BLUE)Upgrading pip in virtual environment...$(RESET)"
	@$(VENV_PYTHON) -m pip install --upgrade pip
	@echo "$(GREEN)Virtual environment ready to use.$(RESET)"
	@echo "Run '$(ACTIVATE_CMD) $(VENV_ACTIVATE)' to activate it."

# Helper to check for virtual environment
venv-check:
	@if [ ! -f $(VENV_ACTIVATE) ]; then \
		echo "$(YELLOW)Virtual environment not found. Creating one...$(RESET)" ; \
		$(MAKE) venv ; \
	fi

# Installation targets
install: venv-check
	@echo "$(YELLOW)Installing package...$(RESET)"
	@if [ -n "$(UV)" ]; then \
		echo "$(BLUE)Using uv for installation...$(RESET)"; \
		uv pip install -e "."; \
	else \
		echo "$(BLUE)Using pip for installation...$(RESET)"; \
		$(VENV_PYTHON) -m pip install -e .; \
	fi
	@echo "$(GREEN)Installation complete.$(RESET)"

install-dev: venv-check
	@echo "$(YELLOW)Installing development dependencies...$(RESET)"
	@if [ -n "$(UV)" ]; then \
		echo "$(BLUE)Using uv for installation...$(RESET)"; \
		uv pip install -e ".[dev]"; \
	else \
		echo "$(BLUE)Using pip for installation...$(RESET)"; \
		$(VENV_PYTHON) -m pip install -e ".[dev]"; \
	fi
	@echo "$(GREEN)Development dependencies installed.$(RESET)"

install-all: venv-check
	@echo "$(YELLOW)Installing all dependencies...$(RESET)"
	@if [ -n "$(UV)" ]; then \
		echo "$(BLUE)Using uv for installation...$(RESET)"; \
		uv pip install -e ".[dev,mcp,all]"; \
	else \
		echo "$(BLUE)Using pip for installation...$(RESET)"; \
		$(VENV_PYTHON) -m pip install -e ".[dev,mcp,all]"; \
	fi
	@echo "$(GREEN)All dependencies installed.$(RESET)"

uninstall: venv-check
	@echo "$(YELLOW)Uninstalling package...$(RESET)"
	$(VENV_PYTHON) -m pip uninstall -y hanzo-aci
	@echo "$(GREEN)Uninstallation complete.$(RESET)"

reinstall: uninstall install
	@echo "$(GREEN)Reinstallation complete.$(RESET)"

# Development targets
test: venv-check install-dev
	@echo "$(YELLOW)Running tests...$(RESET)"
	$(VENV_PYTHON) -m pytest $(TEST_DIR)
	@echo "$(GREEN)Tests complete.$(RESET)"

test-cov: venv-check install-dev
	@echo "$(YELLOW)Running tests with coverage...$(RESET)"
	$(VENV_PYTHON) -m pytest --cov=$(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)Tests with coverage complete.$(RESET)"

lint: venv-check install-dev
	@echo "$(YELLOW)Running linters...$(RESET)"
	$(VENV_PYTHON) -m ruff $(SRC_DIR) $(TEST_DIR) $(EXAMPLES_DIR)
	@echo "$(GREEN)Linting complete.$(RESET)"

format: venv-check install-dev
	@echo "$(YELLOW)Formatting code...$(RESET)"
	$(VENV_PYTHON) -m black $(SRC_DIR) $(TEST_DIR) $(EXAMPLES_DIR)
	@echo "$(GREEN)Formatting complete.$(RESET)"

# Build and packaging targets
build: clean venv-check install-dev
	@echo "$(YELLOW)Building package...$(RESET)"
	$(VENV_PYTHON) -m build
	@echo "$(GREEN)Build complete. Distribution files are in 'dist/'$(RESET)"

# Run targets
run: venv-check
	@echo "$(YELLOW)Running the CLI...$(RESET)"
	$(VENV_PYTHON) -m $(SRC_DIR).cli
	@echo "$(GREEN)CLI execution complete.$(RESET)"

example: venv-check
	@echo "$(YELLOW)Running the example...$(RESET)"
	$(VENV_PYTHON) $(EXAMPLES_DIR)/getting_started.py
	@echo "$(GREEN)Example execution complete.$(RESET)"

basic: venv-check
	@echo "$(YELLOW)Running the basic usage example...$(RESET)"
	$(VENV_PYTHON) $(EXAMPLES_DIR)/basic_usage.py
	@echo "$(GREEN)Basic usage example execution complete.$(RESET)"

integration: venv-check
	@echo "$(YELLOW)Running the integration example...$(RESET)"
	$(VENV_PYTHON) $(EXAMPLES_DIR)/integration_example.py --mode demo
	@echo "$(GREEN)Integration example execution complete.$(RESET)"

# Utility targets
clean:
	@echo "$(YELLOW)Cleaning build artifacts...$(RESET)"
	$(RM_CMD) build/ dist/ *.egg-info/ .pytest_cache/ htmlcov/ .coverage 2>/dev/null || true
ifeq ($(OS),Windows_NT)
	for /d /r . %d in (__pycache__) do @if exist "%d" rd /s /q "%d"
else
	find . -name "__pycache__" -type d -exec rm -rf {} +
endif
	@echo "$(GREEN)Cleaning complete.$(RESET)"

# Help target
help:
	@echo "$(BLUE)Usage: make [target]$(RESET)"
	@echo "Targets:"
	@echo "  $(GREEN)all$(RESET)                 - Install dependencies, run tests"
	@echo "  $(GREEN)install$(RESET)             - Install package in development mode"
	@echo "  $(GREEN)install-dev$(RESET)         - Install package with development dependencies"
	@echo "  $(GREEN)install-all$(RESET)         - Install package with all dependencies"
	@echo "  $(GREEN)uninstall$(RESET)           - Uninstall the package"
	@echo "  $(GREEN)reinstall$(RESET)           - Uninstall and reinstall the package"
	@echo "  $(GREEN)test$(RESET)                - Run tests"
	@echo "  $(GREEN)test-cov$(RESET)            - Run tests with coverage"
	@echo "  $(GREEN)lint$(RESET)                - Run linting"
	@echo "  $(GREEN)format$(RESET)              - Format code"
	@echo "  $(GREEN)build$(RESET)               - Build package"
	@echo "  $(GREEN)run$(RESET)                 - Run the CLI"
	@echo "  $(GREEN)example$(RESET)             - Run the getting started example"
	@echo "  $(GREEN)basic$(RESET)               - Run the basic usage example"
	@echo "  $(GREEN)integration$(RESET)         - Run the integration example"
	@echo "  $(GREEN)clean$(RESET)               - Clean build artifacts"
	@echo "  $(GREEN)venv$(RESET)                - Create virtual environment"
	@echo "  $(GREEN)check-dependencies$(RESET)  - Check system dependencies"
	@echo "  $(GREEN)check-python$(RESET)        - Check Python installation"
	@echo "  $(GREEN)check-uv$(RESET)            - Check uv installation"
	@echo "  $(GREEN)help$(RESET)                - Show this help message"
