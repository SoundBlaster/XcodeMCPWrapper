# REBUILD-WORKFLOW — Spec-Driven Rebuild (File/Lists Thinking)

<role>
You are an autonomous engineering agent executing a multi-step workflow.
You must think in terms of files, lists, matrices, and task graphs.
Each step has mandatory inputs and outputs. Do not skip steps.
</role>

<context>
We have an existing working feature in a source branch ("feature branch").
We will create a new branch ("rebuild branch") and rebuild the feature with improved architecture using SDD:
Evidence -> Spec -> Architecture -> Plan -> Migration/Parity.
</context>

<global_rules>
- Evidence-first: facts from code/tests/logs/issues > assumptions.
- No scope creep: only bug fixes, simplifications, maintainability improvements, and spec clarifications.
- Compatibility is a first-class constraint: preserve observable behavior unless explicitly changed in Spec (bug-fix section).
- Every architectural decision must reference a concrete pain point in the existing implementation.
- Outputs must be commit-ready artifacts (file contents), not vague prose.
</global_rules>

<workflow>

================================================================================
STEP 0 — SESSION SETUP (Branch + Paths)
+++Tone(style=formal)
+++Reasoning
+++OutputFormat(type=json)

INPUT (required):
{
  "repo_context": {
    "project_type": "ios|backend|cli|other",
    "default_branch": "<string or 'main'>",
    "feature_branch": "<string>",
    "rebuild_branch": "<string>",
    "ci_commands_hint": ["<optional commands like 'make test', 'swift test', 'xcodebuild ...'>"]
  },
  "paths": {
    "artifact_root": "FEATURE_REBUILD",
    "spec_path": "FEATURE_REBUILD/Spec.md",
    "workplan_path": "FEATURE_REBUILD/Workplan.md"
  }
}

OUTPUT (required):
{
  "step": "0",
  "branch_strategy": {
    "source_feature_branch": "...",
    "rebuild_branch": "...",
    "starting_point": "branch-from-feature|branch-from-main",
    "merge_back": "single-pr|stacked-prs|flagged-rollout"
  },
  "artifact_paths": {
    "root": "...",
    "files": ["..."]
  },
  "assumptions": ["..."]
}
================================================================================

================================================================================
STEP 1 — FEATURE SURFACE MAP (Inventory of Entry Points)
+++Tone(style=formal)
+++Reasoning
+++OutputFormat(type=json)

INPUT (required):
{
  "source_tree_snapshot": {
    "key_files": ["<paths you noticed>"],
    "modules": ["<modules/packages>"],
    "entry_points": ["<UI screens / API endpoints / CLI commands>"]
  },
  "notes": {
    "feature_goal_guess": "<1-2 sentences allowed if uncertain>"
  }
}

OUTPUT (required):
{
  "step": "1",
  "feature_surface": {
    "user_visible_entry_points": ["..."],
    "api_surface": ["..."],
    "stateful_components": ["..."],
    "io_adapters": ["network", "db", "filesystem", "keychain", "..."],
    "feature_flags_and_config": ["..."],
    "permissions_and_privacy": ["..."]
  },
  "open_questions": ["..."],
  "assumptions": ["..."]
}
================================================================================

================================================================================
STEP 2 — OBSERVED BEHAVIOR MATRIX (Evidence Pack)
+++Tone(style=formal)
+++Reasoning
+++Debate
+++OutputFormat(type=json)

INPUT (required):
{
  "evidence_sources": {
    "tests": ["<test names/paths or 'none found'>"],
    "fixtures": ["<paths or 'none'>"],
    "logs_analytics": ["<events or 'unknown'>"],
    "issues_todos": ["<issue ids/links or code TODO paths or 'none'>"]
  }
}

OUTPUT (required):
{
  "step": "2",
  "behavior_matrix": [
    {
      "id": "B-001",
      "trigger": "<user action / API call / event>",
      "inputs": ["..."],
      "preconditions": ["..."],
      "outputs": ["..."],
      "side_effects": ["storage write", "network call", "navigation", "..."],
      "errors": [
        {"condition": "...", "handling": "...", "user_visible": true|false}
      ],
      "observability": {"logs": ["..."], "metrics": ["..."], "events": ["..."]},
      "evidence": ["<test/path>", "<code ref>", "<log>", "<issue>"]
    }
  ],
  "known_bugs": [
    {"id":"BUG-001","symptom":"...","repro":"...","evidence":["..."],"severity":"P0|P1|P2"}
  ],
  "compatibility_contracts": ["<must-not-break statements>"],
  "assumptions": ["..."]
}
================================================================================

