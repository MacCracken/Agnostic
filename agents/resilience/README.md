# Resilience Agent Documentation

## Overview
The Resilience Agent consolidates infrastructure monitoring and chaos engineering capabilities from three previously separate agents:
- SRE Agent (SiteReliabilityTool, DatabaseTestingTool, InfrastructureHealthTool)
- Chaos Agent (ServiceFailureTool, NetworkPartitionTool, ResourceExhaustionTool, RecoveryValidationTool)
- Enhanced with cross-domain correlation and unified resilience scoring

## Capabilities

### 1. Site Reliability Monitoring
- **Uptime & Availability**: Continuous health checks and availability tracking
- **Latency Analysis**: P50, P95, P99 latency percentiles
- **Error Rate Monitoring**: 4xx and 5xx error rate tracking
- **SLA Compliance**: Automatic SLA violation detection and reporting
- **TLS Certificate Validation**: Expiration monitoring and security checks
- **Reliability Risk Assessment**: Proactive risk identification and scoring

### 2. Database Resilience Testing
- **Connection Pool Testing**: Load testing of database connection pools
- **Transaction Consistency**: ACID property validation
- **Migration Validation**: Database schema and migration state verification
- **Query Performance**: Performance profiling and slow query identification
- **Database Health**: Overall database health assessment

### 3. Chaos Engineering
- **Service Failure Injection**: Simulating service unavailability and dependency failures
- **Network Partition Simulation**: Latency injection, packet loss, DNS failure testing
- **Resource Exhaustion Testing**: Memory pressure, CPU saturation, disk exhaustion scenarios
- **Recovery Mechanism Validation**: Automatic recovery and MTTR measurement
- **Circuit Breaker Testing**: Circuit breaker activation and fallback validation

### 4. Infrastructure Health Monitoring
- **DNS Resolution**: DNS server performance and failure detection
- **Service Discovery**: Service availability and health endpoint monitoring
- **Container Health**: Container status, restart policies, and resource usage
- **Resource Utilization**: Disk, memory, and CPU monitoring with alerting
- **Infrastructure Correlation**: Cross-domain issue correlation and analysis

### 5. Cross-Domain Resilience Analysis
- **Reliability ↔ Database Correlation**: Database impact on site reliability
- **Chaos ↔ Infrastructure Correlation**: Infrastructure impact on resilience
- **Reliability ↔ Chaos Correlation**: Chaos test results and reliability impact
- **Unified Scoring**: Weighted resilience scoring across all domains
- **Executive Reporting**: Business-focused resilience summaries

## Tools

### SiteReliabilityTool
**Purpose**: Comprehensive site reliability monitoring and SLA compliance

**Parameters**:
- `target_url`: Target URL for monitoring
- `sla_config`: SLA configuration including thresholds and probe count

**Metrics**:
- Uptime percentage and availability tracking
- Latency percentiles (P50, P95, P99)
- Error rates by category (4xx, 5xx)
- SLA compliance status and violations
- TLS certificate validation and expiration monitoring

### DatabaseTestingTool
**Purpose**: Database resilience and performance validation

**Parameters**:
- `db_config`: Database connection and test configuration

**Capabilities**:
- Connection pool performance testing
- Transaction consistency validation
- Migration state verification
- Query performance profiling
- Database health assessment

### ChaosFailureInjectorTool
**Purpose**: Controlled failure injection and resilience testing

**Parameters**:
- `failure_config`: Services, failure types, and test configuration

**Chaos Scenarios**:
- Service failure injection with circuit breaker testing
- Network partition simulation with latency/packet loss
- Resource exhaustion testing (memory, CPU, disk)
- Recovery mechanism validation with MTTR measurement

### InfrastructureHealthTool
**Purpose**: Infrastructure health and resource monitoring

**Parameters**:
- `infra_config`: Services, DNS targets, and container configuration

**Monitoring Areas**:
- DNS resolution performance and failures
- Service discovery and availability
- Container health and status
- System resource utilization with alerting

## Integration

### Replaces
- `agents/sre/qa_sre.py` (SiteReliabilityTool, DatabaseTestingTool, InfrastructureHealthTool)
- `agents/chaos/qa_chaos.py` (All chaos engineering tools)
- Enhanced from original SRE and Chaos agents with cross-domain analysis

### Maintains Compatibility
- All existing tool interfaces preserved
- Enhanced with cross-domain correlation and unified scoring
- Improved executive reporting and business metrics
- Integrated resilience assessment across all infrastructure domains

### Redis Keys
- Stores results under `resilience:{session_id}:analysis`
- Publishes notifications to `manager:{session_id}:notifications`

### Celery Queue
- Uses `resilience_agent` queue for task processing

## Usage Examples

### Basic Resilience Analysis
```python
task_data = {
    "session_id": "session_123",
    "scenario": {
        "id": "resilience_analysis",
        "target_url": "https://api.example.com",
        "test_scope": "full_resilience_suite",
        "sla_config": {
            "num_probes": 10,
            "uptime_threshold": 99.9,
            "response_time_threshold_ms": 2000
        }
    }
}
```

