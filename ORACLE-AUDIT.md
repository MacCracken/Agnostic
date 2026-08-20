# Oracle Audit — Python Agnostic & the AgnosAI Integration

**Reviewed:** 2026-08-19 · **Tree:** `main @ c3bedf7` · **Method:** six parallel audits + adversarial verification pass
**Result:** 109 candidate findings → 24 refuted → **85 confirmed** (18 high, 31 medium, 36 low)

> This document is the retained artifact of the Python implementation. The code itself moves to
> `python-port/` and serves as an **oracle** — a behavioural reference for the Cyrius rewrite
> (Agnostic 1.0.0) — **not** as a finalized product. Everything below describes what the oracle
> actually does, including where it is wrong. Do not port a behaviour from `python-port/` without
> checking it against this list first.

---

## 1. State at freeze

177 commits, all inside February–March 2026. Last commit `c3bedf7` landed **29 March 2026**; the tree
is clean. This is a paused project, not an in-flight one.

| Metric | Value |
|---|---|
| Python | 203 files, ~61k LOC |
| Modules | `agents/` 13.0k · `webgui/` 13.4k · `shared/` 7.2k · `config/` 5.5k · `benchmarks/` 1.2k |
| Tests | 64 files, 1,207 test functions (1,129 unit / 43 e2e / 29 k8s / 6 integration) |
| ADRs | 29 |
| CI | 7 jobs across 3 workflows |

The last seven commits were **all** AgnosAI work:

| Commit | What it did |
|---|---|
| `e7b04b7` | Integration landed whole — 13 files, backend ABC + router + client + shim |
| `51b997d` | Benchmark fixes |
| `f8f73a2` | Benchmark scenarios; message notes "hoosh still to be wired into agnosai" |
| `64750c0` | Added `cancel_crew` + definition/preset/tool registry helpers |
| `d63e120` | Connection handling |
| `7617ed4` | `CrewProfile` server-side profiling; renamed compose `ollama` → `ollama-nvidia` |
| `3cfe639` | SSE `event:` parsing; hardware / personality / priority passthrough |
| `c3bedf7` | Replaced compose `build:` (sibling checkout) with public `ghcr.io/maccracken/agnosai:1.0.2` |

Work stopped immediately after making the integration runnable for someone without a sibling AgnosAI
checkout. Nothing was ever verified end to end.

### 1.1 Documentation drift

Every headline number in the README is wrong, and several disagree with each other.

| Claim | Stated | Actual | Where |
|---|---|---|---|
| Unit tests | 865 | **1,129** | `README.md:199` — also 833 / 816 / 922 / 1099 elsewhere |
| E2E tests | 24 | **43** | `README.md:199` |
| MCP tools | 27 · 25 · 32 | **34** | `README.md:184`, `:203`; `agnostic.agpkg.toml:57` |
| RPC methods | 16 | **8** | `agnostic.agpkg.toml:56` |
| ADRs | 28 | **29** | `README.md:162` |
| Presets | 3 | **18** | `README.md:58` |
| Version | 2026.3.12 / .14 / .17 | **2026.3.18** | agpkg · `README.md:224` · `Chart.yaml` · `VERSION` |

The README quick-start snippet calls `AgentFactory.from_preset("qa-standard")`. No such preset exists;
`agents/factory.py:86` does a literal filename lookup with no alias map, so the documented example
raises `FileNotFoundError`. The real preset is `quality-standard`.

Neither changelog mentions AgnosAI at all, across seven commits of work. The roadmap still lists
already-shipped items (the `AGNOSTIC_BACKEND` feature flag) as pending Phase 5 work, and carries no
status markers — `roadmap.md:3` declares everything in it "Pending development work".

---

## 2. How the oracle wires AgnosAI

A four-method `CrewBackend` ABC in `agents/backend/base.py`, with `get_backend()` reading
`AGNOSTIC_BACKEND` **per call** (`agents/backend/router.py:19`). Default `crewai`; setting `agnosai`
swaps the entire Python pipeline for a single HTTP round-trip.

```
                      AGNOSTIC_BACKEND
                     ┌────────┴────────┐
              "crewai" (default)   "agnosai" (opt-in)
                     │                 │
      _build_agents_sync         _build_agents_sync   (definitions only)
      _build_task_data           _translate_crew_config → 4-key payload
      _try_fleet_execution       POST /api/v1/crews    (await body)
      _run_local                 ╳ fleet shim — unreachable branch
                     └────────┬────────┘
                    _aggregate_and_finalize → Redis + webhook
```

### 2.1 Endpoint surface

