# P6-T9: Create Uninstall Script

## Overview

Create an uninstall script that cleanly removes mcpbridge-wrapper from the system, reversing the actions performed by `scripts/install.sh`.

## References

- Installation script: `scripts/install.sh`
- Installs to: `~/bin/mcpbridge-wrapper`
- pip package: `mcpbridge-wrapper`

## Deliverables

1. `scripts/uninstall.sh` - Executable uninstall script

## Acceptance Criteria

- [ ] Running `scripts/uninstall.sh` removes `~/bin/mcpbridge-wrapper` if it exists
- [ ] Running `scripts/uninstall.sh` runs `pip uninstall mcpbridge-wrapper -y`
- [ ] Script has `--dry-run` mode that shows what would be removed without removing
- [ ] Script has confirmation prompt before removing (can be bypassed with `--yes`)
- [ ] Script detects if installation exists before attempting removal
- [ ] Script provides helpful error messages if removal fails
- [ ] Script exits with code 0 on success, non-zero on failure

## Implementation Notes

### What install.sh does (to reverse):
1. Creates `~/bin/` if not exists
2. Installs pip package with `pip3 install -e .`
3. Creates `~/bin/mcpbridge-wrapper` launcher script
4. Makes it executable

### Uninstall script should:
1. Check if `~/bin/mcpbridge-wrapper` exists
2. Optionally remove the pip package (ask user or require --yes)
3. Remove the launcher script from `~/bin/`
4. Optionally clean up pip cache

### Script Options:
- `--dry-run` / `-n`: Show what would be removed
- `--yes` / `-y`: Skip confirmation prompts
- `--help` / `-h`: Show usage

## Verification Steps

1. Run install.sh to install
2. Run uninstall.sh --dry-run to verify it detects installation
3. Run uninstall.sh --yes to remove
4. Verify ~/bin/mcpbridge-wrapper is gone
5. Verify pip list | grep mcpbridge-wrapper returns nothing