### Chaos Testing Configuration
```python
chaos_config = {
    "services": [
        {"name": "database", "host": "db.example.com", "port": 5432},
        {"name": "cache", "host": "redis.example.com", "port": 6379}
    ],
    "failure_types": ["service_failure", "network_partition", "resource_exhaustion"],
    "target_mttr_seconds": 300
}
```

### Infrastructure Monitoring
```python
infra_config = {
    "services": [
        {"name": "api", "host": "api.example.com", "port": 8080},
        {"name": "database", "host": "db.example.com", "port": 5432}
    ],
    "dns_targets": ["api.example.com", "db.example.com"],
    "containers": ["api-service", "database-service", "cache-service"]
}
```

## Enhanced Capabilities

### Cross-Domain Correlation
- **Reliability-Database**: Database performance impact on site reliability
- **Chaos-Infrastructure**: Infrastructure health during chaos testing
- **Reliability-Chaos**: Chaos test results correlation with reliability metrics
- **Unified Risk Assessment**: Cross-domain risk identification and mitigation

### Unified Resilience Scoring
- **Weighted Average**: Reliability (30%), Database (20%), Chaos (30%), Infrastructure (20%)
- **Resilience Levels**: Excellent (90+), Good (75+), Moderate (60+), Poor (<60)
- **Executive Metrics**: Business-friendly resilience indicators
- **Trend Analysis**: Historical resilience tracking and improvement measurement

### Enhanced Recovery Validation
- **MTTR Measurement**: Mean Time To Recovery across failure scenarios
- **Automatic Recovery**: Container restart, service re-registration, dependency reconnection
- **Self-Healing Validation**: Circuit breaker activation and fallback mechanisms
- **Recovery Automation**: Recovery process automation and orchestration

## Migration Notes

### From SRE Agent
- All SRE tools preserved and enhanced
- SiteReliabilityTool: Enhanced with TLS monitoring
- DatabaseTestingTool: Enhanced with resilience correlation
- InfrastructureHealthTool: Enhanced with cross-domain analysis

### From Chaos Agent
- All chaos tools preserved and integrated
- ServiceFailureTool: Enhanced with circuit breaker validation
- NetworkPartitionTool: Integrated with infrastructure monitoring
- ResourceExhaustionTool: Enhanced with recovery measurement
- RecoveryValidationTool: Enhanced with MTTR tracking

## Configuration

### Environment Variables
- `OPENAI_MODEL`: LLM model for agent reasoning (default: gpt-4o)
- `REDIS_URL`: Redis connection string
- `RABBITMQ_URL`: RabbitMQ connection string

### SLA Configuration
```python
sla_config = {
    "num_probes": 10,              # Number of health checks
    "uptime_threshold": 99.9,     # Uptime percentage threshold
    "response_time_threshold_ms": 2000  # Response time threshold in milliseconds
}
```

### Chaos Test Configuration
```python
chaos_config = {
    "services": ["database", "cache", "api"],
    "failure_types": ["service_failure", "network_partition"],
    "test_duration": 300,          # Test duration in seconds
    "target_mttr_seconds": 300     # Target recovery time
}
```

## Scoring & Metrics

### Resilience Score Calculation
- **Site Reliability**: 30% weight (healthy: 100, degraded: 70, unhealthy: 40)
- **Database Resilience**: 20% weight (healthy: 100, degraded: 70, unhealthy: 40)
- **Chaos Engineering**: 30% weight (0-100 based on resilience during failures)
- **Infrastructure Health**: 20% weight (healthy: 100, degraded: 70, unhealthy: 40)

### Resilience Levels
- **Excellent** (90+): Strong resilience with effective recovery mechanisms
- **Good** (75+): Good resilience with minor improvements needed
- **Moderate** (60+): Moderate resilience with significant improvement areas
- **Poor** (<60): Poor resilience requiring immediate attention

## Docker Service

```yaml
resilience:
  build:
    context: .
    dockerfile: agents/resilience/Dockerfile
  environment:
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - REDIS_URL=redis://redis:6379/0
    - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
  depends_on:
    - redis
    - rabbitmq
  volumes:
    - ./agents/resilience:/app
```

## Benefits of Consolidation

### Efficiency Gains
- **33% reduction** in resilience/chaos agents (3 → 1)
- **Unified resilience scoring** across all infrastructure domains
- **Cross-domain correlation** identifies systemic resilience issues
- **Single resilience dashboard** for comprehensive monitoring

### Enhanced Capabilities
- **Integrated chaos engineering** with real-time infrastructure monitoring
- **Cross-domain resilience analysis** identifies interdependent failures
- **Unified MTTR measurement** across all failure scenarios
- **Executive resilience reporting** for business stakeholders

### Operational Improvements
- **Reduced redundant monitoring** across infrastructure domains
- **Improved failure correlation** between different system components
- **Streamlined recovery processes** with unified monitoring
- **Better resource utilization** through consolidated analysis