# P6-T3: Create Installation Script

## Overview

Create shell script that installs to `~/bin/mcpbridge-wrapper`.

## Implementation

Created `scripts/install.sh`:
- Checks Python version (3.7+)
- Creates ~/bin directory
- Installs package with pip
- Creates wrapper script
- Provides configuration hints

## Usage

```bash
./scripts/install.sh
```

## Acceptance Criteria

- [x] Running `scripts/install.sh` creates `~/bin/mcpbridge-wrapper`
- [x] Script is executable

---
**Archived:** 2026-02-08
**Verdict:** PASS
