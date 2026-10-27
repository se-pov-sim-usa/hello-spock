# Local targets mirror the CI jobs in .github/workflows/ci.yml.
VENV ?= .venv
PY := $(VENV)/bin/python
IMAGE ?= hello-spock:local
GIT_SHA ?= $(shell git rev-parse HEAD 2>/dev/null || echo local)

.PHONY: help install lint format test security check run docker-build docker-run manifests ci clean

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-14s %s\n", $$1, $$2}'

$(VENV):
	python3 -m venv $(VENV)

install: $(VENV) ## Install dev dependencies and git hooks
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements-dev.txt
	-$(VENV)/bin/pre-commit install

lint: ## Lint and check formatting
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .

format: ## Auto-fix lint issues and format code
	$(VENV)/bin/ruff check --fix .
	$(VENV)/bin/ruff format .

test: ## Run tests with coverage gate
	$(VENV)/bin/pytest

security: ## Static security analysis and dependency audit
	$(VENV)/bin/bandit -c pyproject.toml -r greeting hello_spock
	$(VENV)/bin/pip-audit -r requirements.txt

check: ## Django deployment checks against production settings
	DJANGO_SECRET_KEY=$$($(PY) -c 'import secrets; print(secrets.token_urlsafe(50))') \
		$(PY) manage.py check --deploy --fail-level WARNING

run: ## Run the dev server on http://localhost:8000
	DJANGO_DEBUG=true $(PY) manage.py runserver 8000

docker-build: ## Build the linux/amd64 image
	docker build --platform linux/amd64 --build-arg GIT_SHA=$(GIT_SHA) -t $(IMAGE) .

docker-run: ## Run the image on http://localhost:8000
	docker run --rm -p 8000:8000 --read-only --tmpfs /tmp \
		-e DJANGO_SECRET_KEY=local-docker-secret -e DJANGO_SECURE_SSL_REDIRECT=false $(IMAGE)

manifests: ## Render and validate the Harness K8s manifests
	bash scripts/validate-manifests.sh

ci: lint security test check manifests ## Run the CI checks locally

clean: ## Remove caches and build output
	rm -rf .pytest_cache .ruff_cache .coverage coverage.xml junit.xml htmlcov staticfiles
	find . -type d -name __pycache__ -not -path './$(VENV)/*' -exec rm -rf {} +
