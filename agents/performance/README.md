# Performance Agent Documentation

## Overview
The Performance Agent consolidates performance testing capabilities from four previously separate agents:
- QA Analyst (PerformanceProfilingTool)
- API Agent (APILoadTool) 
- Mobile Agent (NetworkConditionTool)
- SRE Agent (SiteReliabilityTool performance metrics)

## Capabilities

### 1. Unified Performance Profiler
- **Response Time Analysis**: Avg, P50, P95, P99, max latencies
- **Throughput Measurement**: RPS/TPS calculations
- **Reliability Metrics**: Uptime percentage, error rate analysis
- **SLA Compliance**: Automatic SLA violation detection
- **Bottleneck Identification**: Pinpoints slow endpoints and components
- **Performance Regression**: Baseline comparison and change detection
- **TLS Certificate Validation**: Expiration monitoring and security checks

### 2. Network Condition Simulator
- **Network Profiles**: 2G, 3G, 4G, WiFi, Slow WiFi simulation
- **Load Time Estimation**: Expected performance under different conditions
- **Offline Mode Testing**: Service worker and cached content validation
- **Graceful Degradation**: Application behavior under poor connectivity

## Tools

### UnifiedPerformanceProfilerTool
**Purpose**: Comprehensive performance profiling and SLA validation

**Parameters**:
- `target_config`: Dict containing base_url, endpoints, sla_config, baseline
- `load_profile`: String indicating test intensity (baseline/moderate/stress)

**Key Metrics**:
- Performance Grade (A-F)
- Health Status (healthy/degraded/unhealthy)
- SLA Compliance Status
- Bottleneck Detection
- TLS Certificate Status

### NetworkConditionSimulatorTool
**Purpose**: Test application performance under various network conditions

**Parameters**:
- `network_config`: Dict containing url and profiles to test

**Network Profiles**:
- 2G: 250kbps download, 300ms latency
- 3G: 1.5Mbps download, 100ms latency  
- 4G: 12Mbps download, 30ms latency
- WiFi: 50Mbps download, 5ms latency
- Slow WiFi: 5Mbps download, 20ms latency

## Integration

### Replaces
- `agents/analyst/qa_analyst.py` (PerformanceProfilingTool)
- `agents/api/qa_api.py` (APILoadTool)
- `agents/mobile/qa_mobile.py` (NetworkConditionTool performance parts)
- `agents/sre/qa_sre.py` (SiteReliabilityTool performance metrics)

### Maintains Compatibility
- All existing tool interfaces preserved
- Enhanced metrics combining capabilities from all four agents
- Unified scoring and reporting format

### Redis Keys
- Stores results under `performance:{session_id}:analysis`
- Publishes notifications to `manager:{session_id}:notifications`

### Celery Queue
- Uses `performance_agent` queue for task processing

## Usage Examples

### Basic Performance Analysis
```python
task_data = {
    "session_id": "session_123",
    "scenario": {
        "id": "perf_analysis",
        "target_url": "https://api.example.com",
        "load_profile": "moderate",
        "sla_config": {
            "uptime_threshold": 99.9,
            "response_time_threshold_ms": 2000
        }
    }
}
```

### Network Condition Testing
```python
network_config = {
    "url": "https://app.example.com",
    "profiles": ["4g", "wifi", "3g", "2g"]
}
```

## Performance Improvements

### Consolidation Benefits
- **40% fewer performance tools** (4 → 2)
- **Unified metrics** across all performance domains
- **Cross-domain insights** (e.g., how network conditions affect SLA compliance)
- **Reduced redundant testing** (single load test for web, API, and mobile)
- **Comprehensive reporting** with actionable optimization recommendations

### Enhanced Capabilities
- **SLA-aware testing** with automatic violation detection
- **Network condition correlation** with performance degradation
- **TLS monitoring** integrated with performance testing
- **Unified bottleneck detection** across endpoints and services
- **Comprehensive error analysis** combining 4xx/5xx with performance impact

## Migration Notes

### From QA Analyst
- PerformanceProfilingTool → UnifiedPerformanceProfilerTool
- Enhanced with SLA compliance and TLS monitoring
- Maintains all existing metrics and adds reliability measures

### From API Agent  
- APILoadTool → UnifiedPerformanceProfilerTool (endpoint testing)
- Maintains load testing capabilities with broader metrics
- Added SLA compliance and bottleneck detection

### From Mobile Agent
- NetworkConditionTool → NetworkConditionSimulatorTool
- Maintains network profiles and offline testing
- Enhanced integration with performance metrics

### From SRE Agent
- SiteReliabilityTool performance metrics → UnifiedPerformanceProfilerTool
- Maintains reliability monitoring
- Enhanced with comprehensive performance analysis

## Configuration

### Environment Variables
- `OPENAI_MODEL`: LLM model for agent reasoning (default: gpt-4o)
- `REDIS_URL`: Redis connection string
- `RABBITMQ_URL`: RabbitMQ connection string

### SLA Configuration
```python
sla_config = {
    "uptime_threshold": 99.9,  # Percentage
    "response_time_threshold_ms": 2000  # Milliseconds
}
```

### Load Profiles
- **baseline**: 1 concurrent, 5 requests per endpoint
- **moderate**: 5 concurrent, 20 requests per endpoint  
- **stress**: 10 concurrent, 50 requests per endpoint

## Docker Service

```yaml
performance:
  build:
    context: .
    dockerfile: agents/performance/Dockerfile
  environment:
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - REDIS_URL=redis://redis:6379/0
    - RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
  depends_on:
    - redis
    - rabbitmq
  volumes:
    - ./agents/performance:/app
```