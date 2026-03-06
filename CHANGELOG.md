# Changelog

All notable changes to the mcpbridge-wrapper project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.1] - 2026-03-06

### Fixed

- Broker daemon now sends `notifications/initialized` to the upstream before the `tools/list` probe, completing the MCP handshake and unblocking all subsequent client requests. Previously the probe stalled indefinitely, causing every connected client to time out with 0 tools.

## [0.4.0] - 2026-03-06

### Added

- Persistent broker mode architecture with daemonized upstream session management, multi-client JSON-RPC multiplexing, and stdio proxy support.
- Expanded Web UI observability with tool call detail inspection, session timeline, keyboard shortcuts/command palette, and richer multi-client analytics.

### Changed

- Release metadata aligned for the `0.4.0` publication across package and MCP registry manifests.
- Packaging compatibility declarations aligned to tested Python versions (`3.9`-`3.12`) and modern SPDX license metadata fields.
- Broker startup and transport reliability hardened with transactional startup/rollback behavior and bounded in-memory tracking maps.

### Fixed

- MCP `structuredContent` compliance for empty-content tool results.
- Web UI port collision behavior and stale process cleanup guidance for broker-backed sessions.
- Broker transport handling for numeric JSON-RPC IDs and same-UID client acceptance fallback when peer credential APIs are unavailable.

## [0.3.2] - 2026-02-13

### Fixed

- Publication on https://registry.modelcontextprotocol.io/?q=Xcode was fixed

## [0.3.1] - 2026-02-13

### Fixed

- Included Web UI static assets (`index.html`, `dashboard.css`, `dashboard.js`) in published package artifacts so `--web-ui` serves the full dashboard instead of fallback HTML (`FU-REBUILD-P10-T1-7`).
- Updated all uvx Web UI examples/configs to use `mcpbridge-wrapper[webui]` when `--web-ui` is enabled, preventing missing dependency errors (`FU-P9-T2-1`).

## [0.3.0] - 2026-02-13

### Added

- Optional Web UI dashboard for real-time wrapper monitoring (`--web-ui`)
- Runtime metrics panel with request counts, latency, and error visibility
- Audit logging and activity inspection surfaces for wrapper operations

### Changed

- Documentation and setup guidance aligned for Web UI-enabled workflows
- Release metadata bumped to `0.3.0` for PyPI and MCP Registry publication

## [0.2.0] - 2026-02-08

### Added

- MCP Registry publishing support with automated CI/CD workflow
- `server.json` manifest for MCP Registry compatibility
- GitHub Actions workflow for publishing to PyPI and MCP Registry

### Changed

- Version bump for initial PyPI and MCP Registry release

## [0.1.0] - 2026-02-08

### Added

- **Phase 1: Foundation** - Project structure, Python packaging, development tooling
- **Phase 2: Core Bridge** - Subprocess wrapper around `xcrun mcpbridge` with bidirectional I/O
- **Phase 3: Response Transformation** - JSON parsing, MCP compliance detection, structuredContent injection
- **Phase 4: Edge Cases** - Empty content, non-text content, already compliant responses, error handling
- **Phase 5: Testing** - Comprehensive unit tests (98%+ coverage), integration tests, performance benchmarks
- **Phase 6: Packaging** - Installation script, configuration templates for Cursor/Claude/Codex
- **Phase 7: Documentation** - Installation guide, configuration guides, troubleshooting, API reference

### Features

- ✅ MCP protocol compatibility fix for Cursor
- ✅ Line-buffered I/O for minimal latency (<0.01ms overhead)
- ✅ Memory-efficient processing (<10MB footprint)
- ✅ Graceful error handling and process lifecycle management
- ✅ Support for all 20 Xcode MCP tools
- ✅ Configuration examples for Cursor, Claude Code, and Codex CLI

[0.4.0]: https://github.com/SoundBlaster/XcodeMCPWrapper/releases/tag/v0.4.0
[0.3.2]: https://github.com/SoundBlaster/XcodeMCPWrapper/releases/tag/v0.3.2
[0.3.1]: https://github.com/SoundBlaster/XcodeMCPWrapper/releases/tag/v0.3.1
[0.3.0]: https://github.com/SoundBlaster/XcodeMCPWrapper/releases/tag/v0.3.0
[0.2.0]: https://github.com/SoundBlaster/XcodeMCPWrapper/releases/tag/v0.2.0
[0.1.0]: https://github.com/SoundBlaster/XcodeMCPWrapper/releases/tag/v0.1.0
