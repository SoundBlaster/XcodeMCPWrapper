# Makefile for mcpbridge-wrapper

.PHONY: help install test lint format typecheck clean

help:
	@echo "Available targets:"
	@echo "  install    - Install package in editable mode"
	@echo "  test       - Run pytest with coverage"
	@echo "  lint       - Run ruff linter"
	@echo "  format     - Run ruff formatter"
	@echo "  typecheck  - Run mypy type checker"
	@echo "  clean      - Clean build artifacts"

install:
	pip install -e .

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

lint:
	ruff check src/

format:
	ruff format src/ tests/

typecheck:
	mypy src/

clean:
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
