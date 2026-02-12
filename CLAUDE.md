# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agentic QA Team System — a containerized, multi-agent QA platform powered by CrewAI. Six specialized AI agents (QA Manager, Senior QA Engineer, Junior QA Worker, QA Analyst, Security & Compliance Agent, Performance & Resilience Agent) collaborate via Redis/RabbitMQ to orchestrate intelligent testing workflows with self-healing, fuzzy verification, risk-based prioritization, and comprehensive reliability/security/performance testing. A Chainlit-based WebGUI provides human-in-the-loop interaction.

All application code lives under the project root directory.

## Build & Run Commands

### Docker Compose (Local Development)

```bash
# Setup
cp .env.example .env   # then set OPENAI_API_KEY

# Install dependencies
pip install -e .[dev,test,web,ml,browser]  # Install with optional dependencies

# Build using optimized base image (99% faster rebuilds)
./scripts/build-docker.sh              # Full build: base + all agents
./scripts/build-docker.sh --base-only  # Build base image only (~5 min)
./scripts/build-docker.sh --agents-only # Build agents only (~30 sec)

# Launch all containers (after building)
docker-compose up -d

# Traditional build (slower but simpler)
docker-compose up --build

# Rebuild specific service
docker-compose up --build <service-name>

# View logs
docker-compose logs <service-name>   # qa-manager, senior-qa, junior-qa, qa-analyst, security-compliance-agent, performance-agent, webgui, redis, rabbitmq
```

### Kubernetes (Production/Cloud)

#### Option 1: Direct Kubernetes Manifests

```bash
# Apply all manifests
kubectl apply -k k8s/

# Set OpenAI API key
kubectl create secret generic qa-secrets \
  --from-literal=openai-api-key=$(echo -n "your-key" | base64) \
  --from-literal=rabbitmq-password=Z3Vlc3Q= \
  -n agentic-qa

# Check deployment status
kubectl get pods -n agentic-qa
kubectl get services -n agentic-qa

# Port forward webgui
kubectl port-forward service/webgui-service 8000:8000 -n agentic-qa
```

#### Option 2: Helm Chart (Recommended)

```bash
# Install with Helm
helm install agentic-qa ./k8s/helm/agentic-qa \
  --namespace agentic-qa \
  --create-namespace \
  --set secrets.openaiApiKey=$(echo -n "your-openai-key" | base64)

# Upgrade deployment
helm upgrade agentic-qa ./k8s/helm/agentic-qa \
  --namespace agentic-qa \
  --set ingress.enabled=true \
  --set ingress.host=qa.yourdomain.com

# Scale specific agents
helm upgrade agentic-qa ./k8s/helm/agentic-qa \
  --namespace agentic-qa \
  --set agents.juniorQa.replicaCount=3

# Uninstall
helm uninstall agentic-qa --namespace agentic-qa
```

### Development & Testing

```bash
# Local development (without Docker)
pip install -r requirements.txt

# Testing
python run_tests.py --mode all --env mock          # Run all tests with mocks
python run_tests.py --mode unit                    # Unit tests only  
python run_tests.py --mode integration --env docker # Integration tests with Docker
python run_tests.py --mode coverage                 # Tests with coverage report

# Direct pytest usage
pytest tests/ -v                                   # Run all tests
pytest tests/unit/ -m unit                          # Unit tests only
pytest tests/integration/ -m integration            # Integration tests only
```

### Code Quality

```bash
# Code Quality
ruff check agents/ config/ shared/ webgui/          # Lint code
ruff format agents/ config/ shared/ webgui/          # Format code
black agents/ config/ shared/ webgui/                 # Alternative formatting
mypy agents/ config/ shared/                      # Type checking
bandit -r agents/ config/ shared/                   # Security scan

# Pre-commit hooks (install once)
pre-commit install                                 # Install git hooks
pre-commit run --all-files                         # Run all quality checks
```

**Access URLs:**
- **Docker:** WebGUI: `http://localhost:8000` | RabbitMQ: `http://localhost:15672` (guest/guest)
- **Kubernetes:** WebGUI: `kubectl port-forward service/webgui-service 8000:8000 -n agentic-qa` | RabbitMQ: `kubectl port-forward service/rabbitmq-service 15672:15672 -n agentic-qa`

## Architecture

```
QA Manager (Orchestrator)          ──┐
Senior QA Engineer (Expert)         ─┤
Junior QA Worker (Executor)         ─┤
QA Analyst (Analyst)                ─┼── Redis + RabbitMQ Bus ── Chainlit WebGUI (:8000)
Security & Compliance Agent         ─┤
Performance & Resilience Agent      ─┘
```

