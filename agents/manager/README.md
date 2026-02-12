# QA Manager

## Overview
The QA Manager serves as the orchestrator of the QA system, responsible for decomposing requirements into test plans, delegating tasks by complexity, performing fuzzy verification, and synthesizing comprehensive reports.

## Capabilities
- **Test Plan Decomposition**: Breaks down complex requirements into structured test plans
- **Task Delegation**: Intelligently delegates tasks to appropriate specialized agents
- **Fuzzy Verification**: LLM-based quality scoring with 0-1 confidence ratings
- **Risk Assessment**: Evaluates test risk levels and prioritizes accordingly
- **Report Synthesis**: Combines inputs from all agents into executive summaries

## Tools

### TestPlanDecompositionTool
**Purpose**: Decomposes requirements into detailed test plans

**Parameters**:
- `requirements`: String or dict containing test requirements
- `context`: Additional context about the application type and complexity

**Capabilities**:
- Analyzes requirements and identifies test scenarios
- Breaks down complex features into testable components
- Identifies dependencies between test cases
- Generates structured test plans with priorities

### FuzzyVerificationTool
**Purpose**: Performs LLM-based quality verification with confidence scoring

**Parameters**:
- `test_result`: Result data from test execution
- `expectations`: Expected outcomes and acceptance criteria
- `context`: Additional context for verification

**Scoring System**:
- **0.0-0.2**: Significant issues or failures
- **0.3-0.5**: Partial success with notable concerns
- **0.6-0.8**: Good quality with minor issues
- **0.9-1.0**: Excellent quality meeting all expectations

### RiskAssessmentTool
**Purpose**: Evaluates and prioritizes test scenarios based on risk factors

**Parameters**:
- `test_scenarios`: List of test scenarios to assess
- `code_changes`: List of modified code components
- `business_context`: Business impact and priority information

**Risk Factors**:
- Code change complexity and scope
- Business criticality of features
- Historical defect density
- User-facing vs internal components

## Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_key
PRIMARY_MODEL_PROVIDER=openai
REDIS_HOST=localhost
REDIS_PORT=6379
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
ENABLE_FUZZY_VERIFICATION=true
ENABLE_RISK_BASED_PRIORITIZATION=true
```

### LLM Configuration
```python
# LLM model settings
llm_config = {
    "model": "gpt-4",
    "temperature": 0.3,
    "max_tokens": 2000,
    "timeout": 30
}

# Fuzzy verification thresholds
verification_thresholds = {
    "passing_threshold": 0.7,
    "warning_threshold": 0.5,
    "critical_threshold": 0.3
}
```

## Usage Examples

### Test Plan Decomposition
```python
manager = QAManager()

result = manager.test_plan_tool._run(
    requirements="User authentication flow with social login options",
    context={
        "app_type": "web",
        "complexity": "medium",
        "priority": "high"
    }
)
```

### Fuzzy Verification
```python
result = manager.fuzzy_verification_tool._run(
    test_result={"status": "passed", "warnings": ["minor UI issues"]},
    expectations="All login methods should work seamlessly",
    context={"feature": "authentication", "environment": "production"}
)
```

### Risk Assessment
```python
scenarios = [
    {"id": "login-success", "description": "Successful login flow"},
    {"id": "login-failure", "description": "Failed login handling"}
]

result = manager.risk_assessment_tool._run(
    test_scenarios=scenarios,
    code_changes=["auth.py", "models.py", "views/login.py"],
    business_context={"criticality": "high", "user_impact": "direct"}
)
```

## Development

### Local Development Setup
```bash
cd agents/manager
python -m qa_manager
```

### Testing
```bash
# Run unit tests
pytest tests/unit/test_qa_manager_tools.py

# Run integration tests
pytest tests/integration/test_qa_manager_integration.py
```

### Docker Service
```yaml
qa-manager:
  build:
    context: .
    dockerfile: agents/manager/Dockerfile
  environment:
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - REDIS_HOST=redis
    - RABBITMQ_HOST=rabbitmq
  depends_on:
    - redis
    - rabbitmq
  volumes:
    - ./agents/manager:/app
```

## Integration Points

### Redis Communication
- **Input Channels**: `manager:{session_id}:tasks`
- **Output Channels**: `senior:{session_id}`, `junior:{session_id}`, `analyst:{session_id}`
- **Status Updates**: `manager:{session_id}:status`
- **Notifications**: `manager:{session_id}:notifications`

### Agent Delegation Logic
```python
delegation_rules = {
    "high_complexity": "senior_qa",
    "regression_testing": "junior_qa",
    "analysis_reporting": "qa_analyst",
    "performance_testing": "performance_agent",
    "security_compliance": "security_compliance_agent"
}
```

### CrewAI Integration
- Acts as the primary coordinator in CrewAI workflows
- Receives high-level requirements from WebGUI or external systems
- Coordinates task execution across specialized agents
- Synthesizes results into comprehensive reports

## LLM Integration

### Enhanced Intelligence
The QA Manager uses LLM services for:
- **Requirement Analysis**: Intelligent parsing of complex requirements
- **Test Scenario Generation**: Creative test case design
- **Quality Assessment**: Nuanced quality evaluation beyond pass/fail
- **Risk Prediction**: Proactive risk identification based on patterns

### Fuzzy Verification Process
1. Analyzes test results against expectations
2. Considers context and business impact
3. Evaluates quality on continuous scale
4. Provides confidence scores and reasoning
5. Identifies areas needing attention

## Monitoring and Health

### Health Check Endpoint
```bash
curl http://localhost:8000/api/manager/health
```

### Key Metrics
- Test plans generated per session
- Delegation accuracy and efficiency
- Fuzzy verification confidence scores
- Task completion rates and times

### Performance Monitoring
- LLM response times and token usage
- Agent coordination latency
- Report generation time
- Error rates and fallback usage
