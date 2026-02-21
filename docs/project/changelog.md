# Changelog

All notable changes to the Agentic QA Team System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2026.2.16/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **REST Task Submission** (`webgui/api.py`): `POST /api/tasks` and `GET /api/tasks/{id}` — fire-and-forget QA task submission with Redis-backed status polling (ADR-017)
- **API Key Authentication** (`webgui/api.py`, `webgui/auth.py`): `X-API-Key` header support with dual-mode auth (static `AGNOSTIC_API_KEY` env var + Redis-backed per-client keys). New management endpoints: `POST/GET /api/auth/api-keys`, `DELETE /api/auth/api-keys/{key_id}` (ADR-017)
- **Webhook Callbacks** (`webgui/api.py`): Optional `callback_url` + `callback_secret` on task submission — POST result with HMAC-SHA256 `X-Signature` header on task completion (ADR-018)
- **Agent-Specific Convenience Endpoints** (`webgui/api.py`): `POST /api/tasks/security`, `/api/tasks/performance`, `/api/tasks/regression`, `/api/tasks/full` — thin wrappers that route to specific agent subsets (ADR-017)
- **Enhanced Health Check** (`webgui/app.py`): `/health` now checks Redis ping, RabbitMQ TCP connect, and per-agent heartbeat freshness in Redis. Returns `healthy | degraded | unhealthy` with per-component detail. Configurable via `AGENT_STALE_THRESHOLD_SECONDS` (default 300s)
- **CORS Middleware** (`webgui/app.py`): `CORSMiddleware` with `CORS_ALLOWED_ORIGINS` env var (comma-separated, default: `http://localhost:18789,http://localhost:3001`) (ADR-018)
- **OpenAPI Export Script** (`scripts/export-openapi.py`): Generates `docs/api/openapi.json` from the live FastAPI schema
- **ADR-017**: REST Task Submission and API Key Authentication
- **ADR-018**: Webhook Callbacks and CORS Configuration
- **`AGNOSTIC_API_KEY`** and **`CORS_ALLOWED_ORIGINS`** added to `.env.example`
- **34 new unit tests** covering task submission (P1–P4), enhanced health (P6), and API key auth (P2)

### Added
- **Observability Stack** (`shared/metrics.py`): Prometheus metrics (Counter, Histogram, Gauge) with no-op fallback when `prometheus_client` not installed. Named metrics for tasks, LLM calls, HTTP requests, active agents, circuit breaker state. (ADR-015)
- **Structured Logging** (`shared/logging_config.py`): `configure_logging(service_name)` reads `LOG_FORMAT`/`LOG_LEVEL` env vars; JSON output via structlog or stdlib text fallback. (ADR-015)
- **Resilience Primitives** (`shared/resilience.py`): `CircuitBreaker` dataclass (CLOSED→OPEN→HALF_OPEN), `RetryConfig` + `retry_async` decorator with exponential backoff, `GracefulShutdown` async context manager with SIGTERM/SIGINT handling. (ADR-016)
- **`/api/metrics` endpoint** (`webgui/api.py`): Unauthenticated Prometheus scrape endpoint returning exposition format text
- **`observability` optional deps** (`pyproject.toml`): `prometheus-client>=0.20.0`, `structlog>=24.0.0`
- **ADR-015**: Observability Stack Integration
- **ADR-016**: Agent Communication Hardening
- **Plugin Architecture** (`config/agent_registry.py`): Config-driven `AgentRegistry` + `AgentDefinition` dataclass. Replaces hardcoded if/elif task routing in `qa_manager.py` with `registry.route_task()`. Adding new agents no longer requires editing manager or WebGUI code. (ADR-013)
- **WebGUI REST API** (`webgui/api.py`): 18 FastAPI endpoints wrapping existing manager singletons — dashboard (4), sessions (4), reports (3), agents (3), auth (4). JWT auth on all endpoints. (ADR-014)
- **CI/CD Bandit security scan**: New `security-code-scan` job runs Bandit static analysis on all Python source
- **CI/CD Helm lint**: New `helm-lint` job validates Helm chart syntax and template rendering
- **Test coverage expansion**: 48 new unit tests across 5 test files — agent_registry (16), webgui auth (10), webgui exports (7), webgui API (9), config environment (6)
- **ADR-013**: Plugin Architecture for Agent Registration
- **ADR-014**: WebGUI REST API

