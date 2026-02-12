# Agent API Reference

## Overview

This reference covers the active 6-agent system in the repository.

## Agent APIs

### QA Manager
- **File**: `agents/manager/qa_manager.py`
- **Role**: Orchestrator and task delegator
- **Tools**:
  - `TestPlanDecompositionTool` - Breaks down requirements into test plans
  - `FuzzyVerificationTool` - LLM-based quality scoring (0-1)

### Senior QA Engineer
- **File**: `agents/senior/senior_qa.py`
- **Role**: Complex scenario testing expert
- **Tools**:
  - `SelfHealingTool` - CV + semantic selector repair
  - `ModelBasedTestingTool` - FSM-based testing
  - `EdgeCaseAnalysisTool` - Boundary condition analysis

### Junior QA Worker
- **File**: `agents/junior/junior_qa.py`
- **Role**: Regression test executor
- **Tools**:
  - `RegressionTestingTool` - Executes regression suites
  - `SyntheticDataGeneratorTool` - Generates test data
  - `TestExecutionOptimizerTool` - Risk-based test ordering

### QA Analyst
- **File**: `agents/analyst/qa_analyst.py`
- **Role**: Data aggregation and reporting
- **Tools**:
  - `DataOrganizationReportingTool` - Test data aggregation
  - `SecurityAssessmentTool` - Security analysis (OWASP)
  - `PerformanceProfilingTool` - Performance analysis

### Security & Compliance Agent
- **File**: `agents/security_compliance/qa_security_compliance.py`
- **Role**: Security and regulatory compliance validation
- **Tools**:
  - `ComprehensiveSecurityAssessmentTool` - Headers/TLS/OWASP/CORS
  - `GDPRComplianceTool` - GDPR validation
  - `PCIDSSComplianceTool` - PCI DSS validation

### Performance & Resilience Agent
- **File**: `agents/performance/qa_performance.py`
- **Role**: Performance monitoring, load testing, resilience validation
- **Tools**:
  - `PerformanceMonitoringTool`
  - `LoadTestingTool`
  - `ResilienceValidationTool`

## Communication Protocols

### Redis Messaging
Agents communicate via Redis pub/sub:
- **Request Channel**: `qa_requests`
- **Response Channel**: `qa_responses`
- **Status Channel**: `agent_status`

### Message Format
```json
{
  "id": "unique-request-id",
  "agent": "agent_name",
  "tool": "tool_name",
  "parameters": {},
  "timestamp": "2026-02-11T00:00:00Z"
}
```

## REST Endpoints

### WebGUI Integration
- **Base URL**: `http://localhost:8000`
- **Agent Status**: `GET /api/agents/status`
- **Submit Task**: `POST /api/tasks`
- **Task Results**: `GET /api/tasks/{task_id}`

## Configuration

Each agent supports environment-based configuration:
- `REDIS_HOST`, `REDIS_PORT` - Redis connection
- `RABBITMQ_HOST`, `RABBITMQ_PORT` - RabbitMQ connection
- `OPENAI_API_KEY` - LLM integration
- Agent-specific environment variables per tool
