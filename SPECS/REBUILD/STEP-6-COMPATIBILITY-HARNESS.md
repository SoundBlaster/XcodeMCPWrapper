# STEP 6 — COMPATIBILITY HARNESS & MIGRATION (Prove Parity)
+++Tone(style=formal)
+++Reasoning
+++Debate
+++OutputFormat(type=json)

INPUT (required):
{
  "behavior_matrix": "<from step 2>",
  "spec_summary": "<from step 3>",
  "workplan_task_graph": "<from step 5>"
}

OUTPUT (required):
{
  "step": "6",
  "file": {
    "path": "FEATURE_REBUILD/CompatibilityHarness.md",
    "content_md": "Compatibility harness doc"
  },
  "harness": {
    "goldens": ["<fixtures/snapshots/contracts>"],
    "parity_checks": ["<what exactly we compare>"],
    "automation": ["<where in CI, which commands>"]
  },
  "migration_plan": {
    "approach":"stacked-prs|single-pr|feature-flag",
    "rollback_strategy":"...",
    "release_notes":"..."
  },
  "assumptions": ["..."]
}

CompatibilityHarness.md REQUIRED STRUCTURE:
- Title
- What Must Match (MUST list)
- What May Change (MAY list)
- Golden Sources (tests/fixtures/snapshots/logs)
- Parity Check Plan (how we compare)
- CI Integration
- Rollback Strategy
