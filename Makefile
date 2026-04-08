.PHONY: check-style fix-style check-type check-test check-all help run-sample01 run-sample02 run-sample03 run-samples

# Default target
help:
	@echo "Available commands:"
	@echo "  make setup-dev   	: setup core + dev tools + git hooks (for contributors)"
	@echo "  make fix-style     : Format code and fix lint errors automatically"
	@echo "  make check-style   : Verify code style and linting (read-only)"
	@echo "  make check-type    : Verify static types with Mypy"
	@echo "  make check-test    : Run unit tests with Pytest"
	@echo "  make check-all     : Run style, type and test checks"
	@echo "  make docker-build  : Build the docker image locally"
	@echo "  make docker-run    : Test the built image locally"
	@echo "  make run-sample01  : Execute sample01 pipeline"
	@echo "  make run-sample02  : Execute sample02 pipeline"
	@echo "  make run-sample03  : Execute sample03 pipeline"
	@echo "  make run-samples   : Execute samples (1 to 3) sequentially"

# --- Install  ---

# For contributor
setup-dev:
	pip install uv
	uv sync --all-groups
	uv run pre-commit install

# --- Quality & Tests ---

fix-style:
	uv run ruff format .
	uv run ruff check . --fix

check-style:
	uv run ruff format --check .
	uv run ruff check .

check-type:
	uv run mypy .

check-test:
	uv run pytest stairway_to_salesforce/tests/

check-all: check-style check-type check-test

# --- Pipelines Samples ---

run-sample01:
	uv run pipelines/sample01_upsert_accounts_csv_sf.py

run-sample02:
	uv run pipelines/sample02_upsert_contacts_csv_sf.py

run-sample03:
	uv run pipelines/sample03_delete_contacts_csv_sf.py

run-samples: run-sample01 run-sample02 run-sample03

# --- Docker ---

IMAGE_NAME = stairway-to-salesforce
# Extract the version from pyproject for tagging
VERSION := $(shell python -c "print([l.split('=')[1].strip().strip('\"').strip(\"'\") for l in open('pyproject.toml') if l.startswith('version')][0])")

docker-build: ## Build the docker image locally
	@echo "Building Docker image $(IMAGE_NAME):$(VERSION)..."
	docker build -t $(IMAGE_NAME):latest -t $(IMAGE_NAME):$(VERSION) .

docker-run: ## Run the local docker image to verify it works
	@echo "Running $(IMAGE_NAME):latest..."
	docker run --rm $(IMAGE_NAME):latest python --version
