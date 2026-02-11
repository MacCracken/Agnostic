# Quick Start Guide

## Overview

Get the Agentic QA Team System running in 5 minutes with this step-by-step guide.

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- OpenAI API key (for LLM features)

## 🚀 Quick Start (Docker)

### 1. Clone and Setup
```bash
git clone <repository-url>
cd agentic
cp .env.example .env
```

### 2. Configure Environment
Edit `.env` and set:
```bash
OPENAI_API_KEY=your_openai_api_key_here
PRIMARY_MODEL_PROVIDER=openai
```

### 3. Launch All Services
```bash
docker-compose up --build
```

That's it! The system will start:
- **WebGUI**: http://localhost:8000
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)
- **10 QA Agents** + **Redis** + **RabbitMQ**

### 4. Verify Installation
Open http://localhost:8000 in your browser and submit a test task.

## 🏗️ Architecture Overview

The system uses a **6-agent architecture**:

```
QA Manager (Orchestrator)    ──┐
Senior QA Engineer (Expert)   ─┤
Junior QA Worker (Executor)    ─┤
QA Analyst (Reporter)         ─┤
Site Reliability Engineer     ─┼── Redis + RabbitMQ ── WebGUI (:8000)
Accessibility Tester          ─┤
API Integration Engineer      ─┤
Mobile/Device QA              ─┤
Compliance Tester             ─┤
Chaos Engineer                ─┘
```

## 📋 First Test Task

### Submit via WebGUI
1. Go to http://localhost:8000
2. Enter your test requirements, e.g.:
   ```
   Test the user login flow with valid and invalid credentials
   ```
3. Click "Submit Task"
4. Watch the agents collaborate in real-time

### Expected Output
- QA Manager decomposes the requirement
- Senior QA designs test scenarios  
- Junior QA executes the tests
- QA Analyst generates a report
- All agents coordinate via Redis/RabbitMQ

## 🛠️ Development Setup

### Local Development (without Docker)
```bash
# Install dependencies
pip install -e .[dev,test,web,ml,browser]

# Start services
redis-server
rabbitmq-server

# Run agents in separate terminals
python -m agents.manager.qa_manager
python -m agents.analyst.qa_analyst
# ... etc

# Start WebGUI
python -m webgui.app
```

### Environment Variables
```bash
# Required
OPENAI_API_KEY=your_key_here
PRIMARY_MODEL_PROVIDER=openai

# Optional (for local development)
REDIS_HOST=localhost
RABBITMQ_HOST=localhost
ENABLE_SELF_HEALING=true
ENABLE_FUZZY_VERIFICATION=true
```

## 🧪 Running Tests

```bash
# All tests with mocks
python run_tests.py --mode all --env mock

# Unit tests only
python run_tests.py --mode unit

# Integration tests (requires Docker)
python run_tests.py --mode integration --env docker

# With coverage
python run_tests.py --mode coverage
```

## 📊 Monitoring

### Check System Health
```bash
# Agent status
curl http://localhost:8000/api/agents/status

# Redis status
docker-compose logs redis

# RabbitMQ status
curl http://localhost:15672/api/overview
```

### View Logs
```bash
# All services
docker-compose logs

# Specific agent
docker-compose logs qa-manager
docker-compose logs qa-analyst
```

## 🔧 Common Tasks

### Adding Custom Test Data
```bash
# Upload via WebGUI
# Or place in shared/data directory
docker cp my_test_data.csv agentic:/app/shared/data/
```

### Configuring New LLM Provider
Edit `config/models.json`:
```json
{
  "providers": {
    "my_provider": {
      "api_base": "https://api.myprovider.com",
      "models": ["my-model"],
      "auth": {"api_key": "${MY_API_KEY}"}
    }
  }
}
```

### Extending Agent Capabilities
1. Create new tool in `agents/{agent_name}/tools/`
2. Import and register in agent file
3. Add Docker volume mount if needed
4. Update documentation

## 🚨 Troubleshooting

### Common Issues

**Port conflicts?**
```bash
# Check what's using ports 8000, 6379, 5672
netstat -tulpn | grep ':8000\|:6379\|:5672'

# Change ports in .env
WEBGUI_PORT=8001
REDIS_PORT=6380
```

**Agent not responding?**
```bash
# Check agent logs
docker-compose logs qa-manager

# Restart specific agent
docker-compose restart qa-manager
```

**LLM errors?**
```bash
# Verify API key
echo $OPENAI_API_KEY

# Test connection
python -c "from openai import OpenAI; OpenAI().models.list()"
```

### Getting Help

- Check logs: `docker-compose logs <service-name>`
- Review docs in `docs/` directory
- Open an issue with full logs and environment details

## 📚 Next Steps

1. **Read the full documentation** in `docs/`
2. **Explore agent capabilities** in `docs/api/agents.md`
3. **Configure LLM integration** in `docs/api/llm_integration.md`
4. **Learn WebGUI API** in `docs/api/webgui.md`
5. **Review deployment options** in `DEPLOYMENT_GUIDE.md`

## 🎯 Success Metrics

Your system is working correctly when:
- ✅ All 10 agents show "active" status
- ✅ WebGUI loads at http://localhost:8000
- ✅ Test tasks complete with reports
- ✅ Redis/RabbitMQ show healthy connections
- ✅ LLM calls return structured responses

Welcome to the Agentic QA Team System! 🎉