Eleven AgnosAI endpoints are spoken by `agents/backend/agnosai_backend.py` and
`config/fleet/shim.py`. **Four are reachable from application code.**

| Endpoint | Client method | Reached from | Status |
|---|---|---|---|
| `POST /api/v1/crews` | `execute_crew` | `crews.py:610` | live |
| `POST /api/v1/crews/{id}/cancel` | `cancel_crew` | `crews.py:960` | **wrong id sent** |
| `GET /api/v1/crews/{id}` | `get_crew_status` | — | no callers |
| `GET /api/v1/crews/{id}/stream` | `stream_crew` | — | no callers |
| `GET`/`POST /api/v1/agents/definitions` | `list_definition` / `push_definition` | — | no callers |
| `GET /api/v1/presets` | `list_presets` | — | no callers |
| `GET /api/v1/tools` | `list_tools` | — | no callers |
| `GET /api/v1/fleet/nodes` | `FleetShim.get_alive_nodes` | `crews.py:321` | dead branch |
| `POST /api/v1/fleet/place` | `FleetShim.plan_and_distribute` | `crews.py:324` | dead branch |
| `POST /api/v1/fleet/results` | `FleetShim.submit_result` | — | dead code |
| `GET /api/v1/crews/{id}` (poll) | `FleetShim.collect_results` | `crews.py:339` | dead branch |

### 2.2 Request translation

`_translate_crew_config` (`agnosai_backend.py:21-79`) emits exactly four keys — `name`, `agents`,
`tasks`, `process`. Per-agent it forwards a whitelist of ten fields:

**Forwarded:** `agent_key`, `name`, `role`, `goal`, `backstory`, `domain`, `tools`, `complexity`,
`llm_model`, plus `hardware` **or** the legacy `gpu_required`/`gpu_preferred`/`gpu_memory_min_mb`
trio, plus `personality`.

**Silently dropped:** `focus`, `allow_delegation`, `llm_temperature`, `verbose`, `metadata`,
`gpu_strict`. At crew level: `target_url`, `session_id`, `crew_id`, `task_id`, `priority`,
`scheduling_policy`, `group`, and the entire `task_data` envelope.

### 2.3 The dead fleet branch

`_try_fleet_execution` opens with `if AGNOSTIC_BACKEND == "agnosai"` (`crews.py:317-345`) and
delegates to the shim. Its **only** caller is the `else` arm of that same test at `crews.py:619-623`.
The AgnosAI fleet shim can never execute. Even if reached, it implements 4 of the ~15 capabilities the
native `FleetCoordinator` / `CrewStateManager` / `TaskRelay` stack provides — no relay, no barriers, no
checkpointing, no coordinator failover, no dead-node re-placement, no local-agent execution.

---

## 3. Confirmed defects — high severity

Do **not** carry these behaviours into 1.0.0.

### 3.1 A failed crew is reported to the user as completed
`agents/backend/agnosai_backend.py:151` → `webgui/routes/crews.py:613`

`execute_crew` sets `BackendResult.error` only on transport and HTTP errors. A well-formed `200`
carrying `{"status":"failed","results":[]}` returns `error=None`. The caller branches solely on
`.error` — `BackendResult.status` is **never read anywhere in the codebase** — so execution falls
through to `_aggregate_and_finalize`, where `all()` over an empty results dict is vacuously true and
the crew is finalised as `completed`.

### 3.2 Cancel addresses a crew id AgnosAI has never seen
`agents/backend/agnosai_backend.py:99` → `webgui/routes/crews.py:957`

`execute_crew` accepts `session_id`, `crew_id`, `task_id` and uses none of them — the payload carries
only name/agents/tasks/process. The id AgnosAI assigns comes back in the response and is discarded;
`BackendResult` has no field to hold it. Cancel then POSTs the *local* UUID from `crews.py:751`,
which 404s. That error dict is discarded too (`crews.py:960`), and the record is marked cancelled
while the crew keeps running remotely.

### 3.3 The two backends run structurally different work
`agents/backend/agnosai_backend.py:62`

`_translate_crew_config` emits a real task list only when `crew_config["tasks"]` exists. It never can:
`CrewRunRequest` (`crews.py:74-130`) declares no `tasks` field, and the dict assembled at
`crews.py:790-806` has no such key. Pydantic v2 defaults to `extra='ignore'` with no `model_config`
set, so a client-supplied `tasks` array is silently discarded. The single-task fallback therefore
**always** fires — AgnosAI receives one task holding the raw description with every agent attached,
while the crewai path builds a per-agent task envelope.

