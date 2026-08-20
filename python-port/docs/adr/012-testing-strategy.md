# ADR-012: Testing Strategy

## Status
Accepted

## Context
The project lacked a documented testing strategy. Tests existed for 3 of 6 agents, fixture definitions were duplicated across files, and there was no documented approach for coverage targets, mock boundaries, or CI enforcement. The 2026-02-11 audit noted the need for integration tests but no ADR covered testing holistically.

## Decision

### Test Structure
- **Unit tests** (`tests/unit/`): Test individual tool classes in isolation. Each agent's tools get a dedicated test file (`test_<agent>_tools.py`).
- **Integration tests** (`tests/integration/`): Test agent-to-agent communication via Redis/RabbitMQ. Require Docker services.
- **No end-to-end directory**: Full workflow validation is handled via `docker-compose` smoke tests and manual QA via the WebGUI. The previously referenced `tests/end-to-end/` directory was removed from documentation as it was never created.

### Fixture Management
- **Single source of truth**: All shared fixtures live in `tests/unit/conftest.py`, discovered automatically by pytest.
- **Common fixtures**: `sample_requirements`, `sample_test_results`, `mock_redis`, `mock_celery`, `mock_llm`.
- **No direct imports**: Tests should not import from `tests/fixtures/` directly; conftest auto-discovery is preferred.

### Mock Strategy
- External services (Redis, RabbitMQ, LLM APIs) are always mocked in unit tests.
- Agent tools use `try/except/pytest.skip` pattern for graceful degradation when optional dependencies (Playwright, OpenCV, Faker, etc.) are unavailable.
- Integration tests use real Docker services via `docker-compose up -d redis rabbitmq`.

### Coverage Targets
- **Minimum**: 85% line coverage across `agents/`, `config/`, `shared/`, `webgui/`.
- **Per-agent**: Each agent must have at least one test file covering tool initialization and basic `_run` execution.
- **CI enforcement**: `pytest --cov` runs on every PR via GitHub Actions. Coverage below threshold fails the build.

### Configuration
- **pytest config**: Consolidated in `pyproject.toml` under `[tool.pytest.ini_options]`. No separate `pytest.ini`.
- **Markers**: `unit`, `integration`, `slow`, `redis`, `rabbitmq`, `security`.
- **Test runner**: `python run_tests.py` for convenience; `pytest` directly for fine-grained control.

## Consequences

### Positive
- Clear expectations for test coverage when adding new agents
- Single fixture source prevents drift and duplication
- Graceful skip pattern allows tests to run in minimal environments (CI without Playwright, etc.)
- Documented strategy reduces onboarding friction for contributors

### Negative
- `try/except/pytest.skip` pattern can mask real failures if not carefully reviewed
- Mock-heavy unit tests may not catch integration issues
- 85% coverage target may require ongoing effort as codebase grows

## Rationale
This strategy balances practical constraints (optional heavy dependencies, CI resource limits) with quality goals. The skip pattern is well-established in the existing test suite (used by `test_senior_qa_tools.py` since project inception) and works reliably across environments.
