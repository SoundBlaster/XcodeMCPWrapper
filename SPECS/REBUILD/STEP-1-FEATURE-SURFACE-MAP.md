# STEP 1 — FEATURE SURFACE MAP (Inventory of Entry Points)
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
