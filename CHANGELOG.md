# Changelog

All notable changes to MLX LLM Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions CI/CD workflow
- Comprehensive test suite with pytest
- CONTRIBUTING.md for contributors
- LICENSE file (MIT)
- Docker support (coming soon)

### Changed
- Default port changed from 8000 to 9123 to avoid conflicts
- Default model changed to LibraxisAI/Qwen3-14b-MLX-Q5 (premium quality)
- All scripts now use pure `uv run` without python prefix
- Removed all hardcoded paths from scripts

### Fixed
- Fixed pydantic v2 compatibility (BaseSettings moved to pydantic-settings)
- Fixed VLM server startup to use dynamic model detection
- Updated allowed origins to use correct port (9123)

## [1.0.0] - 2024-12-28

### Added
- Initial release of MLX LLM Server
- OpenAI-compatible API endpoints
- Native MLX support for Apple Silicon optimization
- ChukSessions integration for conversation persistence
- Multi-model support with dynamic loading/unloading
- SSL/TLS support for production deployments
- Redis integration for session storage
- Prometheus metrics for monitoring
- API key and JWT authentication
- Rate limiting per service
- Production/development mode split
- Comprehensive documentation

### Features
- Support for LLM, VLM, embedding, and reranker models
- Memory-aware model management
- Session management with TTL
- Health check endpoints
- Model routing capabilities
- Tailscale integration support

[Unreleased]: https://github.com/LibraxisAI/mlx-llm-server/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/LibraxisAI/mlx-llm-server/releases/tag/v1.0.0