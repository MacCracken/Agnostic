[![CI/CD](https://img.shields.io/github/actions/workflow/status/MacCracken/Agnostic/ci-cd.yml?branch=main&label=CI/CD)](https://github.com/MacCracken/Agnostic/actions/workflows/ci-cd.yml)
![Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![Docker](https://img.shields.io/badge/docker-ready-blue)

# Agentic QA Team System

A containerized, multi-agent QA platform powered by CrewAI. Six specialized AI agents collaborate via Redis/RabbitMQ to orchestrate intelligent testing workflows with self-healing, fuzzy verification, risk-based prioritization, and comprehensive reliability/security/performance testing.

## Quick Start

```bash
# 1. Clone and setup
git clone <repository-url> && cd agnostic
cp .env.example .env
# Edit .env: set OPENAI_API_KEY

# 2. Launch (Docker)
docker-compose up --build -d

# 3. Access WebGUI
open http://localhost:8000
```

[Full Quick Start Guide →](doc/getting-started/quick-start.md)

## 6-Agent Architecture

```
QA Manager (Orchestrator)          ──┐
Senior QA Engineer (Expert)         ─┤
Junior QA Worker (Executor)         ─┤
QA Analyst (Analyst)                ─┼── Redis + RabbitMQ ── WebGUI (:8000)
Security & Compliance Agent         ─┤
Performance & Resilience Agent      ─┘
```

| Agent | Capabilities | Primary Focus |
|-------|--------------|---------------|
| **QA Manager** | Test planning, delegation, fuzzy verification | Orchestration |
| **Senior QA Engineer** | Self-healing UI, model-based testing, edge cases, AI test generation | Complex Testing |
| **Junior QA Worker** | Regression, data generation, optimization, cross-platform testing | Test Automation |
| **QA Analyst** | Reporting, security, performance, predictive analytics | Analysis |
| **Security & Compliance Agent** | OWASP, GDPR, PCI DSS, SOC 2, ISO 27001, HIPAA | Security |
| **Performance & Resilience Agent** | Load testing, monitoring, resilience checks | Performance |

## Documentation

| Guide | Description |
|-------|-------------|
| [Quick Start](doc/getting-started/quick-start.md) | Get running in 5 minutes |
| [Docker Deployment](doc/deployment/docker-compose.md) | Local & production Docker setup |
| [Kubernetes Deployment](doc/deployment/kubernetes.md) | Production K8s with Helm |
| [Development Setup](doc/development/setup.md) | Local development guide |
| [Agent Docs](doc/agents/index.md) | Agent architecture details |
| [Contributing](doc/development/contributing.md) | Contribution guidelines |
| [Changelog](doc/project/changelog.md) | Version history |
| [Roadmap](doc/project/roadmap.md) | Future plans |

### Additional Resources

- [Architecture Decision Records](docs/adr/) - System design decisions
- [API Documentation](docs/api/) - Agent, WebGUI, LLM APIs
- [Security Assessment](doc/security/assessment.md) - Security findings
- [Docker Build](docker/README.md) - Build optimization
- [Helm Chart](k8s/helm/agentic-qa/README.md) - K8s deployment

## Deployment Options

### Docker Compose (Recommended for Local)

```bash
# Optimized build (99% faster)
./scripts/build-docker.sh --base-only  # One-time (~5 min)
./scripts/build-docker.sh --agents-only  # Rebuilds (~30 sec)
docker-compose up -d
```

[Docker Deployment Guide →](doc/deployment/docker-compose.md)

### Kubernetes (Production)

```bash
# Using Helm (recommended)
helm install agentic-qa ./k8s/helm/agentic-qa \
  --namespace agentic-qa \
  --create-namespace \
  --set secrets.openaiApiKey=$(echo -n "your-key" | base64)
```

[Kubernetes Deployment Guide →](doc/deployment/kubernetes.md)

## Usage Example

```python
from agents.manager.qa_manager_optimized import OptimizedQAManager

manager = OptimizedQAManager()
result = await manager.orchestrate_qa_session({
    "requirements": "Test user authentication flow",
    "target_url": "http://localhost:8000",
    "compliance_standards": ["GDPR", "PCI DSS", "SOC 2", "ISO 27001", "HIPAA"]
})
```

## Key Features

- **Self-Healing UI Testing**: CV-based element detection with automatic selector repair
- **Fuzzy Verification**: LLM-based quality scoring beyond pass/fail
- **Risk-Based Prioritization**: ML-driven test ordering by risk score
- **Security & Compliance**: Automated OWASP, GDPR, PCI DSS, SOC 2, ISO 27001, HIPAA validation
- **Cross-Platform Testing**: Web, mobile (iOS/Android), and desktop (Windows/macOS/Linux) unified testing
- **Predictive Quality Analytics**: ML-driven defect prediction, quality trend analysis, risk scoring, and release readiness assessment
- **AI-Enhanced Test Generation**: Autonomous test case generation from requirements and code analysis using LLM
- **Performance Profiling**: Load testing with bottleneck identification
- **Real-time Dashboard**: Live monitoring via Chainlit WebGUI

## Technology Stack

- **Agents**: CrewAI 0.11+ (crewai package)
- **LLMs**: OpenAI, Anthropic, Google Gemini, Ollama, LM Studio
- **Web UI**: Chainlit 1.1+ / 2.x compatible + FastAPI
- **Messaging**: Redis 5.0+ + RabbitMQ + Celery
- **Automation**: Playwright 1.45+
- **ML/CV**: scikit-learn, OpenCV, NumPy, Pandas

**Python**: 3.11-3.13 (compatible)

## Contributing

See [Contributing Guidelines](doc/development/contributing.md).

## License

MIT License - see [LICENSE](LICENSE) file.

---

*Last Updated: 2026-02-16* | [Documentation](doc/README.md) | [Changelog](doc/project/changelog.md)
