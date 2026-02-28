# Makefile for mcpbridge-wrapper

.PHONY: help install install-webui test test-webui lint format format-check typecheck doccheck doccheck-staged doccheck-branch doccheck-all doccheck-all-strict package-assets-check bump-version badge-version badge-version-check clean webui webui-restart webui-health check

help:
	@echo "Available targets:"
	@echo "  install        - Install package in editable mode"
	@echo "  install-webui  - Install package with Web UI dependencies"
	@echo "  test           - Run pytest with coverage"
	@echo "  test-webui     - Run Web UI specific tests"
	@echo "  lint           - Run ruff linter"
	@echo "  format         - Run ruff formatter"
	@echo "  format-check   - Run ruff formatter in check mode"
	@echo "  typecheck      - Run mypy type checker"
	@echo "  doccheck       - Check docs/ are synced with DocC catalog"
	@echo "  doccheck-staged - Check staged docs/ sync with DocC catalog"
	@echo "  doccheck-branch - Check docs/ sync against git branch"
	@echo "  doccheck-all   - Check docs/ sync for unstaged, staged, and branch changes"
	@echo "  doccheck-all-strict - Same as doccheck-all + require doc/docc updates in same commit on branch scope"
	@echo "  package-assets-check - Build artifacts and verify required packaged assets"
	@echo "  bump-version   - Update pyproject.toml and server.json versions (VERSION=x.y.z, add DRY_RUN=1 to preview)"
	@echo "  badge-version  - Update README version badge (latest tag or TAG=vX.Y.Z; add DRY_RUN=1 to preview)"
	@echo "  badge-version-check - Fail if README version badge does not match latest tag"
	@echo "  webui          - Start wrapper with Web UI dashboard (port 8080)"
	@echo "  webui-restart  - Restart Web UI dashboard on chosen port (PORT=8080 by default)"
	@echo "  webui-health   - Check Web UI health status"
	@echo "  clean          - Clean build artifacts"
	@echo "  check          - Run all quality gates (test, lint, format, typecheck, doccheck-all, package-assets-check)"

install:
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "⚠️  No active virtual environment detected."; \
		echo "   If pip fails with externally-managed-environment (PEP 668), run:"; \
		echo "   python3 -m venv .venv && source .venv/bin/activate"; \
	fi
	python3 -m pip install -e .

install-webui:
	@if [ -z "$$VIRTUAL_ENV" ]; then \
		echo "⚠️  No active virtual environment detected."; \
		echo "   If pip fails with externally-managed-environment (PEP 668), run:"; \
		echo "   python3 -m venv .venv && source .venv/bin/activate"; \
	fi
	python3 -m pip install -e ".[webui]"

test:
	pytest tests/ -v --cov=src --cov-report=xml --cov-report=term

test-webui:
	pytest tests/unit/webui/ tests/integration/webui/ -v --cov=src/mcpbridge_wrapper/webui --cov-report=term-missing

lint:
	python -m ruff check src/ tests/

format:
	python -m ruff format src/ tests/

format-check:
	python -m ruff format --check src/ tests/

typecheck:
	mypy src/

doccheck:
	python scripts/check_doc_sync.py

doccheck-staged:
	python scripts/check_doc_sync.py --staged

doccheck-branch:
	python scripts/check_doc_sync.py --branch

doccheck-all:
	python scripts/check_doc_sync.py --all

doccheck-all-strict:
	python scripts/check_doc_sync.py --all --require-same-commit

package-assets-check:
	python -m build --sdist --wheel
	python scripts/check_package_assets.py --dist-dir dist

bump-version:
	@if [ -z "$(VERSION)" ]; then \
		echo "Usage: make bump-version VERSION=x.y.z [DRY_RUN=1]"; \
		exit 1; \
	fi
	@if [ -n "$(DRY_RUN)" ]; then \
		python scripts/publish_helper.py $(VERSION) --dry-run; \
	else \
		python scripts/publish_helper.py $(VERSION); \
	fi

badge-version:
	@if [ -n "$(TAG)" ]; then \
		if [ -n "$(DRY_RUN)" ]; then \
			python scripts/update_version_badge.py --tag "$(TAG)" --dry-run; \
		else \
			python scripts/update_version_badge.py --tag "$(TAG)"; \
		fi; \
	else \
		if [ -n "$(DRY_RUN)" ]; then \
			python scripts/update_version_badge.py --dry-run; \
		else \
			python scripts/update_version_badge.py; \
		fi; \
	fi

badge-version-check:
	python scripts/update_version_badge.py --check

check: test lint format-check typecheck doccheck-all package-assets-check

clean:
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

webui:
	@echo "Starting MCP Wrapper with Web UI on http://127.0.0.1:8080"
	@echo "Press Ctrl+C to stop"
	python -m mcpbridge_wrapper --web-ui --web-ui-port 8080

webui-restart:
	@PORT_VALUE=$${PORT:-8080}; \
	echo "Restarting Web UI on http://127.0.0.1:$$PORT_VALUE"; \
	python -m mcpbridge_wrapper --web-ui-only --web-ui-restart --web-ui-port "$$PORT_VALUE"

webui-health:
	@echo "Checking Web UI health..."
	@curl -s http://localhost:8080/api/health | python -m json.tool 2>/dev/null || echo "Web UI not accessible at http://localhost:8080"
	@echo ""
	@echo "Current metrics:"
	@curl -s http://localhost:8080/api/metrics 2>/dev/null | python -c "import sys, json; d=json.load(sys.stdin); print(f'  Uptime: {d[\"uptime_seconds\"]}s, Requests: {d[\"total_requests\"]}, RPS: {d[\"rps\"]}, Errors: {d[\"total_errors\"]}')" 2>/dev/null || echo "  (unable to fetch metrics)"
