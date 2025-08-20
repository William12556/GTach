# GTach Project Makefile
# Comprehensive build, test, and release automation system
# 
# Created: 2025-08-17
# Protocol: Protocol 13 Release Management Standards
# Integration: Protocol 5 GitHub Desktop Workflow

.PHONY: help clean install test lint typecheck build package release-prompt release-auto release-manual deploy
.DEFAULT_GOAL := help

# Project configuration
PROJECT_NAME := gtach
SRC_DIR := src
TEST_DIR := $(SRC_DIR)/tests
SCRIPTS_DIR := $(SRC_DIR)/scripts
PACKAGES_DIR := packages
PYTHON := python3
PIP := pip3

# Version detection - direct from pyproject.toml
VERSION := $(shell grep -E '^version\s*=' pyproject.toml | sed -E 's/.*["\x27]([^"\x27]*)["\x27].*/\1/' 2>/dev/null || echo "unknown")

# Colors for output
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

help: ## Display this help message
	@echo "$(BLUE)GTach Project Makefile$(RESET)"
	@echo "$(BLUE)Current Version: $(VERSION)$(RESET)"
	@echo ""
	@echo "$(YELLOW)Available targets:$(RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)Release Workflow:$(RESET)"
	@echo "  1. $(GREEN)make package$(RESET)       - Create distribution packages"
	@echo "  2. $(GREEN)make release-prompt$(RESET) - Interactive release creation"
	@echo "  3. $(GREEN)make release-auto$(RESET)   - Automated release creation"
	@echo "  OR $(GREEN)make release-manual$(RESET)  - Standalone release creation"

