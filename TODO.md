# TODO.md

Potential next steps for the Agentic QA Team System.

---

## New Agent: QA Analyst

- [x] Implement `agents/analyst/qa_analyst.py` with four tools: DataOrganizationReportingTool, SiteReliabilityTool, SecurityAssessmentTool, PerformanceProfilingTool
- [x] Create `agents/analyst/Dockerfile` and `agents/analyst/__init__.py`
- [x] Add `qa-analyst` service to `docker-compose.yml`
- [x] Update QA Manager (`qa_manager.py`) to delegate reliability, security, performance, and reporting tasks to the analyst
- [x] Update WebGUI (`app.py`) to surface analyst reports and add `report`, `security`, `performance`, `reliability` commands
- [x] Update README.md and CLAUDE.md with QA Analyst documentation
- [x] See `PROMPT_QA_ANALYST.md` for the full implementation specification

---

## Agent Expansion (6 New Agents + Junior Enhancement)

- [x] **Site Reliability Engineer** — Extract SRE from Analyst into dedicated agent with SiteReliabilityTool, DatabaseTestingTool, InfrastructureHealthTool, IncidentResponseTool
- [x] **Accessibility Tester** — WCAGComplianceTool, ScreenReaderTool, KeyboardNavigationTool, ColorContrastTool
- [x] **API Integration Engineer** — APISchemaValidationTool, ContractTestingTool, APIVersioningTool, APILoadTool
- [x] **Mobile/Device QA** — ResponsiveTestingTool, DeviceCompatibilityTool, NetworkConditionTool, MobileUXTool
- [x] **Compliance & Regulatory Tester** — GDPRComplianceTool, PCIDSSComplianceTool, AuditTrailTool, PolicyEnforcementTool
- [x] **Chaos & Resilience Engineer** — ServiceFailureTool, NetworkPartitionTool, ResourceExhaustionTool, RecoveryValidationTool
- [x] **Junior QA Visual Regression** — VisualRegressionTool (baseline capture, pixel diff, cross-browser, component testing)
- [x] Update QA Manager with 16 scenarios and routing for all 10 agents
- [x] Update docker-compose.yml with all 13 services
- [x] Update WebGUI with all agent commands
- [x] Update CLAUDE.md and README.md documentation

---

## Remaining QA Coverage Gaps

- [ ] **Flaky test detection & management** — identify and quarantine flaky tests, track flake rates, auto-retry strategies
- [ ] **UX/usability testing** — session recording, heatmaps, A/B test analysis, user journey validation
- [ ] **Test management & traceability** — requirement-to-test mapping, defect linking, coverage matrices
- [ ] **i18n/localization testing** — multi-language validation, RTL layout, timezone handling, currency formatting
- [ ] **Advanced performance profiling** — CPU/memory/GC profiling, flame graphs, memory leak detection
- [ ] **Test data privacy** — PII masking, encryption, GDPR-compliant purge, synthetic data anonymization
- [ ] **CI/CD pipeline integration** — GitHub Actions workflows, artifact export, JUnit format results, PR status checks

---

## Testing Infrastructure

- [ ] Create `tests/` directory with pytest structure
- [ ] Add unit tests for each agent's custom tools (tool `_run()` methods can be tested without Redis/Celery)
- [ ] Add integration tests for agent-to-agent communication via Redis pub/sub
- [ ] Add end-to-end tests for the full workflow (requirements → delegation → execution → reporting)
- [ ] Set up `docker-compose.test.yml` for isolated test environments
- [ ] Add `pytest.ini` or `pyproject.toml` with test configuration

## CI/CD Pipeline

- [ ] Add GitHub Actions workflow for automated testing on PR
- [ ] Add linting step (flake8 or ruff) to CI
- [ ] Add type checking step (mypy) to CI
- [ ] Add Docker image build verification to CI
- [ ] Add container health check validation to CI

## Code Quality

- [ ] Add type hints to all function signatures (partially present)
- [ ] Add `pyproject.toml` with unified tool configuration (pytest, linting, formatting)
- [ ] Add a linter configuration (ruff or flake8)
- [ ] Add a formatter configuration (black or ruff format)
- [ ] Replace hardcoded Redis/RabbitMQ connection strings with env vars (currently hardcoded in agent constructors despite env vars being set in docker-compose)

## Agent Improvements

- [ ] Replace simulated/placeholder logic in tool `_run()` methods with real LLM-driven implementations (currently many tools return static example data)
- [ ] Implement actual Playwright-based UI testing in SelfHealingTool (currently CV methods use placeholder templates)
- [ ] Connect RegressionTestingTool to real test execution (currently simulates pass/fail with random)
- [ ] Wire up Celery task workers in each agent (currently agents have `main()` but no Celery worker loop)
- [ ] Add retry logic and error handling for Redis/RabbitMQ connections in agent constructors
- [ ] Implement actual LLM calls in tool methods that currently return hardcoded results (e.g., `_parse_decomposition_result`, `_parse_verification_result`)

## Configuration & Environment

- [ ] Make Redis/RabbitMQ hosts configurable via environment variables in agent constructors (currently hardcoded to `redis` and `rabbitmq`)
- [ ] Add support for configuring agent-specific LLM models (different models for different agents based on task complexity)
- [ ] Add `.env.test` template for test environment configuration
- [ ] Validate required environment variables on startup and fail fast with clear error messages
- [ ] Add configuration for scan targets, SLA thresholds, and performance baselines (needed for QA Analyst)

## WebGUI Enhancements

- [ ] Add a dashboard view showing all active sessions and their statuses
- [ ] Add real-time progress updates using Redis pub/sub → WebSocket push
- [ ] Add report export functionality (PDF, JSON, CSV)
- [ ] Add historical session browsing and comparison
- [ ] Add agent activity visualization (which agent is doing what, in real-time)
- [ ] Add authentication/authorization to the WebGUI

## Infrastructure & Deployment

- [ ] Create `docker-compose.dev.yml` (referenced in README but does not exist)
- [ ] Add container resource limits (memory, CPU) to docker-compose
- [ ] Add log aggregation (ELK stack or similar) for centralized logging
- [ ] Add monitoring/alerting for container health (Prometheus + Grafana)
- [ ] Add Redis persistence configuration for production use
- [ ] Create Kubernetes manifests or Helm chart for production deployment
- [ ] Add TLS configuration for inter-service communication

## Documentation

- [ ] Add API documentation for inter-agent communication protocol
- [ ] Add architecture decision records (ADRs) for key design choices
- [ ] Populate `docs/` directory (currently empty)
- [ ] Add example workflows with expected outputs
- [ ] Add troubleshooting guide for common development issues

## Advanced Features

- [ ] Implement persistent test history and trend tracking across sessions
- [ ] Add webhook/notification integrations (Slack, email, PagerDuty) for critical findings
- [ ] Add support for scheduling recurring test runs
- [ ] Implement agent memory/learning from previous sessions using LangChain memory
- [ ] Add support for custom tool plugins (user-defined tools loaded at runtime)
- [ ] Add multi-tenancy support for team-based usage
- [ ] Implement A/B testing for agent configurations (compare different LLM models/prompts)