### Changed
- **Celery reliability** (`config/environment.py`): Added `task_acks_late`, `task_reject_on_worker_lost`, `task_default_retry_delay=60`, `task_max_retries=3`, `worker_cancel_long_running_tasks_on_connection_loss`
- **LLM circuit breaker + metrics** (`config/llm_integration.py`): All 6 async methods instrumented with Prometheus counters/histograms and protected by `CircuitBreaker`
- **Agent graceful shutdown**: All 6 agent `main()` functions now use `GracefulShutdown` context manager instead of bare `except KeyboardInterrupt`
- **`config/team_config.json`**: Added explicit `role`, `celery_task`, `celery_queue`, `redis_prefix` fields to all standard agents
- **`agents/manager/qa_manager.py`**: `_delegate_to_specialists` now uses `AgentRegistry.route_task()` instead of if/elif chain
- **`webgui/app.py`**: Welcome message dynamically generated from `AgentRegistry.get_agents_for_team()`; REST API router mounted
- **CI/CD `pip install`**: Fixed broken `pip install -r requirements.txt` to use `pip install -e ".[dev,test,web,ml]"`
- **CI/CD `container-build`**: Now depends on `security-code-scan` and `helm-lint` jobs

### Security
- **OAuth2 JWT verification**: Replaced `verify_signature: False` with JWKS-based verification for Google, GitHub, and Azure AD providers (`webgui/auth.py`)
- **GitHub OAuth flow**: Implemented full code→token exchange via GitHub API with email fallback
- **Azure AD OAuth flow**: Implemented JWKS-based ID token verification via Microsoft's public keys
- **SAML guard**: Added explicit handler returning None with warning log instead of potential AttributeError
- **Secret key validation**: `WEBGUI_SECRET_KEY` is now required when `ENVIRONMENT=production`
- **Hardcoded credentials removed**: RabbitMQ credentials in `docker-compose.yml` now reference `${RABBITMQ_USER}` / `${RABBITMQ_PASSWORD}` environment variables

### Fixed
- **`datetime.utcnow()` deprecation** (`webgui/auth.py`): Replaced 4 occurrences with `datetime.now(timezone.utc)`
- **Pydantic test collection errors**: Broadened `except ImportError` to `except Exception` in 5 agent tool test files; added try/except to 2 files that lacked it
- **Docker health checks**: Agent health checks now perform actual Redis ping (`r.ping()`) instead of always-passing `print('healthy')`
- **PDF export**: Implemented real PDF generation with ReportLab (`SimpleDocTemplate`, `Paragraph`, `Table`) with HTML fallback when ReportLab is missing
- **WebGUI RABBITMQ_URL**: Added missing `RABBITMQ_URL` environment variable to webgui service in docker-compose
- **CLAUDE.md tool inventory**: Fixed 3 wrong tool names (Security agent), added 4 missing tools (Junior: `FlakyTestDetectionTool`, `UXUsabilityTestingTool`, `LocalizationTestingTool`; Performance: `AdvancedProfilingTool`)
- **CLAUDE.md API endpoints**: Separated implemented (`/health`) from planned endpoints
- **`.env.example`**: Removed duplicate `REDIS_PASSWORD`/`RABBITMQ_PASSWORD` keys, added 11 missing variables
- **Missing dependencies**: Added `PyJWT[crypto]>=2.8.0`, `reportlab>=4.0`, `requests>=2.31.0` to web deps; `faker>=28.0.0` to ml deps in `pyproject.toml`
- **Agent READMEs**: Added missing tools to junior, security_compliance, and performance documentation

### Changed
- **Roadmap rewrite**: Removed verbose "Current Gaps" section (items now fixed), added "Recently Completed" section, streamlined completed items
- **CLAUDE.md**: Added undocumented modules (`config/environment.py`, `config/team_config_loader.py`, `shared/crewai_compat.py`, `shared/data_generation_service.py`)