clean: ## Remove build artifacts and temporary files
	@echo "$(BLUE)Cleaning build artifacts...$(RESET)"
	@rm -rf build/
	@rm -rf dist/
	@rm -rf *.egg-info/
	@rm -rf $(SRC_DIR)/*.egg-info/
	@rm -rf .pytest_cache/
	@rm -rf .coverage
	@rm -rf htmlcov/
	@rm -rf .mypy_cache/
	@find . -type d -name __pycache__ -delete
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@echo "$(GREEN)Clean completed$(RESET)"

install: ## Install project dependencies
	@echo "$(BLUE)Installing dependencies...$(RESET)"
	@$(PIP) install -e .[dev]
	@echo "$(GREEN)Dependencies installed$(RESET)"

install-dev: ## Install development dependencies only
	@echo "$(BLUE)Installing development dependencies...$(RESET)"
	@$(PIP) install -e .[dev]
	@echo "$(GREEN)Development dependencies installed$(RESET)"

test: ## Run test suite with coverage
	@echo "$(BLUE)Running test suite...$(RESET)"
	@cd $(SRC_DIR) && $(PYTHON) -m pytest -v --cov=$(SRC_DIR) --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)Tests completed$(RESET)"

test-quick: ## Run tests without coverage
	@echo "$(BLUE)Running quick tests...$(RESET)"
	@cd $(SRC_DIR) && $(PYTHON) -m pytest -v
	@echo "$(GREEN)Quick tests completed$(RESET)"

lint: ## Run code linting
	@echo "$(BLUE)Running linting...$(RESET)"
	@$(PYTHON) -m black --check $(SRC_DIR)
	@$(PYTHON) -m isort --check-only $(SRC_DIR)
	@$(PYTHON) -m flake8 $(SRC_DIR)
	@echo "$(GREEN)Linting passed$(RESET)"

lint-fix: ## Fix linting issues automatically
	@echo "$(BLUE)Fixing linting issues...$(RESET)"
	@$(PYTHON) -m black $(SRC_DIR)
	@$(PYTHON) -m isort $(SRC_DIR)
	@echo "$(GREEN)Linting fixes applied$(RESET)"

typecheck: ## Run type checking
	@echo "$(BLUE)Running type checking...$(RESET)"
	@$(PYTHON) -m mypy $(SRC_DIR)
	@echo "$(GREEN)Type checking passed$(RESET)"

validate: clean lint typecheck test ## Run all validation checks
	@echo "$(GREEN)All validation checks passed$(RESET)"

build: clean ## Build distribution packages
	@echo "$(BLUE)Building distribution packages...$(RESET)"
	@$(PYTHON) -m build
	@echo "$(GREEN)Build completed$(RESET)"

# Package creation target (existing workflow integration)
package: validate build ## Create deployment package with validation
	@echo "$(BLUE)Creating deployment package...$(RESET)"
	@mkdir -p $(PACKAGES_DIR)
	@if [ -d "dist" ]; then \
		cp dist/*.tar.gz $(PACKAGES_DIR)/ 2>/dev/null || true; \
		cp dist/*.whl $(PACKAGES_DIR)/ 2>/dev/null || true; \
	fi
	@echo "$(GREEN)Package created in $(PACKAGES_DIR)/$(RESET)"
	@ls -la $(PACKAGES_DIR)/

# Release automation targets
release-check: ## Validate release prerequisites
	@echo "$(BLUE)Validating release prerequisites...$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/create_release.py --debug 2>/dev/null || \
		(echo "$(RED)Release validation failed. Ensure:$(RESET)"; \
		 echo "  - GitHub CLI is installed and authenticated"; \
		 echo "  - Repository is on main branch with no uncommitted changes"; \
		 echo "  - Release assets exist in $(PACKAGES_DIR)/"; \
		 exit 1)
	@echo "$(GREEN)Release prerequisites validated$(RESET)"

release-prompt: package release-check ## Interactive release creation after package build
	@echo "$(BLUE)Starting interactive release creation...$(RESET)"
	@echo "$(YELLOW)Package created for version: $(VERSION)$(RESET)"
	@echo "$(YELLOW)Assets available in $(PACKAGES_DIR)/$(RESET)"
	@ls -la $(PACKAGES_DIR)/
	@echo ""
	@read -p "Create GitHub release for version $(VERSION)? [y/N]: " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		echo "$(BLUE)Creating release...$(RESET)"; \
		$(PYTHON) $(SCRIPTS_DIR)/create_release.py --auto-confirm; \
		echo "$(GREEN)Release creation completed$(RESET)"; \
	else \
		echo "$(YELLOW)Release creation cancelled$(RESET)"; \
		echo "$(YELLOW)To create release later, run: make release-manual$(RESET)"; \
	fi

release-auto: package release-check ## Automated release creation after package build
	@echo "$(BLUE)Creating automated release for version: $(VERSION)$(RESET)"
	@$(PYTHON) $(SCRIPTS_DIR)/create_release.py --auto-confirm
	@echo "$(GREEN)Automated release creation completed$(RESET)"

release-manual: release-check ## Standalone release creation (assumes packages exist)
	@echo "$(BLUE)Creating standalone release for version: $(VERSION)$(RESET)"
	@if [ ! -d "$(PACKAGES_DIR)" ] || [ -z "$$(ls -A $(PACKAGES_DIR) 2>/dev/null)" ]; then \
		echo "$(RED)No packages found. Run 'make package' first.$(RESET)"; \
		exit 1; \
	fi
	@$(PYTHON) $(SCRIPTS_DIR)/create_release.py
	@echo "$(GREEN)Manual release creation completed$(RESET)"

# Development workflow targets
dev-setup: clean install ## Complete development environment setup
	@echo "$(BLUE)Setting up development environment...$(RESET)"
	@echo "$(GREEN)Development environment ready$(RESET)"
	@echo "$(YELLOW)Next steps:$(RESET)"
	@echo "  - $(GREEN)make test$(RESET) to run tests"
	@echo "  - $(GREEN)make package$(RESET) to create packages"
	@echo "  - $(GREEN)make release-prompt$(RESET) for interactive release"

dev-test: lint-fix test ## Quick development testing cycle
	@echo "$(GREEN)Development testing cycle completed$(RESET)"

# Deployment target (existing workflow integration)
deploy: package ## Deploy to Raspberry Pi (requires SCP configuration)
	@echo "$(BLUE)Deploying to Raspberry Pi...$(RESET)"
	@if [ -z "$(PI_HOST)" ]; then \
		echo "$(RED)PI_HOST environment variable not set$(RESET)"; \
		echo "$(YELLOW)Set PI_HOST=pi@your-pi-ip and try again$(RESET)"; \
		exit 1; \
	fi
	@scp $(PACKAGES_DIR)/*.tar.gz $(PI_HOST):~/
	@echo "$(GREEN)Deployment completed$(RESET)"

# Debug and maintenance targets
debug-version: ## Display version information
	@echo "$(BLUE)Version Information:$(RESET)"
	@echo "  Project Version: $(VERSION)"
	@echo "  Python Version: $$($(PYTHON) --version)"
	@echo "  Pip Version: $$($(PIP) --version)"
	@echo "  Git Branch: $$(git branch --show-current 2>/dev/null || echo 'N/A')"
	@echo "  Git Status: $$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ') changes"

debug-env: ## Display environment information
	@echo "$(BLUE)Environment Information:$(RESET)"
	@echo "  Operating System: $$(uname -s)"
	@echo "  Architecture: $$(uname -m)"
	@echo "  Working Directory: $$(pwd)"
	@echo "  Python Path: $$(which $(PYTHON))"
	@echo "  Project Structure:"
	@ls -la $(SRC_DIR)/ 2>/dev/null || echo "    $(SRC_DIR)/ not found"
	@ls -la $(PACKAGES_DIR)/ 2>/dev/null || echo "    $(PACKAGES_DIR)/ not found"

debug-scripts: ## Test release scripts without execution
	@echo "$(BLUE)Testing release scripts...$(RESET)"
	@$(PYTHON) -c "import sys; sys.path.append('$(SCRIPTS_DIR)'); import create_release, release_utils; print('Scripts import successfully')"
	@$(PYTHON) $(SCRIPTS_DIR)/create_release.py --help | head -5
	@echo "$(GREEN)Release scripts validated$(RESET)"

# CI/CD integration targets
ci-test: clean install test lint typecheck ## Complete CI validation pipeline
	@echo "$(GREEN)CI validation pipeline completed$(RESET)"

ci-build: clean install build ## CI build pipeline
	@echo "$(GREEN)CI build pipeline completed$(RESET)"

# Maintenance targets
update-deps: ## Update project dependencies
	@echo "$(BLUE)Updating dependencies...$(RESET)"
	@$(PIP) install --upgrade pip setuptools wheel
	@$(PIP) install --upgrade -e .[dev]
	@echo "$(GREEN)Dependencies updated$(RESET)"

check-deps: ## Check for dependency updates
	@echo "$(BLUE)Checking for dependency updates...$(RESET)"
	@$(PIP) list --outdated

# Safety and cleanup targets
emergency-clean: ## Emergency cleanup of all generated files
	@echo "$(YELLOW)Emergency cleanup - removing ALL generated files...$(RESET)"
	@rm -rf build/ dist/ *.egg-info/ $(SRC_DIR)/*.egg-info/ .pytest_cache/ .coverage htmlcov/ .mypy_cache/
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name "*.orig" -delete 2>/dev/null || true
	@find . -type f -name "*~" -delete 2>/dev/null || true
	@echo "$(GREEN)Emergency cleanup completed$(RESET)"