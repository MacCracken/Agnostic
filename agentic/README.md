# 🤖 Agentic QA Team System

A containerized, multi-agent QA system powered by CrewAI that orchestrates intelligent testing workflows with advanced self-healing, fuzzy verification, and risk-based prioritization capabilities.

## 🌟 Key Features

### 🏗️ Multi-Agent Architecture
- **QA Manager (Orchestrator)**: Decomposes requirements, delegates tasks, performs fuzzy verification
- **Senior QA Engineer**: Self-healing scripts, complex edge-case analysis, model-based testing (MBT)
- **Junior QA Worker**: Regression testing, automated root cause detection, synthetic data generation

### 🚀 Advanced Testing Capabilities
- **Agentic Self-Healing**: Computer vision + semantic analysis for failed UI selectors
- **Fuzzy Verification**: LLM-based quality assessment beyond binary pass/fail
- **Risk-Based Prioritization**: ML-driven test ordering based on code changes and historical data
- **Context-Aware Exploratory Testing**: Dynamic scenario generation based on application context

### 🐳 Containerized Deployment
- Isolated Docker containers for each agent
- Redis/RabbitMQ communication bus
- Chainlit-based WebGUI for human-in-the-loop interaction

## 📋 System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   QA Manager    │    │  Senior QA Eng  │    │  Junior QA Wrk  │
│   (Orchestrator)│    │   (Expert)      │    │   (Executor)   │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │   Redis + RabbitMQ Bus    │
                    │   (State & Communication) │
                    └─────────────┬─────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │      Chainlit WebGUI     │
                    │   (Human-in-the-Loop)     │
                    └───────────────────────────┘
```

## 🛠️ Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- OpenAI API key (for LLM capabilities)
- Git (for code change analysis)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd agentic-qa-system
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your configuration
nano .env
```

Required environment variables:
```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
REDIS_URL=redis://redis:6379/0
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
```

### 3. Launch the System

```bash
# Build and start all containers
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

### 4. Access the WebGUI

Open your browser and navigate to:
```
http://localhost:8000
```

### 5. Start Your First Agentic QA Sprint

1. **Upload a PR/Feature Document** or describe your testing requirements
2. **Watch the agents collaborate** in real-time
3. **Monitor the reasoning trace** to see how decisions are made
4. **Review the fuzzy verification results** with business alignment scores

## 📖 Detailed Usage

### WebGUI Interface

The Chainlit-based WebGUI provides:

- **Chat Interface**: Natural language interaction with the QA team
- **File Upload**: Support for PR documents, feature specs, and test requirements
- **Live Monitoring**: Real-time status updates and reasoning traces
- **Results Dashboard**: Comprehensive test results with fuzzy verification scores

### Available Commands

- **Describe testing requirements**: Start a new test plan (e.g., "Test the e-commerce checkout flow")
- **'status'**: Check current session progress
- **'trace'**: View detailed reasoning trace and agent collaboration
- **'help'**: Show available commands

### Agent Workflows

#### QA Manager (Orchestrator)
1. **Requirement Analysis**: Decomposes user requirements into test plans
2. **Task Delegation**: Assigns scenarios to Senior/Junior agents based on complexity
3. **Fuzzy Verification**: Performs final quality assessment with business alignment
4. **Result Synthesis**: Compiles comprehensive test reports

#### Senior QA Engineer (Expert)
1. **Self-Healing Analysis**: Identifies and repairs failed UI selectors
2. **Model-Based Testing**: Creates state machine models for complex flows
3. **Edge Case Analysis**: Identifies boundary conditions and error scenarios
4. **Complex Problem Solving**: Handles sophisticated testing challenges

#### Junior QA Worker (Executor)
1. **Regression Testing**: Executes comprehensive test suites
2. **Root Cause Detection**: Automatically analyzes test failures
3. **Synthetic Data Generation**: Creates realistic test datasets
4. **Test Optimization**: Prioritizes execution order based on risk

## 🔧 Advanced Configuration

### Custom Agent Prompts

Edit agent configurations in `agents/manager/`, `agents/senior/`, and `agents/junior/`:

```python
# Example: Customizing QA Manager
self.agent = Agent(
    role='QA Manager & Test Orchestrator',
    goal='Your custom goal here',
    backstory='Your custom backstory here',
    # ... other configuration
)
```

### Advanced Testing Modules

The system includes advanced testing capabilities in `advanced_testing/`:

- **Self-Healing**: `self_healing_fuzzy_verification.py`
- **Risk Prioritization**: `risk_prioritization_exploratory.py`

### Custom Tools

Add new CrewAI tools by extending the `BaseTool` class:

```python
from crewai.tools import BaseTool

