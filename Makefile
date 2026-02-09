# Makefile for mcpbridge-wrapper

.PHONY: help install install-webui test test-webui lint format typecheck doccheck clean webui webui-health

help:
	@echo "Available targets:"
	@echo "  install        - Install package in editable mode"
	@echo "  install-webui  - Install package with Web UI dependencies"
	@echo "  test           - Run pytest with coverage"
	@echo "  test-webui     - Run Web UI specific tests"
	@echo "  lint           - Run ruff linter"
	@echo "  format         - Run ruff formatter"
	@echo "  typecheck      - Run mypy type checker"
	@echo "  doccheck       - Check docs/ are synced with DocC catalog"
	@echo "  webui          - Start wrapper with Web UI dashboard (port 8080)"
	@echo "  webui-health   - Check Web UI health status"
	@echo "  clean          - Clean build artifacts"
	@echo "  check          - Run all quality gates (test, lint, format, typecheck, doccheck)"

install:
	pip install -e .

install-webui:
	pip install -e ".[webui]"

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

test-webui:
	pytest tests/unit/webui/ tests/integration/webui/ -v --cov=src/mcpbridge_wrapper/webui --cov-report=term-missing

lint:
	ruff check src/

format:
	ruff format src/ tests/

typecheck:
	mypy src/

doccheck:
	python scripts/check_doc_sync.py

check: test lint format typecheck doccheck

clean:
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

webui:
	@echo "Starting MCP Wrapper with Web UI on http://127.0.0.1:8080"
	@echo "Press Ctrl+C to stop"
	python -m mcpbridge_wrapper --web-ui --web-ui-port 8080

webui-health:
	@echo "Checking Web UI health..."
	@curl -s http://localhost:8080/api/health | python -m json.tool 2>/dev/null || echo "Web UI not accessible at http://localhost:8080"
	@echo ""
	@echo "Current metrics:"
	@curl -s http://localhost:8080/api/metrics 2>/dev/null | python -c "import sys, json; d=json.load(sys.stdin); print(f'  Uptime: {d[\"uptime_seconds\"]}s, Requests: {d[\"total_requests\"]}, RPS: {d[\"rps\"]}, Errors: {d[\"total_errors\"]}')" 2>/dev/null || echo "  (unable to fetch metrics)"
