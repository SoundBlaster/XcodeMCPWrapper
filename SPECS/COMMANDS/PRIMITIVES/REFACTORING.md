---
name: "refactoring"
description: "Use when code needs restructuring for clarity, maintainability, or separation of concerns."
---

# REFACTORING — Code Restructuring Guide

**Version:** 1.0.0

## Purpose

Guide for refactoring Python code in the mcpbridge-wrapper project while maintaining functionality and test coverage.

## When to Refactor

- Functions exceed 50 lines
- Multiple responsibilities in one module
- Duplicate code patterns
- Poor naming conventions
- Circular import risks

## Guidelines

### Function Extraction

- Extract helper functions for complex logic
- Keep functions focused on single responsibility
- Use descriptive names with verb prefixes

### Module Organization

```
src/mcpbridge_wrapper/
├── __init__.py          # Package exports
├── __main__.py          # CLI entry point
├── bridge.py            # Subprocess bridge logic
├── transform.py         # Response transformation
└── utils.py             # Shared utilities (if needed)
```

### Testing During Refactor

1. Ensure tests pass before refactoring
2. Make incremental changes
3. Run tests after each change
4. Maintain ≥90% coverage

### Python-Specific Patterns

- Use type hints for function signatures
- Prefer dataclasses for structured data
- Use context managers (with statements) for resource management
- Follow PEP 8 naming conventions
- Use f-strings for string formatting

## Verification

After refactoring:
```bash
pytest                  # All tests pass
ruff check src/         # No linting errors
pytest --cov           # Coverage maintained
```