class CustomTestingTool(BaseTool):
    name: str = "Custom Tool"
    description: str = "Tool description"
    
    def _run(self, input_data: str) -> Dict[str, Any]:
        # Your custom logic here
        return {"result": "success"}
```

## 📊 Monitoring & Debugging

### Container Status

```bash
# Check all containers
docker-compose ps

# View logs for specific agent
docker-compose logs qa-manager
docker-compose logs senior-qa
docker-compose logs junior-qa
docker-compose logs webgui
```

### Redis Inspection

```bash
# Connect to Redis CLI
docker-compose exec redis redis-cli

# View session data
KEYS session:*
GET session:your_session_id:requirements
```

### RabbitMQ Management

Access the RabbitMQ management interface:
```
http://localhost:15672
Username: guest
Password: guest
```

## 🧪 Example Workflows

### E-commerce Testing

```text
User: "Test the complete e-commerce checkout flow including payment integration"

QA Manager: Creates test plan with scenarios:
- 🔴 Critical: Payment processing (Senior QA)
- 🟠 High: Cart management (Junior QA)  
- 🟡 Medium: User authentication (Senior QA)
- 🟢 Low: Product browsing (Junior QA)
```

### API Testing

```text
User: "Verify the REST API endpoints for user management"

System generates:
- Functional API tests (Junior QA)
- Security vulnerability tests (Senior QA)
- Performance load tests (Junior QA)
- Integration edge cases (Senior QA)
```

### Regression Testing

```text
User: "Run regression tests for the latest PR"

System:
- Analyzes code changes
- Prioritizes affected tests
- Executes optimized test suite
- Provides root cause analysis for failures
```

## 🔍 Troubleshooting

### Common Issues

**Container won't start:**
```bash
# Check Docker logs
docker-compose logs <service-name>

# Rebuild containers
docker-compose down
docker-compose up --build
```

**Redis connection errors:**
```bash
# Restart Redis service
docker-compose restart redis

# Check network connectivity
docker-compose exec qa-manager ping redis
```

**OpenAI API errors:**
- Verify API key in `.env` file
- Check API quota and rate limits
- Ensure network connectivity to OpenAI

### Performance Optimization

**For large test suites:**
- Enable risk-based prioritization
- Use parallel execution where possible
- Monitor resource usage in Docker containers

**For faster response times:**
- Use `gpt-3.5-turbo` for non-critical tasks
- Enable response caching in Redis
- Optimize agent tool usage

## 🤝 Contributing

### Development Setup

```bash
# Install Python dependencies locally
pip install -r requirements.txt

# Run tests locally
pytest tests/

# Start development environment
docker-compose -f docker-compose.dev.yml up
```

### Code Structure

```
agentic-qa-system/
├── agents/                 # Agent implementations
│   ├── manager/           # QA Manager agent
│   ├── senior/            # Senior QA Engineer
│   └── junior/            # Junior QA Worker
├── advanced_testing/     # Advanced testing modules
├── webgui/               # Chainlit web interface
├── config/               # Configuration files
├── examples/             # Example test scenarios
├── docs/                 # Documentation
├── docker-compose.yml    # Container orchestration
└── requirements.txt      # Python dependencies
```

### Adding New Agents

1. Create agent directory in `agents/`
2. Implement agent class with CrewAI
3. Create Dockerfile for containerization
4. Update `docker-compose.yml`
5. Add agent to WebGUI integration

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **CrewAI**: Multi-agent orchestration framework
- **LangChain**: LLM integration and tooling
- **Chainlit**: Conversational AI interface
- **Playwright**: Browser automation
- **OpenAI**: GPT models for intelligent reasoning

## 📞 Support

For issues and questions:

1. Check the troubleshooting section above
2. Review container logs for error details
3. Open an issue on the project repository
4. Join our community discussions

---

**🚀 Ready to revolutionize your QA process with AI agents? Start your first Agentic QA Sprint today!**