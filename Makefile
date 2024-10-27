# Define the package directory for zerox
PACKAGE_DIR := py_zerox

# Define directory configs
VENV_DIR := .venv
DIST_DIR := ${PACKAGE_DIR}/dist
SRC_DIR := $(PACKAGE_DIR)/zerox
TEST_DIR := $(PACKAGE_DIR)/tests

# Define the build configs
POETRY_VERSION := 1.8.3
PYTHON := python3  # Default to python3 for Docker compatibility
POETRY := poetry

# Test related configs
PYTEST_OPTIONS := -v

# Default target
.PHONY: all
all: venv build test dev

# Initialization
.PHONY: init
init:
	@echo "== Initializing Development Environment =="
	curl -sSL https://install.python-poetry.org | $(PYTHON) -

	@echo "== Installing Pre-Commit Hooks =="
	pre-commit install || true
	pre-commit autoupdate || true
	pre-commit install --install-hooks || true
	pre-commit install --hook-type commit-msg || true

# Create virtual environment if it doesn't exist
.PHONY: venv
venv: $(VENV_DIR)/bin/activate

$(VENV_DIR)/bin/activate:
	@echo "== Creating Virtual Environment =="
	$(PYTHON) -m venv $(VENV_DIR)
	. $(VENV_DIR)/bin/activate && pip install --upgrade pip setuptools wheel
	touch $(VENV_DIR)/bin/activate

# Resolving dependencies and build the package using SetupTools
.PHONY: build
build: venv
	@echo "== Resolving dependencies and building the package using SetupTools =="
	$(PYTHON) setup.py sdist --dist-dir $(DIST_DIR)

# Install test dependencies for test environment
.PHONY: install-test
install-test: venv
	@echo "== Resolving test dependencies =="
	$(POETRY) install --with test

# Test out the build
.PHONY: test
test: install-test
	@echo "== Triggering tests =="
	pytest $(TEST_DIR) $(PYTEST_OPTIONS) || (echo "Tests failed" && exit 1)

# Clean build artifacts
.PHONY: clean
clean:
	@echo "== Cleaning DIST_DIR and VENV_DIR =="
	rm -rf $(DIST_DIR)
	rm -rf $(VENV_DIR)

# Install dev dependencies for dev environment
.PHONY: install-dev
install-dev: venv build
	@echo "== Resolving development dependencies =="
	$(POETRY) install --with dev

# Package Development Build
.PHONY: dev
dev:
	@echo "== Preparing development build =="
	$(POETRY) install
	$(POETRY) run pip install -e .

# Run lint and format checks
.PHONY: check
check: install-dev lint format

# Lint the codebase
.PHONY: lint
lint: venv
	@echo "== Running Linting =="
	$(VENV_DIR)/bin/ruff check $(SRC_DIR) $(TEST_DIR)

# Check code formatting
.PHONY: format
format: venv
	@echo "== Running Formatting Check =="
	$(VENV_DIR)/bin/black --check $(SRC_DIR) $(TEST_DIR)

# Fix linting and formatting issues
.PHONY: fix
fix: install-dev lint-fix format-fix

# Fix linting issues
.PHONY: lint-fix
lint-fix: venv
	@echo "== Fixing Linting Issues =="
	$(VENV_DIR)/bin/ruff check --fix $(SRC_DIR) $(TEST_DIR)

# Fix formatting issues
.PHONY: format-fix
format-fix: venv
	@echo "== Fixing Formatting Issues =="
	$(VENV_DIR)/bin/black $(SRC_DIR) $(TEST_DIR)
