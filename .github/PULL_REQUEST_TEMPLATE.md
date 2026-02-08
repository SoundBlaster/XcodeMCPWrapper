## Description

Brief description of the changes in this PR.

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring
- [ ] CI/CD improvement

## Quality Gates

Before submitting, ensure all quality gates pass:

```bash
make check
```

Or run individually:
- [ ] `make test` - All tests pass with ≥90% coverage
- [ ] `make lint` - No linting errors
- [ ] `make format` - Code is properly formatted
- [ ] `make typecheck` - Type checking passes
- [ ] `make doccheck` - Documentation is synced with DocC (if docs changed)

## Documentation Sync

If you modified files in `docs/`, ensure corresponding DocC files are also updated:

| docs/ file | DocC file |
|------------|-----------|
| `docs/installation.md` | `mcpbridge-wrapper.docc/Installation.md` |
| `docs/cursor-setup.md` | `mcpbridge-wrapper.docc/CursorSetup.md` |
| `docs/claude-setup.md` | `mcpbridge-wrapper.docc/ClaudeCodeSetup.md` |
| `docs/codex-setup.md` | `mcpbridge-wrapper.docc/CodexCLISetup.md` |
| `docs/troubleshooting.md` | `mcpbridge-wrapper.docc/Troubleshooting.md` |
| `docs/architecture.md` | `mcpbridge-wrapper.docc/Architecture.md` |
| `docs/environment-variables.md` | `mcpbridge-wrapper.docc/EnvironmentVariables.md` |
| `README.md` | `mcpbridge-wrapper.docc/mcpbridge-wrapper.md` |

- [ ] Documentation changes are synced with DocC catalog (or N/A)

## Testing

- [ ] Added/updated tests for new functionality
- [ ] All tests pass locally
- [ ] Manually tested the changes

## Checklist

- [ ] Code follows the project's style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated (if needed)
- [ ] No new warnings generated
- [ ] PR title is descriptive