### 3.4 Fleet and GPU failures are finalised as successful empty runs
`webgui/routes/crews.py:418`, `:330`, `:366` → `:632`

Three failure paths write a terminal `failed` status and then `return {}, 0`. The caller only
distinguishes `None` from a tuple, so the sentinel is accepted as a result set; control reaches
`_aggregate_and_finalize`, whose `all()` over `{}` is vacuously true and overwrites `failed` with
`completed`. **This predates the AgnosAI work and affects the default backend too.**

### 3.5 Cancellation does not stop the in-flight task
`webgui/routes/crews.py:962`

The background `asyncio` task is never cancelled. It continues and later rewrites the Redis record
from `cancelled` back to `completed`.

### 3.6 `CrewProfile` is used without being imported
`agents/backend/agnosai_backend.py:144`

Line 13 imports only `BackendResult` and `CrewBackend`. Line 144 calls `CrewProfile(...)`. Any AgnosAI
response containing a `profile` object raises `NameError` inside `execute_crew`. Latent because
`from __future__ import annotations` renders the line-141 annotation inert.

### 3.7 The profile test never calls the code it claims to test
`tests/unit/test_agnosai_backend.py:260`

Docstring: *"Verify execute_crew extracts CrewProfile from response."* Body: imports `CrewProfile`
from `agents.backend.base` and constructs it directly. `execute_crew` is never called — which is why
3.6 went undetected.

### 3.8 No test asserts an AgnosAI URL, method, or payload key
`tests/unit/test_agnosai_backend.py:122`

Every execute/cancel test patches `httpx.AsyncClient` and asserts only on the returned
`BackendResult`. Change `/api/v1/crews` to any other path, or rename a payload key, and the suite
stays green. Six client methods have no test at all; `config/fleet/shim.py` has none.

### 3.9 CI never starts agnosai-server
`.github/workflows/ci.yml:130`

The string `agnosai` appears **zero times** under `.github/`. The e2e job runs
`docker compose --profile dev up -d`; `agnosai-server` sits behind the `agnosai`/`e2e`/`benchmark`
profiles. `tests/e2e/test_crew_dual_backend.py` is collected but `E2E_BACKEND` defaults to `crewai`,
so both legs exercise the same path.

### 3.10 `.env.example` breaks the documented quick start
`.env.example:39`, `:5`

Copying `.env.example` to `.env` — step one of the README quick start — sets
`REDIS_URL=redis://redis:6379/0`, which Compose interpolates over the working default (verified with
`docker compose config`). Line 5 has the mirror-image problem: `AGNOSAI_URL=http://localhost:8080`
overrides the correct in-network `http://agnosai-server:8080`, so an in-container client dials itself.

### 3.11 Agent fields dropped in translation
`agents/backend/agnosai_backend.py:33`

See §2.2. `gpu_strict` is the sharp one — a hard-fail GPU requirement becomes a silent CPU fallback.

### 3.12 Compose overrides target services that no longer exist
`docker-compose.prod.yml:36`

### 3.13 CrewAI pinned three incompatible ways
`requirements.txt:40` (`crewai==0.11.2` + langchain 0.1.20) vs `requirements-docker.txt:6`
(`crewai[litellm]==1.10.1`) vs `pyproject.toml:51` (`>=1.0.0,<2.0.0`). The Dockerfiles install
`requirements-docker.txt`; `contributing.md:16` tells developers to install `requirements.txt`, which
violates pyproject's own constraint. `requirements.txt` is a 292-line `pip freeze` of a dev virtualenv
that nothing installs.

### 3.14 The benchmark harness is not apples-to-apples
`benchmarks/runner.py:88` — see §4.

---

## 4. The benchmark numbers do not mean what they say

`benchmarks/` is 1,213 lines across 8 files and **imports nothing from the project** — only `httpx`
and `pytest`. It drives both servers directly with its own payload shapers, so it never exercises
`AgnosAIBackend`, `get_backend()`, or `FleetShim`. It benchmarks the AgnosAI server, not the
integration.

| Defect | Where | Effect on the published tables |
|---|---|---|
| CrewAI arm's task list discarded | `runner.py:88` | `CrewRunRequest` has no `tasks` field and Pydantic ignores extras — the two arms run different workloads |
| Poll loop sleeps before its first check | `runner.py:119` | CrewAI latencies quantize to ≥2s buckets; AgnosAI returns synchronously and skips polling, never paying the tax |
| Timeouts count as successes | `report.py:42` | `status != "error"` admits `timeout`, folding 300s runs into the latency mean — this is the "300.8 (timeout)" cell |
| No output validation | `report.py:42` | Only the status string is checked; a `{"status":"completed","results":[]}` no-op scores as the fastest possible run |

