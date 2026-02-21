# ADR-019: A2A (Agent-to-Agent) Protocol Integration

**Status:** Accepted
**Date:** 2026-02-21
**Deciders:** Engineering Team

---

## Context

YEOMAN (SecureYeoman) operates a network of AI agents that delegate tasks to peer agents via an A2A (Agent-to-Agent) protocol. The protocol defines a small envelope for inter-agent messages:

```json
{
  "id": "<message-uuid>",
  "type": "a2a:delegate | a2a:heartbeat | ...",
  "fromPeerId": "<yeoman-agent-id>",
  "toPeerId": "<agnostic-peer-id>",
  "payload": { ... },
  "timestamp": 1708516800000
}
```

Without A2A endpoints, YEOMAN can only drive Agnostic via the REST task API (ADR-017). That works for one-off tasks but does not let Agnostic appear as a first-class peer in YEOMAN's delegation tree. YEOMAN needs two things:

1. **A receive endpoint** — a single URL it can POST any A2A message to.
2. **A capabilities endpoint** — a way to discover what Agnostic can do before delegating.

---

## Decisions

### 1. `POST /api/v1/a2a/receive` — inbound message handler

A single endpoint receives all A2A messages. Routing is performed on `msg.type`:

| `type` | Action |
|--------|--------|
| `a2a:delegate` | Extract task fields from `payload`, construct a `TaskSubmitRequest`, call `submit_task()` internally, return `task_id` |
| `a2a:heartbeat` | Echo back `message_id` and `timestamp` — liveness check only |
| anything else | Return `accepted: true` with a `warning` field — forward-compatible unknown-type handling |

**Why a single endpoint instead of per-type URLs:** Matches the A2A protocol convention used by YEOMAN, avoids URL proliferation, and simplifies YEOMAN-side configuration (one URL to register).

**Why reuse `submit_task()`:** Keeps task lifecycle logic (Redis store, asyncio fire-and-forget, webhook callbacks) in a single place. The A2A handler is a thin translation layer, not a new execution path.

**Authentication:** The endpoint uses the same `get_current_user` dependency as all other API endpoints. YEOMAN authenticates with an `X-API-Key` header (ADR-017).

### 2. `GET /api/v1/a2a/capabilities` — capability advertisement

Returns a static JSON list of capability objects:

```json
{
  "capabilities": [
    {"name": "qa",             "description": "...", "version": "1.0"},
    {"name": "security-audit", "description": "...", "version": "1.0"},
    {"name": "performance-test","description": "...", "version": "1.0"}
  ]
}
```

YEOMAN calls this before delegating to verify the peer supports the required capability.

**Why static:** Capabilities reflect the deployed agent configuration, which changes infrequently. Dynamic capability discovery (reading from `AgentRegistry`) would add complexity with minimal benefit; version bumps require a deployment anyway.

**Why unauthenticated:** YEOMAN needs to discover capabilities before it has established credentials. This endpoint exposes no sensitive data — it is equivalent to an API's `/openapi.json`.

### 3. Path prefix `/api/v1/a2a/`

Using `/api/v1/` signals that this is a versioned, protocol-specific sub-API distinct from the general REST endpoints under `/api/`. Future A2A protocol versions can be added as `/api/v2/a2a/` without breaking existing integrations.

### 4. `A2AMessage` Pydantic model

The inbound envelope is validated by a dedicated `A2AMessage` model:

```python
class A2AMessage(BaseModel):
    id: str
    type: str
    fromPeerId: str
    toPeerId: str
    payload: dict[str, Any] = {}
    timestamp: int   # Unix milliseconds
```

Fields map directly to the YEOMAN A2A wire format. `payload` defaults to `{}` so heartbeats and unknown types do not require a payload.

---

## Consequences

**Positive:**
- Agnostic becomes a first-class A2A peer in YEOMAN's delegation tree.
- The `agnostic_delegate_a2a` MCP tool in YEOMAN can now route QA tasks without the caller knowing internal REST endpoints.
- Forward-compatible unknown-type handling means new YEOMAN message types do not break the integration.
- No new infrastructure — reuses existing auth, Redis, and task execution machinery.

**Negative / trade-offs:**
- Capabilities list is static; a deployed agent going offline is not reflected until a manual update.
- No A2A protocol version negotiation — if YEOMAN changes the envelope schema, the `A2AMessage` model must be updated.
- `GET /api/v1/a2a/capabilities` is unauthenticated; this is intentional but means the capability list is publicly visible.

---

## Related

- ADR-017: REST Task Submission and API Key Authentication (reused by delegate handler)
- ADR-018: Webhook Callbacks and CORS Configuration
- ADR-013: Plugin Architecture for Agent Registration (AgentRegistry as future capability source)