**Agent roles and delegation flow:**
1. **QA Manager** (`agents/manager/qa_manager.py`) — decomposes requirements into test plans, delegates tasks by complexity, performs fuzzy verification (LLM-based 0-1 quality scoring), synthesizes reports. Tools: `TestPlanDecompositionTool`, `FuzzyVerificationTool`.
2. **Senior QA Engineer** (`agents/senior/senior_qa.py`) — handles complex scenarios: self-healing UI selectors (CV + semantic analysis), model-based testing (FSM), edge-case/boundary analysis. Tools: `SelfHealingTool`, `ModelBasedTestingTool`, `EdgeCaseAnalysisTool`.
3. **Junior QA Worker** (`agents/junior/junior_qa.py`) — executes regression suites, root cause detection, synthetic data generation, risk-based test ordering, visual regression testing. Tools: `RegressionTestingTool`, `SyntheticDataGeneratorTool`, `TestExecutionOptimizerTool`, `VisualRegressionTool`.
4. **QA Analyst** (`agents/analyst/qa_analyst.py`) — aggregates test data into structured reports, runs security assessments (headers, TLS, OWASP indicators), profiles performance (latency, throughput, bottlenecks), and produces comprehensive cross-cutting reports with release readiness verdicts. Tools: `DataOrganizationReportingTool`, `SecurityAssessmentTool`, `PerformanceProfilingTool`.
5. **Security & Compliance Agent** (`agents/security_compliance/qa_security_compliance.py`) — handles security testing (OWASP, penetration testing), compliance validation (GDPR, PCI DSS), and audit trail management. Tools: `SecurityTestingTool`, `ComplianceValidationTool`, `AuditTrailTool`.
6. **Performance & Resilience Agent** (`agents/performance/qa_performance.py`) — monitors system performance, load testing, stress testing, and infrastructure resilience. Tools: `PerformanceMonitoringTool`, `LoadTestingTool`, `ResilienceValidationTool`.

**Key modules:**
- `config/model_manager.py` — multi-provider LLM manager (OpenAI, Anthropic, Google, Ollama, LM Studio) with fallback chains
- `config/universal_llm_adapter.py` — bridge between model_manager and CrewAI's LLM interface
- `config/models.json` — provider configuration (routing strategy, retries, timeouts)
- `config/llm_integration.py` — comprehensive LLM service for intelligent tool implementations (scenario generation, risk identification, fuzzy verification, security analysis, performance profiling)
- `advanced_testing/self_healing_fuzzy_verification.py` — CV-based element detection, semantic selector repair, fuzzy matching
- `advanced_testing/risk_prioritization_exploratory.py` — ML-driven risk scoring, code change analysis, exploratory test generation
- `webgui/` — Enhanced Chainlit-based WebGUI with comprehensive monitoring and reporting
  - `app.py` — Main Chainlit application with chat interface and agent interaction
  - `dashboard.py` — Real-time dashboard showing active sessions and resource utilization
  - `realtime.py` — WebSocket infrastructure for live updates and notifications
  - `exports.py` — PDF/JSON/CSV report generation with charts and analytics
  - `history.py` — Session browsing, comparison, and trend analysis
  - `agent_monitor.py` — Agent activity visualization and performance monitoring
  - `auth.py` — JWT-based authentication with role-based access control

## Container & Orchestration

### Docker Compose (Local)
**Eight containers** defined in `docker-compose.yml`: `redis` (:6379), `rabbitmq` (:5672, :15672), `qa-manager`, `senior-qa`, `junior-qa`, `qa-analyst`, `security-compliance-agent`, `performance-agent`, `webgui` (:8000).

**Optimized Build System:**
- **Base Image** (`agnostic-qa-base`): Pre-built with all common dependencies (CrewAI, LangChain, Redis, RabbitMQ, Playwright, OpenCV)
- **Agent Images**: Extend base image with only agent-specific code
- **Performance**: 99% faster rebuilds (~30 sec vs 10-15 min)
- See [docker/README.md](docker/README.md) for build optimization details

### Kubernetes (Production)
**Kustomize-based manifests** in `k8s/manifests/` with:
- Namespace `agentic-qa`
- Infrastructure services (Redis, RabbitMQ) with persistent volumes
- Agent deployments with health checks, resource limits, and scaling
- ConfigMaps/Secrets for configuration management
- Service discovery and networking
- Optional Ingress for external access

**Helm chart** in `k8s/helm/agentic-qa/` with:
- Configurable agent enablement and resource allocation
- Autoscaling support
- Custom values for different environments
- Integrated secrets management
- Dependency management and lifecycle hooks

## Key Technology Stack

- **Agent framework:** CrewAI 0.75.0 + LangChain 0.2.16
- **LLM providers:** OpenAI (primary), Anthropic, Google Gemini, Ollama, LM Studio
- **Web UI:** Chainlit 1.1.304 + FastAPI
- **Messaging:** Redis 5.0.8 + Celery 5.4.0 + RabbitMQ
- **Browser automation:** Playwright 1.45.0
- **ML/CV:** scikit-learn 1.5.1, OpenCV 4.10.0, NumPy, Pandas
- **Testing:** pytest 8.3.2

## Adding New Agents

