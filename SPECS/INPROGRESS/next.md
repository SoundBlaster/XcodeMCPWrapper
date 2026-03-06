# Next Task: P4-T2 — Cache tools/list in broker and gate client responses on upstream readiness

**Priority:** P1
**Phase:** Phase 4: Broker Advanced Features
**Effort:** Large
**Dependencies:** None
**Status:** Selected

## Description

The broker currently forwards `tools/list` to the upstream on every client request with no buffering. This creates a race: when the upstream (`xcrun mcpbridge`) is still initializing or waiting for Xcode approval, a client's `tools/list` gets no reply or an empty one, which the client caches as "0 tools".

The fix has two parts:
1. **Upstream readiness gate** — after spawning the upstream, the broker waits for a successful `initialize` round-trip before accepting or processing further client requests; if the upstream exits immediately (e.g. Xcode dialog not yet approved), the broker retries with backoff instead of forwarding the failure to clients.
2. **tools/list response cache** — after upstream initialization succeeds, the broker immediately fetches and caches the `tools/list` response; subsequent client `tools/list` requests are served from cache; cache is invalidated and refreshed on upstream reconnect.

Together these eliminate the Xcode first-approval race: the broker is silent to clients until the upstream is truly ready, and once ready the tools list is served instantly from cache.

## Next Step

Run the PLAN command to generate the implementation-ready PRD.
