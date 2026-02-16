# ADR-015: Observability Stack Integration

## Status
Accepted

## Date
2026-02-16

## Context

The system had zero observability infrastructure. All agents used `logging.basicConfig(level=logging.INFO)` with plain text. There was no way to collect or expose runtime metrics (task throughput, LLM call latency, error rates) for monitoring or alerting. Production debugging required log scraping.

## Decision

### Prometheus Metrics (`shared/metrics.py`)
- Named metric objects (Counter, Histogram, Gauge) covering tasks, LLM calls, HTTP requests, active agents, and circuit breaker state.
- **No-op fallback**: When `prometheus_client` is not installed, a `_NoOpMetric` class silently accepts all `.labels().inc()` / `.observe()` / `.set()` calls. This means callers never need to guard imports.
- Metrics exposed via `GET /api/metrics` endpoint (unauthenticated, for Prometheus scraping).

### Structured Logging (`shared/logging_config.py`)
- `configure_logging(service_name)` reads `LOG_FORMAT` (json/text) and `LOG_LEVEL` from environment variables.
- When `structlog` is installed and `LOG_FORMAT=json`, produces JSON-structured log lines.
- Otherwise, falls back to stdlib `logging.basicConfig` with a `[service_name]` prefix.

### LLM Call Instrumentation (`config/llm_integration.py`)
- All 6 async LLM methods instrumented with `LLM_CALLS_TOTAL` (counter by method+status) and `LLM_CALL_DURATION` (histogram by method).

### Optional Dependencies (`pyproject.toml`)
- New `observability` extras group: `prometheus-client>=0.20.0`, `structlog>=24.0.0`.

## Consequences

### Positive
- Prometheus scraping ready out of the box when optional deps installed
- Zero runtime cost when `prometheus_client` / `structlog` not installed (no-op pattern)
- JSON structured logging enables log aggregation (ELK, Loki) without parsing
- LLM call metrics enable latency/error dashboards and alerting

### Negative
- Metric cardinality must be managed (avoid high-cardinality label values)
- OpenTelemetry tracing deferred to a future phase

## Alternatives Considered
1. **OpenTelemetry-only**: More comprehensive but heavier; decided to start with Prometheus + structlog and add OTel later.
2. **StatsD**: Less common in Kubernetes ecosystems; Prometheus is the de facto standard.
3. **Mandatory dependencies**: Rejected — the no-op fallback keeps the core lightweight.
