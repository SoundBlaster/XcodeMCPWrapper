# STEP 3 — SPEC DRAFT (Implementation-Agnostic)
+++Tone(style=formal)
+++Reasoning
+++OutputFormat(type=json)

INPUT (required):
{
  "behavior_matrix": "<from step 2>",
  "compatibility_contracts": "<from step 2>",
  "known_bugs": "<from step 2>"
}

OUTPUT (required):
{
  "step": "3",
  "file": {
    "path": "FEATURE_REBUILD/Spec.md",
    "content_md": "Markdown spec with stable headings (see structure below)"
  },
  "spec_summary": {
    "scope": ["..."],
    "must_keep": ["..."],
    "may_change": ["..."],
    "bug_fixes_included": ["BUG-..."]
  },
  "assumptions": ["..."],
  "open_questions": ["..."]
}

SPEC.md REQUIRED STRUCTURE (must match):
- Title
- Assumptions
- Glossary
- Goals / Non-Goals
- Functional Requirements (FR) — numbered
- Non-Functional Requirements (NFR)
- State Model & Invariants (or “N/A”)
- Persistence & Caching Rules (or “N/A”)
- API Contracts (Types / Inputs / Outputs / Errors)
- Observability (Logs/Metrics/Events)
- Compatibility Rules (MUST / MAY)
- Bug Fixes (what changes, why, and expected behavior)
- Acceptance Criteria (high-level)