### Added
- UX/Usability Testing Tool with session analysis, heatmaps, A/B testing
- Advanced Performance Profiling Tool with CPU/memory profiling, GC analysis, memory leak detection, flame graphs
- i18n/Localization Testing Tool with multi-language validation, RTL support, timezone handling, cultural formatting
- Test Traceability Tool with requirement-to-test mapping, coverage matrices, defect linking
- Flaky Test Detection Tool with quarantine management and auto-retry strategies
- Team configuration system with lean/standard/large presets (`config/team_config.json`)
- Team config loader utility (`config/team_config_loader.py`)
- Scalable Team Architecture ADR (ADR-011)
- **SOC 2 Type II Compliance Tool** - Trust service criteria validation (security, availability, processing integrity, confidentiality, privacy)
- **ISO 27001:2022 Compliance Tool** - Annex A controls validation (organizational, people, physical, technological)
- **HIPAA Compliance Tool** - Privacy Rule, Security Rule, and Breach Notification validation
- **Mobile App Testing Tool** - iOS and Android testing with Appium integration, device profiles, functional/UI/performance testing
- **Desktop App Testing Tool** - Windows, macOS, Linux testing for Electron and native apps
- **Cross-Platform Testing Orchestrator** - Unified testing across web, mobile, and desktop platforms
- **Defect Prediction Tool** - ML-driven defect prediction using code churn, complexity, author experience, test coverage, and historical bug analysis
- **Quality Trend Analysis Tool** - Time-series analysis of quality metrics with trend detection, volatility analysis, and future predictions
- **Risk Scoring Tool** - Multi-dimensional risk scoring (technical, business, schedule, resource, compliance) for features and releases
- **Release Readiness Tool** - Comprehensive release readiness assessment combining quality, testing, security, performance, and business dimensions
- **AI Test Generation Tool** - LLM-driven autonomous test case generation from requirements (functional, edge case, negative, boundary, integration, UI tests)
- **Code Analysis Test Generator** - Automatic test generation based on code structure analysis (functions, classes)
- **Autonomous Test Data Generator** - AI-powered intelligent test data generation with constraints validation and quality assessment
- Removed duplicate documentation (docs/guides/quick-start.md)

### Changed
- **Roadmap updated with forward-looking priorities**: Added 10 new roadmap items from code audit — security fixes (critical: OAuth2 JWT verification disabled, hardcoded credentials), WebGUI API implementation, test coverage expansion, CI/CD hardening, K8s production readiness, observability, agent communication, multi-tenant, plugin architecture, test persistence. Added "Current Gaps" section documenting 11 issues across documentation accuracy, security vulnerabilities, and implementation completeness
- **Kubernetes hardened security**: All pods now run with `readOnlyRootFilesystem: true`, `capabilities.drop: [ALL]`, `seccompProfile: RuntimeDefault`, and `runAsNonRoot: true`
- **K8s resource alignment**: Resource limits across Helm chart, raw manifests, and docker-compose are now consistent
- **K8s manifest cleanup**: Consolidated from 3 agent manifest files to 1 (`qa-agents-1.yaml` contains all 5 non-manager agents); removed stale `qa-agents-2.yaml` and `qa-agents-3.yaml` that referenced non-existent agents
- **Kustomization.yaml rewrite**: Removed stale resource refs, broken annotations, and NODE_ENV patches
- **Helm RABBITMQ_URL fix**: Added `rabbitmqPasswordPlain` for URL construction (separate from base64-encoded K8s Secret value)
- **Helm WebGUI fix**: Fixed broken `$(REDIS_HOST)` env var expansion, added missing RABBITMQ_URL, fixed double-tagged image reference
- **Ingress security**: Removed RabbitMQ management exposure from Ingress; added rate-limiting annotations
- Added missing Helm templates: `rabbitmq.yaml`, `serviceaccount.yaml`, `ingress.yaml`
- Added emptyDir volumes (`/tmp`, `/app/logs`) to all pods to support read-only root filesystem
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

## [2026.2.16] - 2026-02-16

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