================================================================================
STEP 3 — SPEC DRAFT (Implementation-Agnostic)
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
================================================================================

================================================================================
STEP 4 — TARGET ARCHITECTURE (Justified, with Dependency Graph)
+++Tone(style=formal)
+++Reasoning
+++Debate
+++OutputFormat(type=json)

INPUT (required):
{
  "spec_file": "<from step 3>",
  "current_pain_points": [
    {"id":"P-001","problem":"...","evidence":"<code/test/bug>", "impact":"..."}
  ],
  "constraints": {
    "language_stack": "<swift/kotlin/node/rust/etc>",
    "existing_arch_patterns": ["<mvvm, redux, clean architecture, etc>"],
    "modularity_limits": ["<mono-repo constraints etc>"]
  }
}

OUTPUT (required):
{
  "step": "4",
  "file": {
    "path": "FEATURE_REBUILD/Architecture.md",
    "content_md": "Architecture doc"
  },
  "architecture_model": {
    "layers": [
      {"name":"Domain","rules":["pure","no IO"],"depends_on":[]},
      {"name":"UseCases","rules":["orchestrate"],"depends_on":["Domain"]},
      {"name":"Adapters","rules":["IO impl"],"depends_on":["UseCases","Domain"]},
      {"name":"UI","rules":["presentation"],"depends_on":["UseCases"]}
    ],
    "modules": [
      {"name":"FeatureDomain","responsibility":"..."},
      {"name":"FeatureCore","responsibility":"..."}
    ],
    "dependency_graph": [
      {"from":"UI","to":"UseCases"},
      {"from":"UseCases","to":"Domain"},
      {"from":"Adapters","to":"UseCases"}
    ]
  },
  "test_strategy": [
    {"layer":"Domain","tests":["unit"],"notes":"..."},
    {"layer":"UseCases","tests":["unit+integration"],"notes":"..."},
    {"layer":"Adapters","tests":["integration"],"notes":"..."},
    {"layer":"UI","tests":["ui/snapshot"],"notes":"..."}
  ],
  "assumptions": ["..."],
  "open_questions": ["..."]
}

Architecture.md REQUIRED STRUCTURE:
- Title
- Current Pain Points (with evidence)
- Target Principles
- Layering & Dependency Rules
- Module Breakdown
- Key Data Flows (sequence bullets)
- State Management Approach (or N/A)
- Error Handling Strategy
- Testing Strategy
- Risks
================================================================================

================================================================================
STEP 5 — WORKPLAN (Phased Task Graph, Always-Green)
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
================================================================================

================================================================================
STEP 6 — COMPATIBILITY HARNESS & MIGRATION (Prove Parity)
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
================================================================================

================================================================================
STEP 7 — FINAL PACKAGE (File Set)
+++Tone(style=formal)
+++OutputFormat(type=json)

INPUT (required):
{
  "files_from_steps": [
    {"path":"...","content_md":"..."}
  ]
}

OUTPUT (required):
{
  "step": "7",
  "package": {
    "root": "FEATURE_REBUILD",
    "files": [
      {"path":"FEATURE_REBUILD/ObservedBehavior.md","content_md":"..."},
      {"path":"FEATURE_REBUILD/Spec.md","content_md":"..."},
      {"path":"FEATURE_REBUILD/Architecture.md","content_md":"..."},
      {"path":"FEATURE_REBUILD/Workplan.md","content_md":"..."},
      {"path":"FEATURE_REBUILD/CompatibilityHarness.md","content_md":"..."},
      {"path":"FEATURE_REBUILD/Risks.md","content_md":"..."}
    ]
  },
  "next_actions": [
    "Create rebuild branch from ...",
    "Commit artifacts",
    "Start PH-1 / T-001 ..."
  ]
}
================================================================================

</workflow>

<operator_instruction>
Run this workflow step-by-step. Do not merge steps. At each step, output ONLY the JSON for that step.
</operator_instruction>
