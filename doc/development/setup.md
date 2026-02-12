# Development Setup

This guide provides detailed instructions for setting up a local development environment for the Agentic QA Team System.

## Project Overview

Agentic QA Team System is a containerized, multi-agent QA platform powered by CrewAI. Six specialized AI agents collaborate via Redis/RabbitMQ to orchestrate intelligent testing workflows with self-healing, fuzzy verification, risk-based prioritization, and comprehensive reliability/security/performance testing. A Chainlit-based WebGUI provides human-in-the-loop interaction.

All application code lives under the project root directory.

## Prerequisites

- Python 3.11+
- Docker 20.10+ and Docker Compose
- Git
- 4GB+ RAM for parallel agent execution
- OpenAI API Key (or other LLM provider)

## Setup

### 1. Clone and Configure

```bash
# Clone repository
git clone <repository-url>
cd agnostic

# Copy environment template
cp .env.example .env

# Edit .env and set your API key
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
PRIMARY_MODEL_PROVIDER=openai
```

### 2. Install Dependencies

```bash
# Install with all optional dependencies
pip install -e ".[dev,test,web,ml,browser]"

# Or install specific groups
pip install -e ".[dev,test]"  # Development and testing
pip install -e ".[web]"      # WebGUI dependencies
```

### 3. Start Infrastructure Services

```bash
# Start Redis and RabbitMQ
docker-compose up -d redis rabbitmq

# Verify services are running
docker-compose ps
```

### 4. Run Agents in Development Mode

In separate terminal windows:

```bash
# Terminal 1: QA Manager
python -m agents.manager.qa_manager

# Terminal 2: Senior QA
python -m agents.senior.senior_qa

# Terminal 3: Junior QA
python -m agents.junior.junior_qa

# Terminal 4: QA Analyst
python -m agents.analyst.qa_analyst

# Terminal 5: Security & Compliance
python -m agents.security_compliance.qa_security_compliance

# Terminal 6: Performance & Resilience
python -m agents.performance.qa_performance
```

### 5. Start WebGUI

```bash
python -m webgui.app
```

Access the WebGUI at http://localhost:8000

## Testing

### Running Tests

```bash
# All tests with mocks
python run_tests.py --mode all --env mock

# Unit tests only
python run_tests.py --mode unit

# Integration tests (requires Docker)
python run_tests.py --mode integration --env docker

# With coverage report
python run_tests.py --mode coverage

# Direct pytest usage
pytest tests/ -v
pytest tests/unit/ -m unit
pytest tests/integration/ -m integration
```

### Test Structure

- `tests/unit/` - Unit tests for individual components
- `tests/integration/` - Integration tests for agent communication
- `tests/end-to-end/` - Full workflow tests

## Code Quality

### Linting and Formatting

```bash
# Lint code
ruff check agents/ config/ shared/ webgui/

# Format code
ruff format agents/ config/ shared/ webgui/

# Alternative: Use Black
black agents/ config/ shared/ webgui/

# Type checking
mypy agents/ config/ shared/

# Security scan
bandit -r agents/ config/ shared/
```

### Pre-commit Hooks

```bash
# Install hooks
pre-commit install

# Run all checks on all files
pre-commit run --all-files
```

## Architecture

### 6-Agent System

```
QA Manager (Orchestrator)          ──┐
Senior QA Engineer (Expert)         ─┤
Junior QA Worker (Executor)         ─┤
QA Analyst (Analyst)                ─┼── Redis + RabbitMQ Bus ── Chainlit WebGUI (:8000)
Security & Compliance Agent         ─┤
Performance & Resilience Agent      ─┘
```

### Agent Roles