1. Create directory under `agents/`
2. Implement agent class using CrewAI; extend `BaseTool` for custom tools
3. Add a Dockerfile (follow existing pattern: Python 3.11-slim, PYTHONPATH=/app)
4. Add service to `docker-compose.yml`
5. Add Kubernetes manifest in `k8s/manifests/` or update Helm chart template
6. Add scenario + routing in `agents/manager/qa_manager.py`
7. Integrate with WebGUI in `webgui/app.py`

## Environment Configuration

Configured via `.env` (see `.env.example`). **NEW**: All Redis/RabbitMQ connections now use environment configuration with validation and logging. Key variables: 

**Connection**: `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_PASSWORD`, `RABBITMQ_HOST`, `RABBITMQ_PORT`, `RABBITMQ_USER`, `RABBITMQ_PASSWORD`, `RABBITMQ_VHOST`

**LLM**: `OPENAI_API_KEY`, `OPENAI_MODEL`, `PRIMARY_MODEL_PROVIDER`, `FALLBACK_MODEL_PROVIDERS`

**Features**: `ENABLE_SELF_HEALING`, `ENABLE_FUZZY_VERIFICATION`, `ENABLE_RISK_BASED_PRIORITIZATION`, `ENABLE_CONTEXT_AWARE_TESTING`

Configuration system includes validation on startup, connection logging (without passwords), and fallback to URL-based config for backwards compatibility.

## WebGUI Enhancements

The WebGUI has been enhanced with comprehensive monitoring, reporting, and authentication capabilities:

### Architecture Decisions (ADRs)
See `docs/adr/` for detailed Architecture Decision Records:
- **ADR-001**: WebGUI Technology Stack Selection (Chainlit + FastAPI)
- **ADR-002**: Real-time Communication Infrastructure (Redis Pub/Sub + WebSocket)
- **ADR-003**: Session Management Architecture (Hybrid Redis + File-based)
- **ADR-004**: Report Generation Strategy (Template-based with multiple formats)
- **ADR-005**: Authentication and Authorization Design (JWT + RBAC)

### Real-time Features
- **Dashboard**: Live session monitoring with status indicators and resource metrics
- **WebSocket Updates**: Real-time progress, agent status, and notifications
- **Agent Monitoring**: Performance metrics, task queue visualization, communication graphs
- **Resource Tracking**: CPU/memory usage, Redis metrics, system load

### Reporting & Analytics
- **Multi-format Exports**: PDF (with charts), JSON (raw data), CSV (spreadsheet analysis)
- **Report Types**: Executive Summary, Technical Report, Compliance Report, Agent Performance
- **Historical Analysis**: Session comparison, trend analysis, searchable archives
- **Scheduled Reports**: Automated generation and distribution

### Authentication & Security
- **Multi-provider Auth**: Google OAuth2, GitHub, Azure AD, SAML support
- **Role-based Access Control**: Super Admin, Org Admin, Team Lead, QA Engineer, Viewer, API User
- **Resource Isolation**: Team-based data separation, audit trails, permission checking
- **JWT Tokens**: Access tokens (15 min) + refresh tokens (7 days) with blacklisting

### Session Management
- **Hybrid Storage**: Redis for active sessions, file system for persistence, database for metadata
- **Session Lifecycle**: Creation → Planning → Testing → Analysis → Completion → Archive
- **Snapshots**: Periodic session state preservation for crash recovery
- **Search & Filter**: By user, date range, status, custom criteria

### WebGUI Environment Variables
```bash
# Authentication
WEBGUI_SECRET_KEY=your-secret-key
OAUTH2_GOOGLE_CLIENT_ID=your-google-client-id
OAUTH2_GOOGLE_CLIENT_SECRET=your-google-client-secret

# Real-time Features
WEBSOCKET_ENABLED=true
REDIS_PUBSUB_CHANNEL=webgui_updates

# Reporting
REPORT_EXPORT_PATH=/app/reports
PDF_GENERATOR_ENGINE=reportlab
```

### WebGUI API Endpoints
The enhanced WebGUI includes FastAPI endpoints for:
- `/api/dashboard` - Dashboard data and metrics
- `/api/sessions` - Session management and history
- `/api/reports` - Report generation and download
- `/api/agents` - Agent monitoring and status
- `/api/auth` - Authentication and authorization
- `/ws/realtime` - WebSocket real-time updates

### Static Assets
Frontend assets are organized in `webgui/static/`:
- `css/` - Stylesheets for dashboard, reports, and custom components
- `js/` - JavaScript for real-time updates, charts, and interactive elements
- `images/` - Icons, logos, and static images
- `templates/` - HTML templates for custom reports and email notifications

---

## Full Documentation

For comprehensive documentation, see the [doc/](doc/) directory:
- [Quick Start Guide](doc/getting-started/quick-start.md)
- [Deployment Guides](doc/deployment/)
- [Development Setup](doc/development/setup.md)
- [Agent Documentation](doc/agents/)
- [Project Roadmap](doc/project/roadmap.md)
