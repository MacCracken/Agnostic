# ADR-014: WebGUI REST API

## Status
Accepted

## Context

The WebGUI had fully implemented manager singletons (`dashboard_manager`, `history_manager`, `report_generator`, `agent_monitor`, `auth_manager`) but no HTTP layer to expose them. The Chainlit-based chat interface was the only way to interact with the system. External tools, dashboards, and CI/CD pipelines had no programmatic access.

CLAUDE.md documented planned API endpoints that did not exist.

## Decision

Create `webgui/api.py` — a **FastAPI APIRouter** that wraps existing manager singletons with HTTP endpoints. Mount it on the existing FastAPI `app` in `webgui/app.py`.

### Endpoint Structure

| Group | Endpoints | Manager |
|-------|-----------|---------|
| Auth | `POST /api/auth/login`, `POST /api/auth/refresh`, `POST /api/auth/logout`, `GET /api/auth/me` | `auth_manager` |
| Dashboard | `GET /api/dashboard`, `GET /api/dashboard/sessions`, `GET /api/dashboard/agents`, `GET /api/dashboard/metrics` | `dashboard_manager` |
| Sessions | `GET /api/sessions`, `GET /api/sessions/search`, `GET /api/sessions/{id}`, `POST /api/sessions/compare` | `history_manager` |
| Reports | `GET /api/reports`, `POST /api/reports/generate`, `GET /api/reports/{id}/download` | `report_generator` |
| Agents | `GET /api/agents`, `GET /api/agents/queues`, `GET /api/agents/{name}` | `agent_monitor` |

### Auth Design

- JWT Bearer tokens via `Authorization: Bearer <token>` header
- `get_current_user()` dependency extracts and verifies token
- `require_permission(Permission.X)` factory for endpoint-level permission checks
- Login returns access + refresh tokens; refresh endpoint rotates tokens

### Design Principles

1. **Thin HTTP layer**: All business logic stays in existing managers. The API module only handles routing, serialization, and auth.
2. **Lazy imports**: Manager singletons are imported inside endpoint functions to avoid circular imports and heavy startup costs.
3. **Pydantic models**: Request bodies use Pydantic `BaseModel` for validation.
4. **Dataclass serialization**: Response data uses `dataclasses.asdict()` for consistent JSON output.

## Consequences

### Positive
- External tools and CI/CD can now query dashboard, agent status, and reports programmatically
- CLAUDE.md planned endpoints are now implemented
- Auth is enforced on all API endpoints
- 8 unit tests verify endpoint behavior

### Negative
- WebSocket `/ws/realtime` endpoint is not yet implemented (deferred to observability work)
- Some endpoints return raw dataclass dicts; may want Pydantic response models later
- Report download depends on file system paths; may need object storage for production

## Rationale

FastAPI router was chosen because:
- Already a dependency (Chainlit uses FastAPI internally)
- Provides automatic OpenAPI/Swagger documentation
- Dependency injection pattern cleanly handles auth
- Pydantic validation catches malformed requests early
