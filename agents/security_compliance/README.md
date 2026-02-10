# Security & Compliance Agent Documentation

## Overview
The Security & Compliance Agent consolidates security testing and regulatory compliance capabilities from two previously separate agents:
- QA Analyst (SecurityAssessmentTool)
- Compliance Agent (GDPRComplianceTool, PCIDSSComplianceTool, AuditTrailTool, PolicyEnforcementTool)

## Capabilities

### 1. Comprehensive Security Assessment
- **HTTP Security Headers**: CSP, HSTS, X-Frame-Options, X-Content-Type-Options
- **TLS/SSL Configuration**: Certificate validation, protocol support, cipher strength
- **OWASP Top 10 Analysis**: XSS, SQL injection, broken access control detection
- **CORS Policy Validation**: Cross-origin resource sharing security
- **Information Disclosure**: Server version and technology exposure detection
- **Vulnerability Scoring**: Critical, High, Medium, Low severity classification

### 2. GDPR Compliance Validation
- **Consent Management**: Cookie banners, granular consent, withdrawal mechanisms
- **Data Handling**: Data minimization, purpose limitation, processing records
- **Right to Erasure**: Account deletion, third-party propagation, confirmation
- **Data Portability**: Machine-readable exports, complete data inclusion
- **Compliance Scoring**: Overall GDPR compliance percentage and level

### 3. PCI DSS Compliance Validation
- **Payment Flow Security**: HTTPS enforcement, PAN storage prevention
- **Cardholder Data Protection**: Data masking, access restriction, retention policies
- **Encryption Requirements**: Data at rest, data in transit, key management
- **Requirement Tracking**: Detailed PCI DSS requirement mapping

### 4. Cross-Compliance Analysis
- **Correlation Detection**: Security impacts on regulatory compliance
- **Holistic Risk Assessment**: Integrated compliance scoring
- **Executive Reporting**: Business-focused compliance summaries

## Tools

### ComprehensiveSecurityAssessmentTool
**Purpose**: Complete security vulnerability assessment and analysis

**Parameters**:
- `target`: Dict containing target URL
- `scan_profile`: String indicating scan intensity (standard/comprehensive)

**Security Checks**:
- HTTP security header validation
- TLS/SSL configuration analysis
- OWASP Top 10 vulnerability indicators
- CORS policy misconfiguration detection
- Information disclosure identification

**Output Metrics**:
- Security score (0-1)
- Risk level (low/medium/high/critical)
- Vulnerability count by severity
- Compliance status indicators

### GDPRComplianceTool
**Purpose**: Complete GDPR compliance validation

**Parameters**:
- `gdpr_config`: Dict containing GDPR-specific test configuration

**GDPR Checks**:
- Consent management (Art. 7)
- Data handling principles (Art. 5)
- Right to erasure (Art. 17)
- Data portability (Art. 20)

**Output Metrics**:
- GDPR score (0-100)
- Compliance level (compliant/mostly_compliant/non_compliant)
- Violation count and GDPR article mapping

### PCIDSSComplianceTool
**Purpose**: Complete PCI DSS compliance validation

**Parameters**:
- `pci_config`: Dict containing PCI DSS-specific test configuration

**PCI DSS Checks**:
- Payment flow security (Req 4.1)
- Cardholder data protection (Req 3.1-3.3)
- Encryption requirements (Req 3.4-3.5, 4.1)

**Output Metrics**:
- PCI DSS score (0-100)
- Compliance level (compliant/mostly_compliant/non_compliant)
- Requirement-specific violation tracking

## Integration

### Replaces
- `agents/analyst/qa_analyst.py` (SecurityAssessmentTool, DataOrganizationReportingTool security parts)
- `agents/compliance/qa_compliance.py` (All compliance tools)

### Maintains Compatibility
- All existing tool interfaces preserved
- Enhanced cross-compliance correlation analysis
- Unified scoring and risk assessment
- Integrated executive reporting

### Redis Keys
- Stores results under `security_compliance:{session_id}:audit`
- Publishes notifications to `manager:{session_id}:notifications`

