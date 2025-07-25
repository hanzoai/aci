SHELL=/bin/bash

# Variables
PRE_COMMIT_CONFIG_PATH = "./dev_config/python/.pre-commit-config.yaml"

# ANSI color codes
GREEN=$(shell tput -Txterm setaf 2)
YELLOW=$(shell tput -Txterm setaf 3)
RED=$(shell tput -Txterm setaf 1)
BLUE=$(shell tput -Txterm setaf 6)
RESET=$(shell tput -Txterm sgr0)

install-pre-commit-hooks:
	@echo "$(YELLOW)Installing pre-commit hooks...$(RESET)"
	@git config --unset-all core.hooksPath || true
	@poetry run pre-commit install --config $(PRE_COMMIT_CONFIG_PATH)
	@echo "$(GREEN)Pre-commit hooks installed successfully.$(RESET)"

lint-python:
	@echo "$(YELLOW)Running linters...$(RESET)"
	@poetry run pre-commit run --files hanzo_aci/**/* tests/**/* --show-diff-on-failure --config $(PRE_COMMIT_CONFIG_PATH)

lint:
	@$(MAKE) -s lint-python
