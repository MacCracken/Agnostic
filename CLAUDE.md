# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agentic QA Team System — a containerized, multi-agent QA platform powered by CrewAI. Ten specialized AI agents (QA Manager, Senior QA Engineer, Junior QA Worker, QA Analyst, Site Reliability Engineer, Accessibility Tester, API Integration Engineer, Mobile/Device QA, Compliance Tester, Chaos Engineer) collaborate via Redis/RabbitMQ to orchestrate intelligent testing workflows with self-healing, fuzzy verification, risk-based prioritization, and comprehensive reliability/security/performance/accessibility/compliance analysis. A Chainlit-based WebGUI provides human-in-the-loop interaction.

All application code lives under the `agentic/` directory.

## Build & Run Commands

```bash
# Setup
cd agentic
cp .env.example .env   # then set OPENAI_API_KEY

# Launch all containers
docker-compose up --build

# Detached mode
docker-compose up -d --build

# Rebuild specific service
docker-compose up --build <service-name>

# View logs
docker-compose logs <service-name>   # qa-manager, senior-qa, junior-qa, qa-analyst, sre-agent, accessibility-agent, api-agent, mobile-agent, compliance-agent, chaos-agent, webgui, redis, rabbitmq

# Local development (without Docker)
pip install -r agentic/requirements.txt
pytest tests/
```

WebGUI: `http://localhost:8000` | RabbitMQ Management: `http://localhost:15672` (guest/guest)

## Architecture

```
QA Manager (Orchestrator)          ──┐
Senior QA Engineer (Expert)         ─┤
Junior QA Worker (Executor)         ─┤
QA Analyst (Analyst)                ─┤
Site Reliability Engineer (SRE)     ─┤
Accessibility Tester (A11y)         ─┼── Redis + RabbitMQ Bus ── Chainlit WebGUI (:8000)
API Integration Engineer (API)      ─┤
Mobile/Device QA (Mobile)           ─┤
Compliance Tester (Compliance)      ─┤
Chaos Engineer (Chaos)              ─┘
```

**Agent roles and delegation flow:**
1. **QA Manager** (`agents/manager/qa_manager.py`) — decomposes requirements into test plans, delegates tasks by complexity, performs fuzzy verification (LLM-based 0-1 quality scoring), synthesizes reports. Tools: `TestPlanDecompositionTool`, `FuzzyVerificationTool`.
2. **Senior QA Engineer** (`agents/senior/senior_qa.py`) — handles complex scenarios: self-healing UI selectors (CV + semantic analysis), model-based testing (FSM), edge-case/boundary analysis. Tools: `SelfHealingTool`, `ModelBasedTestingTool`, `EdgeCaseAnalysisTool`.
3. **Junior QA Worker** (`agents/junior/junior_qa.py`) — executes regression suites, root cause detection, synthetic data generation, risk-based test ordering, visual regression testing. Tools: `RegressionTestingTool`, `SyntheticDataGeneratorTool`, `TestExecutionOptimizerTool`, `VisualRegressionTool`.
4. **QA Analyst** (`agents/analyst/qa_analyst.py`) — aggregates test data into structured reports, runs security assessments (headers, TLS, OWASP indicators), profiles performance (latency, throughput, bottlenecks), and produces comprehensive cross-cutting reports with release readiness verdicts. Tools: `DataOrganizationReportingTool`, `SecurityAssessmentTool`, `PerformanceProfilingTool`.
5. **Site Reliability Engineer** (`agents/sre/qa_sre.py`) — monitors site reliability (health checks, SLA compliance), tests database resilience, checks infrastructure health, and handles incident response. Tools: `SiteReliabilityTool`, `DatabaseTestingTool`, `InfrastructureHealthTool`, `IncidentResponseTool`.
6. **Accessibility Tester** (`agents/accessibility/qa_accessibility.py`) — audits WCAG 2.1 AA/AAA compliance, screen reader compatibility, keyboard navigation, and color contrast. Tools: `WCAGComplianceTool`, `ScreenReaderTool`, `KeyboardNavigationTool`, `ColorContrastTool`.
7. **API Integration Engineer** (`agents/api/qa_api.py`) — validates OpenAPI specs, verifies consumer/provider contracts, checks API versioning, and performs endpoint load testing. Tools: `APISchemaValidationTool`, `ContractTestingTool`, `APIVersioningTool`, `APILoadTool`.
8. **Mobile/Device QA** (`agents/mobile/qa_mobile.py`) — tests responsive design, device compatibility matrix, network condition simulation, and mobile UX patterns. Tools: `ResponsiveTestingTool`, `DeviceCompatibilityTool`, `NetworkConditionTool`, `MobileUXTool`.
9. **Compliance Tester** (`agents/compliance/qa_compliance.py`) — verifies GDPR compliance, PCI DSS standards, audit trail integrity, and organizational policy enforcement. Tools: `GDPRComplianceTool`, `PCIDSSComplianceTool`, `AuditTrailTool`, `PolicyEnforcementTool`.
10. **Chaos Engineer** (`agents/chaos/qa_chaos.py`) — injects service failures, simulates network partitions, tests resource exhaustion, and validates recovery mechanisms. Tools: `ServiceFailureTool`, `NetworkPartitionTool`, `ResourceExhaustionTool`, `RecoveryValidationTool`.

