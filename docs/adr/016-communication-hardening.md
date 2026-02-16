# ADR-016: Agent Communication Hardening

## Status
Accepted

## Date
2026-02-16

## Context

Agent communication had several reliability gaps:
- **No circuit breaker**: LLM API failures cascaded — every request waited for a timeout before falling back.
- **No Celery retries**: Failed tasks were lost (no `task_acks_late`, no retry config).
- **No graceful shutdown**: All 6 agents used bare `except KeyboardInterrupt` with no cleanup callbacks, risking data loss on SIGTERM.
- **No backoff**: The retry utility existed but wasn't wired into the system.

## Decision

### Circuit Breaker (`shared/resilience.py`)
- `CircuitBreaker` dataclass: CLOSED → OPEN (after threshold failures) → HALF_OPEN (after recovery timeout) → CLOSED (on success).
- Module-level `_llm_circuit` instance in `config/llm_integration.py` protects all 6 LLM methods. When open, methods skip the LLM call and use the existing fallback immediately.

### Retry with Exponential Backoff (`shared/resilience.py`)
- `RetryConfig` dataclass and `retry_async()` decorator for async functions.
- Configurable max retries, base delay, max delay, and exponential base.

### Celery Reliability (`config/environment.py`)
Added to `app.conf.update()`:
- `task_acks_late=True` — acknowledge after execution, not before
- `task_reject_on_worker_lost=True` — re-queue tasks when workers crash
- `task_default_retry_delay=60` — 60-second retry delay
- `task_max_retries=3` — max 3 retries per task
- `worker_cancel_long_running_tasks_on_connection_loss=True`

### Graceful Shutdown (`shared/resilience.py`)
- `GracefulShutdown` async context manager registers SIGTERM/SIGINT handlers.
- Provides `should_stop` property and `add_cleanup()` for resource cleanup.
- Replaces identical try/while/except pattern in all 6 agent `main()` functions.

## Consequences

### Positive
- LLM outages no longer block every request (circuit breaker fast-fails)
- Celery tasks survive worker restarts (ack-late + reject-on-lost)
- Agents shut down cleanly on SIGTERM (Kubernetes pod termination)
- Retry decorator available for future use in other async paths

### Negative
- Circuit breaker state is per-process (not shared across replicas)
- Dead-letter exchange (DLX) for RabbitMQ deferred to a future phase

## Alternatives Considered
1. **pybreaker library**: Adds external dependency; the dataclass implementation is ~40 lines and sufficient.
2. **Celery retry decorators on individual tasks**: Would require changes in every agent task function; global config is simpler.
3. **Kubernetes preStop hooks**: Complement but don't replace in-process signal handling.
