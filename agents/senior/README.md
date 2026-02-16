# Senior QA Engineer

## Overview
The Senior QA Engineer handles complex testing scenarios including self-healing UI selectors, model-based testing, edge-case analysis, and AI-driven test generation.

## Capabilities
- **Self-Healing UI Testing**: CV-based element detection with automatic selector repair
- **Model-Based Testing**: Finite State Machine (FSM) exploration for state coverage
- **Edge Case Analysis**: Boundary value analysis and corner case identification
- **AI Test Generation**: LLM-powered test case generation from requirements and code
- **Code Analysis**: Static analysis-driven test generation
- **Autonomous Test Data**: Intelligent test data generation based on schema analysis

## Tools

### SelfHealingTool
**Purpose**: Detects and repairs broken UI selectors using computer vision and semantic analysis

**Parameters**:
- `selector`: CSS/XPath selector to heal
- `action`: Action to perform (click, type, etc.)

### ModelBasedTestingTool
**Purpose**: Generates test paths from finite state machine models

**Parameters**:
- `model`: State machine definition with states and transitions
- `coverage_criteria`: Desired coverage level (state, transition, path)

### EdgeCaseAnalysisTool
**Purpose**: Identifies boundary values and edge cases for test scenarios

**Parameters**:
- `feature_spec`: Feature specification to analyze
- `input_domains`: Input parameter domains and constraints

### AITestGenerationTool
**Purpose**: Generates test cases using LLM analysis of requirements

**Parameters**:
- `requirements`: Natural language requirements
- `context`: Application context and constraints

### CodeAnalysisTestGeneratorTool
**Purpose**: Generates tests from static code analysis

**Parameters**:
- `source_code`: Code to analyze
- `test_framework`: Target test framework (pytest, unittest, etc.)

### AutonomousTestDataGeneratorTool
**Purpose**: Generates realistic test data based on schema and domain analysis

**Parameters**:
- `schema`: Data schema definition
- `constraints`: Business rules and data constraints
- `volume`: Number of records to generate

## Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_key
PRIMARY_MODEL_PROVIDER=openai
REDIS_HOST=localhost
REDIS_PORT=6379
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
ENABLE_SELF_HEALING=true
```

## Development

### Testing
```bash
pytest tests/unit/test_senior_qa_tools.py
```

### Docker Service
```yaml
senior-qa:
  build:
    context: .
    dockerfile: agents/senior/Dockerfile
  environment:
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - REDIS_HOST=redis
    - RABBITMQ_HOST=rabbitmq
  depends_on:
    - redis
    - rabbitmq
```

## Integration Points

### Redis Communication
- **Input Channels**: `senior:{session_id}:tasks`
- **Output Channels**: `senior:{session_id}:results`
- **Status Updates**: `senior:{session_id}:status`

### Delegation
Receives complex testing tasks from the QA Manager based on high complexity scores or scenarios requiring self-healing, model-based testing, or AI-driven generation.
