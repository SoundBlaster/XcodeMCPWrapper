# STEP 0 — SESSION SETUP (Branch + Paths)
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