### Celery Queue
- Uses `security_compliance_agent` queue for task processing

## Usage Examples

### Basic Security & Compliance Audit
```python
task_data = {
    "session_id": "session_123",
    "scenario": {
        "id": "security_compliance_audit",
        "target_url": "https://app.example.com",
        "standards": ["OWASP Top 10", "GDPR", "PCI DSS"],
        "scan_profile": "standard"
    }
}
```

### GDPR-Only Assessment
```python
gdpr_config = {
    "consent_management": True,
    "data_handling": True,
    "right_to_erasure": True,
    "data_portability": True
}
```

### PCI DSS-Only Assessment
```python
pci_config = {
    "payment_flow": True,
    "cardholder_data": True,
    "encryption": True,
    "requirement_level": "4.0"
}
```

## Enhanced Capabilities

### Cross-Compliance Correlations
- **TLS Security ↔ PCI DSS**: Weak TLS affects multiple requirements
- **Information Disclosure ↔ GDPR**: Privacy impact assessment
- **Security Headers ↔ Regulatory**: Compliance evidence generation

### Integrated Risk Assessment
- **Weighted Scoring**: Security (40%), GDPR (30%), PCI DSS (30%)
- **Risk Level Calculation**: Low/Medium/High/Critical determination
- **Executive Summaries**: Business-friendly compliance reporting

### Compliance Evidence
- **Audit Trail Generation**: Compliance verification documentation
- **Requirement Mapping**: Specific control to requirement mapping
- **Remediation Prioritization**: Risk-based improvement planning

## Migration Notes

### From QA Analyst
- SecurityAssessmentTool → ComprehensiveSecurityAssessmentTool
- Enhanced with OWASP Top 10 and CORS analysis
- Maintains all existing security checks
- Added cross-compliance correlation

### From Compliance Agent
- All compliance tools preserved and enhanced
- GDPRComplianceTool, PCIDSSComplianceTool maintained
- Added integrated reporting and scoring
- Enhanced with security correlation analysis

## Configuration

### Environment Variables
- `OPENAI_MODEL`: LLM model for agent reasoning (default: gpt-4o)
- `REDIS_URL`: Redis connection string
- `RABBITMQ_URL`: RabbitMQ connection string

### Security Scan Profiles
- **standard**: Basic security header and TLS checks
- **comprehensive**: Full OWASP Top 10 and deep analysis

### Compliance Standards
- **GDPR**: EU General Data Protection Regulation
- **PCI DSS**: Payment Card Industry Data Security Standard 4.0
- **OWASP Top 10**: 2021 web application security risks

## Scoring & Risk Assessment

### Security Score Calculation
- Base score: 1.0 (perfect security)
- Deductions: Critical (0.15), High (0.10), Medium (0.05), Low (0.02)
- Risk levels: ≥0.9 (Low), ≥0.7 (Medium), ≥0.5 (High), <0.5 (Critical)

### Compliance Score Calculation
- Weighted average: Security (40%), GDPR (30%), PCI DSS (30%)
- Overall risk assessment based on combined score
- Executive summary generation for business stakeholders

## Docker Service

```yaml
security_compliance:
  build:
    context: .
    dockerfile: agents/security_compliance/Dockerfile
  environment:
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - REDIS_URL=redis://redis:6379/0
    - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
  depends_on:
    - redis
    - rabbitmq
  volumes:
    - ./agents/security_compliance:/app
```

## Benefits of Consolidation

### Efficiency Gains
- **33% reduction** in security/compliance agents (2 → 1)
- **Unified security assessment** across all compliance standards
- **Cross-compliance correlation** identifies systemic issues
- **Single audit report** covering all regulatory requirements

### Enhanced Capabilities
- **Integrated risk scoring** combining security and compliance
- **Executive reporting** for business stakeholders
- **Evidence generation** for regulatory audits
- **Holistic remediation planning** addressing root causes

### Operational Improvements
- **Reduced redundant testing** across security domains
- **Streamlined audit preparation** with unified reporting
- **Improved compliance tracking** with integrated scoring
- **Better resource utilization** through consolidated analysis