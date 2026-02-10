# STEP 4 — TARGET ARCHITECTURE (Justified, with Dependency Graph)
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
