# Security & Compliance Agent

## Overview
The Security & Compliance Agent handles security testing (OWASP, penetration testing), compliance validation (GDPR, PCI DSS, SOC 2, ISO 27001, HIPAA), and audit trail management.

## Capabilities
- **Security Assessment**: Comprehensive security analysis including headers, TLS, CORS, OWASP indicators
- **GDPR Compliance**: Consent management, data handling, erasure, and portability validation
- **PCI DSS Compliance**: Payment flow security, cardholder data protection, encryption checks
- **SOC 2 Compliance**: Security, availability, processing integrity, confidentiality, and privacy controls
- **ISO 27001 Compliance**: Information security policies, risk management, and Annex A controls
- **HIPAA Compliance**: Privacy Rule, Security Rule, and Breach Notification validation

## Tools

### ComprehensiveSecurityAssessmentTool
**Purpose**: Complete security analysis including headers, TLS, OWASP indicators, CORS, and information disclosure

**Parameters**:
- `target`: Target configuration with URL and scan parameters
- `scan_profile`: Scan depth (quick, standard, thorough)

### GDPRComplianceTool
**Purpose**: GDPR compliance validation including consent management and data handling

**Parameters**:
- `target`: Application target configuration
- `scope`: GDPR articles and requirements to validate

### PCIDSSComplianceTool
**Purpose**: PCI DSS validation including payment flow security and encryption

**Parameters**:
- `target`: Application target configuration
- `pci_level`: PCI compliance level (1-4)

### SOC2ComplianceTool
**Purpose**: SOC 2 Type II validation across trust service criteria

**Parameters**:
- `target`: Application target configuration
- `trust_criteria`: Trust service criteria to evaluate

### ISO27001ComplianceTool
**Purpose**: ISO/IEC 27001:2022 validation including Annex A controls

**Parameters**:
- `target`: Application target configuration
- `annex_controls`: Specific Annex A controls to validate

### HIPAAComplianceTool
**Purpose**: HIPAA validation including Privacy, Security, and Breach Notification rules

**Parameters**:
- `target`: Application target configuration
- `rule_scope`: HIPAA rules to validate

## Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_key
PRIMARY_MODEL_PROVIDER=openai
REDIS_HOST=localhost
REDIS_PORT=6379
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
```

## Development

### Testing
```bash
pytest tests/unit/test_security_compliance_tools.py
```

### Docker Service
```yaml
security-compliance-agent:
  build:
    context: .
    dockerfile: agents/security_compliance/Dockerfile
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
- **Input Channels**: `security:{session_id}:tasks`
- **Output Channels**: `security:{session_id}:results`
- **Status Updates**: `security:{session_id}:status`

### Delegation
Receives security and compliance testing tasks from the QA Manager. All tasks involving OWASP testing, compliance validation, or security scanning are routed to this agent.
