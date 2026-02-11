# Agent API Reference

## Overview

This section provides comprehensive API documentation for all QA agents in the system.

## Agent APIs

### QA Manager
- **File**: `agents/manager/qa_manager.py`
- **Role**: Orchestrator and task delegator
- **Tools**:
  - `TestPlanDecompositionTool` - Breaks down requirements into test plans
  - `FuzzyVerificationTool` - LLM-based quality scoring (0-1)
  - `RiskAssessmentTool` - Evaluates test risk levels
- **API**: Accepts test requirements via REST or Redis messaging

### Senior QA Engineer  
- **File**: `agents/senior/senior_qa.py`
- **Role**: Complex scenario testing expert
- **Tools**:
  - `SelfHealingTool` - CV + semantic selector repair
  - `ModelBasedTestingTool` - FSM-based testing
  - `EdgeCaseAnalysisTool` - Boundary condition analysis
- **API**: Handles complex test scenarios delegated by QA Manager

### Junior QA Worker
- **File**: `agents/junior/junior_qa.py` 
- **Role**: Regression test executor
- **Tools**:
  - `RegressionTestingTool` - Executes regression suites
  - `SyntheticDataGeneratorTool` - Generates test data
  - `TestExecutionOptimizerTool` - Risk-based test ordering
  - `VisualRegressionTool` - Visual comparison testing
- **API**: Processes bulk test execution requests

### QA Analyst
- **File**: `agents/analyst/qa_analyst.py`
- **Role**: Data aggregation and reporting
- **Tools**:
  - `DataOrganizationReportingTool` - Test data aggregation
  - `SecurityAssessmentTool` - Security analysis (OWASP)
  - `PerformanceProfilingTool` - Performance analysis
- **API**: Generates comprehensive reports and assessments

### Site Reliability Engineer
- **File**: `agents/sre/qa_sre.py`
- **Role**: Infrastructure and reliability testing
- **Tools**:
  - `SiteReliabilityTool` - Health checks and SLA monitoring
  - `DatabaseTestingTool` - Database resilience testing
  - `InfrastructureHealthTool` - Infrastructure validation
  - `IncidentResponseTool` - Incident management
- **API**: Monitors and tests system reliability

### Accessibility Tester
- **File**: `agents/accessibility/qa_accessibility.py`
- **Role**: WCAG compliance testing
- **Tools**:
  - `WCAGComplianceTool` - WCAG 2.1 AA/AAA auditing
  - `ScreenReaderTool` - Screen reader compatibility
  - `KeyboardNavigationTool` - Keyboard navigation testing
  - `ColorContrastTool` - Color contrast validation
- **API**: Performs accessibility compliance testing

### API Integration Engineer
- **File**: `agents/api/qa_api.py`
- **Role**: API validation and testing
- **Tools**:
  - `APISchemaValidationTool` - OpenAPI spec validation
  - `ContractTestingTool` - Consumer/provider contract testing
  - `APIVersioningTool` - API version compatibility
  - `APILoadTool` - Endpoint load testing
- **API**: Validates API specifications and performance

### Mobile/Device QA
- **File**: `agents/mobile/qa_mobile.py`
- **Role**: Mobile and device compatibility testing
- **Tools**:
  - `ResponsiveTestingTool` - Responsive design validation
  - `DeviceCompatibilityTool` - Device matrix testing
  - `NetworkConditionTool` - Network simulation
  - `MobileUXTool` - Mobile UX pattern testing
- **API**: Tests mobile compatibility across devices

### Compliance Tester
- **File**: `agents/compliance/qa_compliance.py`
- **Role**: Regulatory compliance validation
- **Tools**:
  - `GDPRComplianceTool` - GDPR compliance checking
  - `PCIDSSComplianceTool` - PCI DSS validation
  - `AuditTrailTool` - Audit trail integrity
  - `PolicyEnforcementTool` - Policy compliance
- **API**: Validates regulatory compliance requirements

### Chaos Engineer
- **File**: `agents/chaos/qa_chaos.py`
- **Role**: Failure injection and resilience testing
- **Tools**:
  - `ServiceFailureTool` - Service failure injection
  - `NetworkPartitionTool` - Network partition simulation
  - `ResourceExhaustionTool` - Resource exhaustion testing
  - `RecoveryValidationTool` - Recovery mechanism validation
- **API**: Performs chaos engineering experiments

## Communication Protocols

### Redis Messaging
All agents communicate via Redis pub/sub:
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
  "timestamp": "2026-02-10T23:30:00Z"
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