1. **QA Manager** (`agents/manager/qa_manager.py`) - Test planning, delegation, fuzzy verification
2. **Senior QA Engineer** (`agents/senior/senior_qa.py`) - Complex scenarios, self-healing, model-based testing
3. **Junior QA Worker** (`agents/junior/junior_qa.py`) - Regression testing, data generation, visual testing
4. **QA Analyst** (`agents/analyst/qa_analyst.py`) - Reporting, security assessment, performance profiling
5. **Security & Compliance Agent** (`agents/security_compliance/qa_security_compliance.py`) - OWASP testing, GDPR/PCI DSS validation
6. **Performance & Resilience Agent** (`agents/performance/qa_performance.py`) - Load testing, monitoring, resilience checks

### Key Modules

- `config/model_manager.py` - Multi-provider LLM manager with fallback chains
- `config/universal_llm_adapter.py` - Bridge between model_manager and CrewAI
- `config/models.json` - Provider configuration
- `config/llm_integration.py` - LLM service for intelligent tools
- `advanced_testing/self_healing_fuzzy_verification.py` - CV-based element detection
- `advanced_testing/risk_prioritization_exploratory.py` - ML-driven risk scoring
- `webgui/` - Chainlit-based WebGUI with monitoring and reporting

## Technology Stack

- **Agent framework:** CrewAI 0.75.0 + LangChain 0.2.16
- **LLM providers:** OpenAI, Anthropic, Google Gemini, Ollama, LM Studio
- **Web UI:** Chainlit 1.1.304 + FastAPI
- **Messaging:** Redis 5.0.8 + Celery 5.4.0 + RabbitMQ
- **Browser automation:** Playwright 1.45.0
- **ML/CV:** scikit-learn 1.5.1, OpenCV 4.10.0
- **Testing:** pytest 8.3.2

## Environment Variables

### Required

```bash
OPENAI_API_KEY=your_key_here
PRIMARY_MODEL_PROVIDER=openai
```

### Infrastructure (for local development)

```bash
REDIS_HOST=localhost
REDIS_PORT=6379
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
```

### Feature Flags

```bash
ENABLE_SELF_HEALING=true
ENABLE_FUZZY_VERIFICATION=true
ENABLE_RISK_BASED_PRIORITIZATION=true
ENABLE_CONTEXT_AWARE_TESTING=true
```

## Adding New Agents

1. Create directory under `agents/`
2. Implement agent class using CrewAI; extend `BaseTool` for custom tools
3. Add a Dockerfile (follow existing pattern: Python 3.11-slim, PYTHONPATH=/app)
4. Add service to `docker-compose.yml`
5. Add Kubernetes manifest in `k8s/manifests/` or update Helm chart template
6. Add scenario + routing in `agents/manager/qa_manager.py`
7. Integrate with WebGUI in `webgui/app.py`

## Common Development Tasks

### Restart a Single Agent

```bash
# In Docker
docker-compose restart qa-manager

# Or rebuild and restart
docker-compose up --build -d qa-manager
```

### Add Custom Test Data

```bash
# Place files in shared/data directory
mkdir -p shared/data
cp my_test_data.csv shared/data/
```

### Configure New LLM Provider

Edit `config/models.json`:

```json
{
  "providers": {
    "anthropic": {
      "api_base": "https://api.anthropic.com",
      "models": ["claude-3-opus-20240229"],
      "auth": {"api_key": "${ANTHROPIC_API_KEY}"}
    }
  }
}
```

## Troubleshooting

### Port Conflicts

```bash
# Check what's using required ports
netstat -tulpn | grep -E ':8000|:6379|:5672'

# Change ports in .env if needed
WEBGUI_PORT=8001
REDIS_PORT=6380
RABBITMQ_PORT=5673
```

### Agent Not Responding

```bash
# Check agent logs
docker-compose logs qa-manager

# Verify RabbitMQ connection
docker-compose logs rabbitmq

# Restart the agent
docker-compose restart qa-manager
```

### LLM Errors

```bash
# Verify API key is set
echo $OPENAI_API_KEY

# Test LLM connection
python -c "from openai import OpenAI; OpenAI().models.list()"
```

---

For more details, see the [Contributing Guidelines](contributing.md).
