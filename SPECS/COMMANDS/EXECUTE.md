# EXECUTE — Task Execution Wrapper

**Version:** 1.0.0

## Purpose

EXECUTE is a lightweight workflow wrapper for the Python-based mcpbridge-wrapper project. It ensures the environment is ready, shows the PLAN PRD, lets you execute the implementation, and then validates/tests before committing.

## Inputs

- `SPECS/INPROGRESS/{TASK_ID}_{TASK_NAME}.md` produced by PLAN.
- `SPECS/INPROGRESS/next.md` to know the chosen task.

## Steps

1. **Pre-flight checks**
   - Confirm the working tree is clean: `git status -sb` (if not, remind to commit or stash other work).
   - Verify Python toolchain: `python3 --version` (requires 3.7+).
   - Print the PRD summary and key acceptance criteria from the `SPECS/INPROGRESS` doc so you know the story.

2. **Work period**
   - Assume the role defined in [`SPECS/ROLES/TDD_Executor_xml.md`](../ROLES/TDD_Executor_xml.md) — Outside-In XP / TDD Engineering Agent.
   - Start by writing or updating tests before making implementation changes.
   - Follow the step-by-step tasks in the PRD. This is when you edit files, run tests, etc.
   - Use the PRD task plan for your commits (one commit per major change is ideal).

3. **REQUIRED Post-flight validation**
   - Run `make test` or `pytest` to ensure all tests pass
   - Run `make lint` or `ruff check src/` for code quality
   - Run `make typecheck` or `mypy src/` for type checking (if configured)
   - Check test coverage: `pytest --cov=src/mcpbridge_wrapper --cov-report=term-missing`

4. **Refactor structure pass (if needed)**
   - Apply [`SPECS/COMMANDS/PRIMITIVES/REFACTORING.md`](./PRIMITIVES/REFACTORING.md) to split mixed changes into focused files before final commit.
   - Re-run validation after refactoring.

5. **Finalize**
   - Stage relevant files and commit per [`SPECS/COMMANDS/PRIMITIVES/COMMIT.md`](./PRIMITIVES/COMMIT.md).
   - Optionally update `SPECS/INPROGRESS/next.md` if metadata (priority, status) changed.
   - Suggest next task from `SPECS/Workplan.md` (SELECT will capture it later).

## Quality Gate Commands

### Using Makefile (when available)

```bash
# Run all quality checks
make quality-gate

# Individual targets
make test           # Run pytest with coverage
make lint           # Run ruff linting
make format         # Run ruff formatting
make typecheck      # Run mypy type checking
make install        # Install package in editable mode
make clean          # Clean build artifacts
```

### Direct Commands

```bash
# Testing
pytest                              # Run all tests
pytest -v                           # Verbose output
pytest --cov=src/mcpbridge_wrapper  # With coverage
pytest tests/unit/                  # Unit tests only
pytest tests/integration/           # Integration tests only

# Linting and formatting
ruff check src/                     # Check code style
ruff format src/                    # Format code
ruff check --fix src/               # Auto-fix issues

# Type checking
mypy src/mcpbridge_wrapper          # Check types

# Manual integration test
./src/mcpbridge_wrapper/cli.py --help  # Test CLI
```

## Project Structure

```
/
├── src/
│   └── mcpbridge_wrapper/      # Main package
│       ├── __init__.py
│       ├── __main__.py         # Entry point
│       ├── bridge.py           # Subprocess bridge
│       └── transform.py        # Response transformation
├── tests/
│   ├── unit/                   # Unit tests
│   └── integration/            # Integration tests
├── scripts/                    # Helper scripts
│   ├── pick_next_task.py
│   └── calc_progress.py
├── SPECS/
│   ├── Workplan.md             # Task tracker (this project)
│   ├── INPROGRESS/             # Active tasks
│   └── COMMANDS/               # This folder
├── pyproject.toml              # Project configuration
└── Makefile                    # Build automation
```

## Quality Gate Checklist

Before committing, ensure:
- [ ] `pytest` passes (all tests)
- [ ] `ruff check src/` passes (no linting errors)
- [ ] Code coverage remains ≥90% for modified files
- [ ] No regressions in existing tests

## Notes

- EXECUTE does not invent steps; it only organizes pre/post validations around the PRD.
- Python 3.7+ is required (standard on macOS 10.15+)
- The wrapper operates as a stdin/stdout bridge - test manually with echo commands
- When the task is complete, mark the PRD ready for ARCHIVE.
