# Changelog

All notable changes to the Agentic QA Team System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- UX/Usability Testing Tool with session analysis, heatmaps, A/B testing
- Advanced Performance Profiling Tool with CPU/memory profiling, GC analysis, memory leak detection, flame graphs
- i18n/Localization Testing Tool with multi-language validation, RTL support, timezone handling, cultural formatting
- Test Traceability Tool with requirement-to-test mapping, coverage matrices, defect linking
- Flaky Test Detection Tool with quarantine management and auto-retry strategies
- Team configuration system with lean/standard/large presets (`config/team_config.json`)
- Team config loader utility (`config/team_config_loader.py`)
- Scalable Team Architecture ADR (ADR-011)
- Removed duplicate documentation (docs/guides/quick-start.md)

### Changed
- Updated roadmap to reflect completed medium-term items
- Updated agent documentation with extended tool lists
- Agent reorganization section with team size presets
- Updated all documentation to reflect 6-agent structure instead of 10-agent
- Cleaned up docker-compose.yml to match actual agent implementations
- Removed redundant and outdated documentation files
- Consolidated agent README files
 - Aligned WebGUI commands and exports to the 6-agent architecture
 - Updated QA Manager routing to active agents only

### Removed
- Removed utility scripts: add_type_hints.py, demonstrate_llm_integration.py, update_agents_env.py, check_type_coverage.py
- Removed redundant documentation: DOCUMENTATION_AUDIT.md, PROJECT_COMPLETION.md
- Removed non-existent agent directories: accessibility, api, chaos, compliance, mobile, sre
- Removed outdated agent README files

### Fixed
- Corrected agent count discrepancies across all documentation
- Fixed docker-compose.yml service dependencies
- Updated architecture diagrams to match current implementation
 - Fixed agent task routing names to match Celery task registration

## [1.0.0] - 2026-02-10

### Added
- Complete 6-agent QA system implementation
- CrewAI-based agent orchestration
- Redis/RabbitMQ communication bus
- Chainlit WebGUI interface
- Docker Compose deployment
- Kubernetes manifests and Helm chart
- Comprehensive testing infrastructure
- CI/CD pipeline with GitHub Actions
- Multi-provider LLM integration
- Self-healing UI testing
- Fuzzy verification capabilities
- Risk-based test prioritization

### Features
- QA Manager (orchestration and delegation)
- Senior QA Engineer (complex testing scenarios)
- Junior QA Worker (regression and data generation)
- QA Analyst (security assessment and performance profiling)
- Security & Compliance Agent (OWASP testing, GDPR/PCI DSS)
- Performance & Resilience Agent (load testing, SRE monitoring)

### Infrastructure
- Docker containerization for all services
- Kubernetes deployment manifests
- Helm chart for production deployments
- Redis for caching and pub/sub
- RabbitMQ for message queuing
- Comprehensive logging and monitoring

---

## How to Update This File

When making changes to the project:
1. Add a new `[Unreleased]` section entry
2. Categorize changes as `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, or `Security`
3. When releasing, move the `[Unreleased]` content to a new version section
4. Add a new `[Unreleased]` section at the top
