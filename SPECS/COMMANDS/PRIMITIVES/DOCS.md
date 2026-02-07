---
name: "docs"
description: "Use when updating project documentation, README, or docstrings."
---

# DOCS — Documentation Updates

**Version:** 1.0.0

## Purpose

Update project documentation, docstrings, and README files for the mcpbridge-wrapper project.

## Documentation Types

### Code Documentation

- Add docstrings to all public functions and classes
- Follow Google-style docstring format:

```python
def process_response(line: str) -> str:
    """Process a single response line from mcpbridge.
    
    Args:
        line: Raw JSON line from bridge stdout.
        
    Returns:
        Processed JSON line with structuredContent injected.
    """
```

### Project Documentation

- Update `README.md` for user-facing changes
- Update `AGENTS.md` for agent-specific context
- Update `SPECS/` documentation for design decisions

### Configuration Documentation

- Document config options in code
- Update example configuration files
- Keep Cursor/Claude/Codex setup instructions current

## Checklist

- [ ] Docstrings added/updated for modified functions
- [ ] README updated if behavior changes
- [ ] AGENTS.md updated if agent workflow changes
- [ ] Configuration examples remain valid
