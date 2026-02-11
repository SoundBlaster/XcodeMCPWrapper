# STEP 2 — OBSERVED BEHAVIOR MATRIX (Evidence Pack)
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
