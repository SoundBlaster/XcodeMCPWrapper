# Changelog

All notable changes to the mcpbridge-wrapper project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.1.0]: https://github.com/SoundBlaster/XcodeMCPWrapper/releases/tag/v0.1.0
