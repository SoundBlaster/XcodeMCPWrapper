# STEP 7 — FINAL PACKAGE (File Set)
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
