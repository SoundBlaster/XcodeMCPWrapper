# Web UI Rebuild Risks

## Risk Register

| ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R-001 | Contract drift between frontend expectations and backend payloads | Medium | High | Lock schema with fixture-based contract tests and CI gates |
| R-002 | Metrics abstraction refactor causes runtime performance degradation | Medium | Medium | Benchmark key paths and keep SQL indexes, bounded windows |
| R-003 | Auth flow changes break websocket live updates | Medium | High | Add explicit auth-mode websocket tests and fallback polling checks |
| R-004 | Documentation-runtime mismatch persists after rebuild | Medium | Medium | Treat docs changes as required acceptance criteria with review checklist |
| R-005 | Multi-process metrics edge cases produce nondeterministic tests | Medium | Medium | Use deterministic fixtures and tolerance windows for time-based assertions |

## Open Questions

1. Should websocket authentication be cookie/session based or explicit token query based?
2. Should `SharedMetricsStore` expose exact percentiles (costlier query) or clearly labeled approximations?
3. Should Web UI support an explicit `WEBUI_ENABLED` env switch to reduce reliance on CLI flags for managed runtimes?

## Residual Risks After Rebuild

- Minor timing jitter in timeseries buckets may still exist under heavy concurrent load.
- Browser-specific websocket behavior under Basic auth may vary by environment.
- Operator misconfiguration remains possible when custom config files and env overrides conflict.
