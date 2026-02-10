# STEP 5 — WORKPLAN (Phased Task Graph, Always-Green)
+++Tone(style=formal)
+++Reasoning
+++OutputFormat(type=json)

INPUT (required):
{
  "spec_file": "<from step 3>",
  "architecture_file": "<from step 4>",
  "verification_commands": ["<repo-accurate commands or best-guess with labels>"]
}

OUTPUT (required):
{
  "step": "5",
  "file": {
    "path": "FEATURE_REBUILD/Workplan.md",
    "content_md": "Workplan doc"
  },
  "task_graph": {
    "phases": [
      {
        "phase_id":"PH-1",
        "title":"...",
        "tasks":[
          {
            "id":"T-001",
            "title":"...",
            "priority":"P0|P1|P2",
            "deps":["T-..."],
            "parallelizable_with":["T-..."],
            "touched_files":["..."],
            "acceptance_criteria":["..."],
            "verification_commands":["..."],
            "rollback":"..."
          }
        ]
      }
    ]
  },
  "assumptions": ["..."],
  "risks": ["..."]
}

Workplan.md REQUIRED STRUCTURE:
- Title
- Assumptions
- Phases Overview (table)
- Tasks (grouped by phase, each task as a mini-card)
- Acceptance Criteria (rolled up)
- Verification Commands
- Definition of Done
- Risks & Open Questions
