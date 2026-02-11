# QA Analyst

## Overview
The QA Analyst is responsible for aggregating test data from all agents, performing comprehensive security assessments, profiling performance metrics, and generating structured reports with release readiness verdicts.

## Capabilities
- **Data Aggregation**: Collects and organizes test results from all QA agents
- **Security Assessment**: Performs security analysis including OWASP indicators, TLS validation, and header analysis
- **Performance Profiling**: Analyzes latency, throughput, bottlenecks, and performance regressions
- **Report Generation**: Creates comprehensive cross-cutting reports with release readiness verdicts

## Tools

### DataOrganizationReportingTool
**Purpose**: Aggregates test results and generates structured QA reports

**Parameters**:
- `session_id`: Unique session identifier
- `raw_results`: Raw test result data dictionary

**Capabilities**:
- Collects results from Senior and Junior agents
- Categorizes findings by severity (critical, high, medium, low)
- Calculates test coverage metrics
- Generates executive summary reports

### SecurityAssessmentTool  
**Purpose**: Performs comprehensive security analysis

**Parameters**:
- `target_url`: Target application URL
- `scan_type`: Type of security scan (basic, comprehensive, owasp)

**Security Checks**:
- HTTP header analysis (security headers, CSP, HSTS)
- TLS certificate validation and expiration
- OWASP Top 10 vulnerability indicators
- Authentication and authorization testing
- Input validation assessment

### PerformanceProfilingTool
**Purpose**: Analyzes application performance characteristics

**Parameters**:
- `target_config`: Target configuration with URLs and endpoints
- `load_profile`: Test intensity level (baseline, moderate, stress)

**Performance Metrics**:
- Response time analysis (avg, P50, P95, P99)
- Throughput measurement (RPS/TPS)
- Error rate analysis and bottleneck identification
- Performance regression detection
- SLA compliance monitoring

## Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_key
PRIMARY_MODEL_PROVIDER=openai
REDIS_HOST=localhost
REDIS_PORT=6379
RABBITMQ_HOST=localhost  
RABBITMQ_PORT=5672
ENABLE_SECURITY_ANALYSIS=true
ENABLE_PERFORMANCE_PROFILING=true
```

### Tool Configuration
```python
# Security scan configuration
security_config = {
    "headers_to_check": [
        "X-Frame-Options", "X-XSS-Protection", "X-Content-Type-Options",
        "Strict-Transport-Security", "Content-Security-Policy"
    ],
    "owasp_checks": true,
    "tls_validation": true
}

# Performance profiling configuration  
performance_config = {
    "response_time_threshold_ms": 2000,
    "error_rate_threshold_percent": 1.0,
    "throughput_threshold_rps": 100
}
```

## Usage Examples

### Basic Test Data Aggregation
```python
analyst = QAAnalyst()

result = analyst.data_organization_tool._run(
    session_id="session_123",
    raw_results={"test_results": [...]}
)
```

### Security Assessment
```python
result = analyst.security_assessment_tool._run(
    target_url="https://app.example.com",
    scan_type="comprehensive"
)
```

### Performance Profiling
```python
target_config = {
    "base_url": "https://api.example.com",
    "endpoints": ["/users", "/orders", "/products"],
    "sla_config": {"response_time_threshold_ms": 1000}
}

result = analyst.performance_profiling_tool._run(
    target_config=target_config,
    load_profile="moderate"
)
```

## Development

### Local Development Setup
```bash
cd agents/analyst
python -m qa_analyst
```

### Testing
```bash
# Run unit tests
pytest tests/unit/test_qa_analyst_tools.py

# Run integration tests
pytest tests/integration/test_qa_analyst_integration.py
```

### Docker Service
```yaml
qa-analyst:
  build:
    context: .
    dockerfile: agents/analyst/Dockerfile
  environment:
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - REDIS_HOST=redis
    - RABBITMQ_HOST=rabbitmq
  depends_on:
    - redis
    - rabbitmq
  volumes:
    - ./agents/analyst:/app
```

## Integration Points

### Redis Communication
- **Input Channels**: `senior:{session_id}`, `junior:{session_id}`
- **Output Channels**: `analyst:{session_id}`, `manager:{session_id}:notifications`
- **Data Storage**: `analyst:{session_id}:reports`, `analyst:{session_id}:security`, `analyst:{session_id}:performance`

### CrewAI Integration
The QA Analyst works as part of the CrewAI agent ecosystem:
- Receives delegated tasks from QA Manager
- Coordinates with Senior QA and Junior QA agents
- Provides consolidated analysis and recommendations

### LLM Integration
Enhanced with LLM services for intelligent analysis:
- `llm_service.analyze_security()` for advanced security insights
- `llm_service.profile_performance()` for performance bottleneck analysis
- `llm_service.generate_summary()` for executive report generation

## Monitoring and Health

### Health Check Endpoint
```bash
curl http://localhost:8001/api/analyst/health
```

### Metrics Collection
- Reports processed per session
- Security assessment completion time
- Performance profiling duration
- LLM service response times

### Logging
Key log categories:
- `INFO`: Task completion, data aggregation
- `WARN`: Security issues, performance degradation
- `ERROR`: LLM service failures, data processing errors