### 4.1 The 0.002s cells

`docs/development/benchmarks.md` reports AgnosAI at **0.002s** for multi-agent, DAG and 6-agent crews,
attributed to response-cache hits on "prompts cached from the single-agent run". But
`benchmarks/scenarios.py` gives those scenarios entirely distinct prompts — revenue summarisation,
microservice research, SQL-injection review, REST API planning. A cache cannot legitimately hit across
them. Either the cache is over-matching or those crews returned without running, and nothing validates
that any agent produced output.

**The "AgnosAI 2.2× faster on large crews" headline rests on cells the harness cannot distinguish from
a no-op.** Treat all published numbers as unverified.

### 4.2 The 422 cells are not a CrewAI capability gap

`CrewRunRequest.process` is `Literal["sequential", "hierarchical"]`. The `parallel` and `dag`
scenarios are rejected by Agnostic's own request model before CrewAI is ever reached.

### 4.3 The documented run command no longer works

Commit `7617ed4` renamed the compose `ollama` service to `ollama-nvidia`, so
`docker compose --profile benchmark up` now starts no LLM server at all.

---

## 5. Remaining findings by theme

| Theme | Count | Representative |
|---|---:|---|
| Docs vs reality | 18 | No changelog mentions AgnosAI; README documents nothing about the backend; roadmap lists shipped items as pending |
| Config & deploy | 17 | `Dockerfile.agnos` builds `FROM` a local-only tag; cadvisor and agnosai-server both claim host port 8080; `AGNOSAI_EXECUTE_TIMEOUT` used but undocumented |
| Tests & coverage | 16 | Dual-backend e2e assertions never verify which backend ran; `run_tests.py` reports success on zero collected tests |
| Translation fidelity | 14 | `process` is a no-op on crewai but forwarded to AgnosAI; result keys collapse when `task_id` is absent; fallback task omits `expected_output` |
| Backend correctness | 11 | `resp.json()` outside the try block; `stream_crew` has no `raise_for_status` and leaks event type across frames; `"results": null` raises `TypeError` |
| Call sites | 9 | Early returns leak the `ACTIVE_CREW_TASKS` gauge and skip the webhook; `gpu_agent_count` hardcoded to 0 |

### 5.1 Refuted candidates

24 findings were dropped by the verification pass. The dominant reason: they depended on the
behaviour of the external `ghcr.io/maccracken/agnosai` image, which has no source in this tree —
default auth posture, persistence needs, whether the create-crew endpoint is synchronous, and whether
image tag `1.0.2` corresponds to crate version `0.21.3+`. **These are open questions for 1.0.0, not
settled facts.**

---

## 6. Design lessons for Agnostic 1.0.0 (Cyrius)

Carried forward as requirements, derived from what the oracle got wrong:

1. **A result type must carry status, error, *and* the remote id.** The oracle's `BackendResult` has
   no id field and its `status` is never read. Both are load-bearing.
2. **Terminal states must be terminal.** No aggregation step may promote a `failed` record to
   `completed`. An empty result set is not success.
3. **One task model, not two.** The oracle's request model and its translation layer disagree about
   whether tasks exist. Whatever the wire format is, the API model and the translator must be
   generated from or checked against a single definition.
4. **Cancellation must stop work,** not just relabel a record.
5. **Every field in the agent definition is either forwarded or explicitly rejected** — never silently
   dropped. `gpu_strict` becoming a CPU fallback is the failure mode to design out.
6. **Tests assert the wire, not the mock.** URL, method, payload keys, response parsing.
7. **CI runs the AgnosAI path.** An integration with no CI coverage is an integration that does not
   exist.
8. **Benchmarks validate output before timing it,** exercise the real client path, and never count a
   timeout as a success.
9. **One version string.** The oracle had six across eight files.

---

## 7. Method

Six parallel audits over `agents/backend`, `config/fleet`, `webgui/routes/crews.py`, `benchmarks/`,
`tests/` and `docs/`, each followed by an adversarial verification agent instructed to refute rather
than confirm, with instructions to default to *not real* when the code could not be shown to fail.
Severities in this document reflect the verifier's correction, not the finder's claim. Claims about
the external AgnosAI server binary were systematically refuted for lack of in-tree evidence.

Interactive version of this report:
<https://claude.ai/code/artifact/fca74d0d-3947-4984-ad48-f83b90f794f0>
