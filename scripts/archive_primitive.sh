#!/usr/bin/env bash
set -euo pipefail

# archive_primitive.sh
# Minimal helper for archive workflow primitives.
# Agents MUST call `prepare-task` before moving task files.

usage() {
  cat <<'USAGE'
Usage:
  scripts/archive_primitive.sh prepare-task <TASK_ID> <TASK_NAME>
  scripts/archive_primitive.sh ensure-historical
  scripts/archive_primitive.sh archive-prd <PRD_PATH> <DATE> <VERDICT>

Commands:
  prepare-task      Create and print task archive folder path.
  ensure-historical Ensure SPECS/ARCHIVE/_Historical exists.
  archive-prd       Append archive metadata footer to a PRD markdown file.
USAGE
}

cmd_prepare_task() {
  local task_id="${1:-}"
  local task_name="${2:-}"

  if [[ -z "$task_id" || -z "$task_name" ]]; then
    echo "error: prepare-task requires <TASK_ID> <TASK_NAME>" >&2
    usage
    exit 2
  fi

  local dir="SPECS/ARCHIVE/${task_id}_${task_name}"
  mkdir -p "$dir"
  echo "$dir"
}

cmd_ensure_historical() {
  mkdir -p "SPECS/ARCHIVE/_Historical"
  echo "SPECS/ARCHIVE/_Historical"
}

cmd_archive_prd() {
  local prd_path="${1:-}"
  local date="${2:-}"
  local verdict="${3:-}"

  if [[ -z "$prd_path" || -z "$date" || -z "$verdict" ]]; then
    echo "error: archive-prd requires <PRD_PATH> <DATE> <VERDICT>" >&2
    usage
    exit 2
  fi

  if [[ ! -f "$prd_path" ]]; then
    echo "error: file not found: $prd_path" >&2
    exit 1
  fi

  {
    echo
    echo "---"
    echo "**Archived:** ${date}"
    echo "**Verdict:** ${verdict}"
  } >> "$prd_path"

  echo "$prd_path"
}

main() {
  local cmd="${1:-}"
  shift || true

  case "$cmd" in
    prepare-task)
      cmd_prepare_task "$@"
      ;;
    ensure-historical)
      cmd_ensure_historical "$@"
      ;;
    archive-prd)
      cmd_archive_prd "$@"
      ;;
    ""|-h|--help|help)
      usage
      ;;
    *)
      echo "error: unknown command: $cmd" >&2
      usage
      exit 2
      ;;
  esac
}

main "$@"
