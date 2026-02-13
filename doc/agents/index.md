# Agent Documentation Index

## 6-Agent Architecture

### Quick Reference

| Agent | Capabilities | Primary Focus | Documentation |
|-------|--------------|---------------|---------------|
| **QA Manager** | Test planning, delegation, fuzzy verification | Orchestration | `agents/manager/qa_manager.py` |
| **Senior QA Engineer** | Self-healing UI, model-based testing, edge cases | Complex Testing | `agents/senior/senior_qa.py` |
| **Junior QA Worker** | Regression execution, data generation, optimization | Test Automation | `agents/junior/junior_qa.py` |
| **QA Analyst** | Reporting, security assessment, performance profiling | Analysis & Reporting | `agents/analyst/qa_analyst.py` |
| **Security & Compliance Agent** | OWASP, GDPR, PCI DSS | Security & Compliance | `agents/security_compliance/README.md` |
| **Performance & Resilience Agent** | Load testing, performance monitoring, resilience checks | Performance & Reliability | `agents/performance/README.md` |

---

## Agent Details

### QA Manager
**Focus**: Orchestration, test plan decomposition, delegation, fuzzy verification.

**Key tools**:
- TestPlanDecompositionTool
- FuzzyVerificationTool

### Senior QA Engineer
**Focus**: Self-healing UI, model-based testing, edge case analysis.

**Key tools**:
- SelfHealingTool
- ModelBasedTestingTool
- EdgeCaseAnalysisTool

### Junior QA Worker
**Focus**: Regression execution, synthetic data, test ordering optimization, UX testing, localization.

**Key tools**:
- RegressionTestingTool
- SyntheticDataGeneratorTool
- TestExecutionOptimizerTool
- VisualRegressionTool
- FlakyTestDetectionTool
- UXUsabilityTestingTool
- LocalizationTestingTool

### QA Analyst
**Focus**: Aggregation, reporting, security and performance analysis, traceability.

**Key tools**:
- DataOrganizationReportingTool
- SecurityAssessmentTool
- PerformanceProfilingTool
- TestTraceabilityTool

### Security & Compliance Agent
**Focus**: OWASP, GDPR, PCI DSS.

**Key tools**:
- ComprehensiveSecurityAssessmentTool
- GDPRComplianceTool
- PCIDSSComplianceTool

### Performance & Resilience Agent
**Focus**: Performance monitoring, load testing, resilience validation, advanced profiling.

**Key tools**:
- PerformanceMonitoringTool
- LoadTestingTool
- ResilienceValidationTool
- AdvancedProfilingTool

---

## Quick Deployment

```bash
# Start core services
docker-compose up -d redis rabbitmq

# Start agents + manager
docker-compose up -d qa-manager senior-qa junior-qa qa-analyst security-compliance-agent performance-agent

# Start WebGUI
docker-compose up -d webgui
```

---

## Configuration Notes

```bash
# Required
OPENAI_API_KEY=your_api_key
REDIS_HOST=redis
RABBITMQ_HOST=rabbitmq

# Optional (URL-based override)
REDIS_URL=redis://redis:6379/0
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
```

---

*Last Updated: 2026-02-13*
*Architecture: 6-Agent with Extended Testing Tools*
