# ADR-018: Webhook Callbacks and CORS Configuration

**Status:** Accepted
**Date:** 2026-02-21
**Deciders:** Engineering Team

---

## Context

Two operational needs emerged from the M2M task submission work (ADR-017):

1. **Completion notification** — Polling `GET /api/tasks/{id}` works but requires the client to know when to check. CI/CD pipelines and YEOMAN agents benefit from a push notification so they don't have to poll.
2. **Browser access from YEOMAN dashboard** — The YEOMAN UI runs on `localhost:18789`. Without CORS headers, browsers block cross-origin requests to the WebGUI API at `localhost:8000`.

---

## Decisions

### 1. Webhook / callback on task completion

`TaskSubmitRequest` accepts two optional fields:

```json
{
  "callback_url": "https://ci.example.com/hooks/qa",
  "callback_secret": "optional-signing-secret"
}
```

When the task finishes (completed or failed), `_run_task_async` fires an HTTP POST to `callback_url` with the full `TaskStatusResponse` body.

**Push vs. poll trade-off:**

| | Polling | Webhook |
|---|---------|---------|
| Client complexity | Higher (needs retry loop) | Lower (receive once) |
| Server complexity | Zero (stateless) | Low (one extra HTTP call) |
| Reliability | High (client controls) | Lower (network, endpoint availability) |
| Latency | Depends on poll interval | Near-instant |

Webhooks are chosen as an optional addition, not a replacement for polling. Clients that cannot receive HTTP callbacks simply omit `callback_url`.

### 2. HMAC-SHA256 request signing

If `callback_secret` is provided, the outbound POST includes:

```
X-Signature: sha256=<hmac-sha256-hex>
```

The signature covers the entire JSON body, keyed by `callback_secret`. This follows the same convention as GitHub webhooks, making it familiar and easy to verify:

```python
import hmac, hashlib
expected = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
assert request.headers["X-Signature"] == f"sha256={expected}"
```

**Why HMAC-SHA256:** Simple, widely supported, no PKI required, replay-safe when combined with the `task_id` in the payload (idempotent by design).

### 3. Webhook failure handling

Webhook delivery failures are **logged but do not affect the task result**. The task status in Redis remains `completed` (or `failed`) regardless of whether the callback POST succeeded. Clients must not rely on webhook delivery as the authoritative task result; they should poll `GET /api/tasks/{id}` if they need guaranteed delivery.

**Why:** Making the task outcome depend on webhook delivery would introduce a coupling between the QA pipeline and an external HTTP endpoint outside our control. This would cause false failures in QA results.

### 4. Configurable CORS via `CORS_ALLOWED_ORIGINS`

`CORSMiddleware` is added to the FastAPI app. Allowed origins are read from the `CORS_ALLOWED_ORIGINS` environment variable (comma-separated):

```bash
CORS_ALLOWED_ORIGINS=http://localhost:18789,http://localhost:3001
```

Default: `http://localhost:18789,http://localhost:3001` (YEOMAN dashboard + common dev port).

**Why env var instead of wildcard `*`:** The API uses `allow_credentials=True`, which is incompatible with `allow_origins=["*"]` per the CORS spec. An explicit allowlist is required for credentialed requests. The env var allows operators to extend the list without code changes.

**Security note:** In production, set `CORS_ALLOWED_ORIGINS` to only the actual UI origin(s). Do not use wildcard.

---

## Consequences

**Positive:**
- CI/CD pipelines get near-instant notification of QA completion without polling.
- YEOMAN browser UI can call the WebGUI API without CORS errors.
- HMAC signing provides lightweight webhook authenticity verification.

**Negative / trade-offs:**
- Webhook delivery is best-effort. Clients requiring guaranteed delivery must use polling as a fallback.
- CORS allowlist must be maintained as new consumer origins are added.
- No webhook retry logic (could be added later via a task queue).