**Key modules:**
- `config/model_manager.py` — multi-provider LLM manager (OpenAI, Anthropic, Google, Ollama, LM Studio) with fallback chains
- `config/universal_llm_adapter.py` — bridge between model_manager and CrewAI's LLM interface
- `config/models.json` — provider configuration (routing strategy, retries, timeouts)
- `advanced_testing/self_healing_fuzzy_verification.py` — CV-based element detection, semantic selector repair, fuzzy matching
- `advanced_testing/risk_prioritization_exploratory.py` — ML-driven risk scoring, code change analysis, exploratory test generation
- `webgui/app.py` — Chainlit + FastAPI web interface with file upload, session management, reasoning traces

## Docker Services

Thirteen containers defined in `agentic/docker-compose.yml`: `redis` (:6379), `rabbitmq` (:5672, :15672), `qa-manager`, `senior-qa`, `junior-qa`, `qa-analyst`, `sre-agent`, `accessibility-agent`, `api-agent`, `mobile-agent`, `compliance-agent`, `chaos-agent`, `webgui` (:8000). All agent containers use Python 3.11-slim with shared volume mounts for agent code and config.

## Key Technology Stack

- **Agent framework:** CrewAI 0.75.0 + LangChain 0.2.16
- **LLM providers:** OpenAI (primary), Anthropic, Google Gemini, Ollama, LM Studio
- **Web UI:** Chainlit 1.1.304 + FastAPI
- **Messaging:** Redis 5.0.8 + Celery 5.4.0 + RabbitMQ
- **Browser automation:** Playwright 1.45.0
- **ML/CV:** scikit-learn 1.5.1, OpenCV 4.10.0, NumPy, Pandas
- **Testing:** pytest 8.3.2

## Adding New Agents

1. Create directory under `agentic/agents/`
2. Implement agent class using CrewAI; extend `BaseTool` for custom tools
3. Add a Dockerfile (follow existing pattern: Python 3.11-slim, PYTHONPATH=/app)
4. Add service to `docker-compose.yml`
5. Add scenario + routing in `agents/manager/qa_manager.py`
6. Integrate with WebGUI in `webgui/app.py`

## Environment Configuration

Configured via `.env` (see `.env.example`). Key variables: `OPENAI_API_KEY`, `OPENAI_MODEL`, `REDIS_URL`, `RABBITMQ_URL`. Feature flags: `ENABLE_SELF_HEALING`, `ENABLE_FUZZY_VERIFICATION`, `ENABLE_RISK_BASED_PRIORITIZATION`, `ENABLE_CONTEXT_AWARE_TESTING`. Multi-provider fallback configured via `PRIMARY_MODEL_PROVIDER` and `FALLBACK_MODEL_PROVIDERS`.
