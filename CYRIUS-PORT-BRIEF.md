# Cyrius Port Brief — Agnostic 1.0.0

**Researched:** 2026-08-19 · **Cyrius:** 6.5.29 · **AgnosAI:** 2.0.1 → 2.0.2 (dist target)
**Method:** 12 research agents across cyrius / vidya / agnosai / ~150 ecosystem repos, plus an
adversarial refutation pass over every claimed capability gap (35 agents completed).

Companion to [`ORACLE-AUDIT.md`](ORACLE-AUDIT.md), which documents what the Python oracle in
`python-port/` actually does — including where it is wrong.

---

## 0. Headline

**Agnostic 1.0.0 is roughly a third of the Python tree.** AgnosAI 2.0.1 already owns the entire
*engine* tier: crews, tasks, agents, DAG/priority scheduling, agent scoring, LLM routing through
hoosh, the tool registry with four sandbox tiers, fleet coordination + GPU scheduling, multi-tenant
budgets, human-in-the-loop approvals, a tamper-evident audit chain, durable state, SSE, Prometheus,
OTLP/GenAI telemetry, RL learning, definition versioning/packaging, the TeamSpec crew assembler, and
the same 18-preset library.

Of the oracle's 16 route modules, only `crews`, `agents/definitions`, `presets`, `tools`, `dashboard`
and the A2A half of `tasks` have AgnosAI counterparts.

**AgnosAI already ran this exact port.** Rust → Cyrius, `rust-old/` kept as the parity oracle,
2026-07-28 → 2026-08-18: 167 commits in 22 working days, ~122 "bites" across 10 module groups,
shipped as exactly **two** releases (2.0.0 and 2.0.1). Follow that shape.

---

## 1. Cyrius, in the terms that matter for this port

| | |
|---|---|
| Core type | **Everything is i64.** Pointer, bool, char, struct handle — one 64-bit word (ADR-002) |
| Annotations | `: i64`, `: Str`, `: Result` are **documentation + dispatch hints, never enforcement**. Verified: `fn f(x: i64): Result { return x + 1; }` compiles clean and returns a bare integer at cycc 6.5.29 |
| Where types ARE load-bearing | Three places only: struct-field byte width, pointer-to-struct dot syntax, and name-suffix overload dispatch |
| Structs | Contiguous and **unpadded** — `struct S { a: i32; b: i64; }` puts `b` at byte 4. `p.x` and `load64(p)` are the same bytes |
| Memory | Fully manual. `lib/alloc.cyr` is a bump allocator with **no `free()`** — only `alloc_reset()`, which invalidates every pointer ever handed out. `lib/freelist.cyr` is the only real per-block free |
| Namespace | **ONE global symbol table, last-definition-wins.** The compiler warns on duplicate `fn` and is *silent* on duplicate `var` or duplicate enum member |
| Polymorphism | Three tiers: convention mangling (`impl T for Point` → `Point_method`), name-suffix overloads (`strlen(Str)` → `strlen_str`), manual vtables (`lib/trait.cyr` / `callptr`) |
| Errors | `Result` as a 16-byte heap cell `{tag, payload}`. But `?` is barely used in real code — the dominant idiom is `is_err_result(r)` / `payload(r)`, or a 0/-1 sentinel, or sakshi's zero-alloc packed-i64 code |
| Builds | **Always `cyrius build`, never `cat \| cycc`.** The CLI materialises a temp file carrying `#@incdir` / `#@pkgver` / one `include` per `[deps].stdlib` module / `#@srcline` before your source. Raw piping silently loses all of it |

### 1.1 The five things that will bite coming from Python

1. **No `free()`.** The server idiom is a **per-request arena** with SPILL policy, threaded through
   every `_a`-suffixed call. Copy `agnosai/src/server/serve.cyr:124-129` (`agnosai_spill_arena`) and
   `:401-420` verbatim.
2. **Arena exhaustion returns 0, and a `Str` of 0 is indistinguishable from a valid one.** There is
   no option type and no error channel through the `_a` families — it flows on and the first
   dereference crashes. This is why SPILL exists.
3. **Top-level `var A = get();` referencing a global declared later silently evaluates to 0.**
   Function forward references are fine (cycc is two-pass); top-level var initialisers are not.
4. **The flat namespace is a real hazard.** An audit in agnosai found four duplicated enum constants,
   three with *different* values, three of them struct sizes passed straight to `alloc()`. Adopt
   `scripts/check-symbols.sh` (agnosai's) on day one, prefixing everything `agnostic_*` / `_agnostic_*`
   / `AGNOSTIC_*`.
5. **AgnosAI declares zero `struct`s and 182 `enum`s** — enums used as named offset tables over
   `alloc()`ed blocks. That is the house idiom for this codebase size.

---

## 2. The dependency stack

Two wiring mechanisms, and mixing them up breaks the build.

**Folded into the cyrius stdlib** — declare in `[deps].stdlib = [...]`, **never** write a
`[deps.NAME]` git block (doing so silently downgrades transitive consumers):

| Module | Replaces | Notes |
|---|---|---|
| `patra` 1.13.9 | PostgreSQL + SQLAlchemy | Embedded single-file store, `flock`-arbitrated. **No client/server mode** — the oracle's multi-container "everyone talks to `postgres`" topology cannot be reproduced |
| `sandhi` 1.9.10 | FastAPI + httpx | HTTP/1.1(+TLS) server, 4 concurrency models, `:name` routing, chunked/SSE writes, per-request arena, cooperative stop flag |
| `bayan` 1.4.2 | pydantic (runtime half) + json | `bayan_json_v_*` tagged tree. The `*_from_value_a` idiom with an allow-list == serde `deny_unknown_fields` |
| `sakshi` 2.4.11 | logging + OTel spans | Packed-i64 errors, 6 output targets, W3C 128-bit trace ids. **Spans carry no key/value attributes** |
| `sigil` 3.12.9 | cryptography | SHA-256 + `ct_eq_bytes` (API keys), `hmac_sha256` (webhook sigs), X.509/Ed25519/ECDSA/RSA |
| `yantra` 1.0.2 | Playwright | 46 verbs, CDP + W3C WebDriver + Appium. See §4 |
| `ganita` 1.1.1 | numpy (linalg half) | Matrix, linalg, transcendental |

**External git deps** — copy AgnosAI's `cyrius.cyml` block shape verbatim
(`git` / `path` / `tag` / `modules = ["dist/NAME.cyr"]`):

| Package | Replaces | Verdict |
|---|---|---|
| `majra` 2.6.6 | Redis + Celery + RabbitMQ | **Required.** `relay`/`heartbeat`/`queue`/`barrier`/`namespace`/`ratelimit` map near-1:1 onto `python-port/config/fleet/*.py` — the oracle's `TaskRelay` seq+dedup logic *is* majra's `relay_send`/`relay_receive_ex`/`relay_last_seq` |
| `kavach` 3.11.14 | `agents/tool_sandbox.py` | **Required.** 10 real sandbox backends vs the oracle's hand-rolled rlimit subprocess |
| `bote` 3.3.1 | `shared/yeoman_mcp_server.py` | **Required.** Ships the MCP dispatcher, 18 `prompt_*` and 15 `resource_*` fns, JSON Schema compile+validate, CORS precedent, server-side session store |
| `ai-hwaccel` 2.3.17 | `config/gpu.py` | **Yes** — strict superset of the oracle's `nvidia-smi`-only detection |
| `tyche` 1.0.1 | retry jitter, sampling | Small yes. Explicitly **not** a CSPRNG |
| `agnosai` **2.0.2** | CrewAI + the whole engine tier | **The point of the exercise.** Needs a dist target — see §3 |

> ⚠ **Do not declare `unicode` in Agnostic's `[deps].stdlib`.** `dist/agnosai.deps` already lists it,
> and a package-**directory** leaf declared in both places at once makes `cbt` emit an unexpanded
> `include "lib/unicode.cyr"` — a file that does not exist — and the build fails with
> `cannot open include file: lib/unicode.cyr`. `unicode` is the only stdlib module that is a
> directory (`lib/unicode/*.cyr`) rather than a single file, so it is the only leaf affected.
> Filed upstream as
> `cyrius/docs/development/issues/2026-08-19-agnostic-sidecar-package-dir-double-declare.md`
> with a 2-line repro. Remove the line and the build completes; `cyrius deps` still provisions
> `lib/unicode/` from the sidecar.

**hoosh 2.6.3 is a service, not a library** — no `[lib]`, no `dist/`. AgnosAI consumes it as a remote
OpenAI-compatible seam (`src/llm/hoosh.cyr`, 24 fns, one `sandhi_http_post`) and does not list it in
`cyrius.cyml` at all. The oracle's `AGNOS_LLM_GATEWAY_*` **is** hoosh — same port 8088. Copy the seam;
let hoosh own budgets, caching, cost, DLP, rate limiting and failover.

---

## 3. Making AgnosAI consumable as a library (2.0.2)

Today AgnosAI is binary-only: no `[lib]` stanza, no `dist/`, `[release] bins = ["agnosai"]`, and
`README.md:84` documents the posture as intentional. The fix is a one-manifest change plus a
regenerate, matching what every dependency AgnosAI itself consumes already does.

**Mechanism** (confirmed from `majra/cyrius.cyml:14-30`): a `[lib] modules = [...]` list, in
**main.cyr's include order** — "critical for Cyrius single-pass forward-reference resolution" — then
`cyrius distlib`, which emits `dist/agnosai.cyr` plus a `dist/agnosai.deps` sidecar listing required
stdlib leaves. Profiles are supported (`cyrius distlib <profile>` from `[lib.<profile>]`).

**Three obstacles, all known:**

1. **`src/main.cyr` must be excluded.** It ends with
   `var _agnosai_exit_code = main(); _agnosai_exit_process(_agnosai_exit_code);` — top-level
   statements that run at include time. A consumer linking that would start a server on include.
   Its own header says so: *"The lines at the foot run `main()` at include time."*
2. **The `[lib].modules` list must be main.cyr's include order fully expanded through the nine
   `mod.cyr` hubs** (102 include-free leaves), because the hubs share the basename `mod.cyr` and
   their `include "src/..."` paths resolve against the *consumer's* root.
3. **Five leaf basenames are duplicated across directories** — `approval`, `registry`, `router`,
   `sse`, `state` — which collide in the flat namespace. `cyrius distlib` concatenates rather than
   namespaces, so verify with `scripts/check-symbols.sh` after generating.

**Profiles worth considering:** a `core` default (orchestrator + llm + tools + definitions) versus
`full` (+ fleet, sandbox, learning, server). Agnostic likely wants close to full, since the library
path is the *only* way to reach `agnosai_orchestrator_submit_crew`, the fleet stack, the learning
stack and durable_state — **none of which has an HTTP route.**

---

## 4. AgnosAI 2.0.1 as it actually is

19 method+path pairs, enumerated at `src/server/router.cyr:300-441`: three unauthenticated probes
(`/health`, `/ready`, `/metrics`), `POST /mcp`, and fifteen routes under `/api/v1`.

**Answers to the questions `ORACLE-AUDIT.md` §5.1 left open:**

| Question | Answer |
|---|---|
| Is `POST /api/v1/crews` synchronous? | **Fully synchronous** — calls `agnosai_orchestrator_run_crew` inline, returns 200 only when the crew has finished (`routes/crews.cyr:544-584`) |
| Does the response carry `crew_id`? | **Yes** — plus `status`, `results[]`, and an optional `profile` |
| Does `profile` match the oracle's `CrewProfile`? | **Superset** — `{wall_ms, task_ms{}, task_count, cost_usd?, agent_cost_usd?, task_cost_usd?, sandbox_strength?}`; `cost_usd` omitted when zero |
| Auth? | `Authorization: Bearer <token>` **only** — case-sensitive, no `X-API-Key`. Shared-secret or RS256-JWT. **Disabled by default (fail-open)** |
| Client-supplied crew id / idempotency key? | **No.** `CrewRunRequest` is `deny_unknown_fields` over exactly `{name, agents, tasks, process, max_concurrency}`; the UUID is minted server-side |
| Fleet endpoints? | **They have never existed.** `grep -rn "fleet" src/server/` returns nothing. The oracle's entire `config/fleet/shim.py` targeted phantom routes |
| SSE events | `connected`, `crew_started`, `task_started`, `token`, `task_completed`, `crew_completed`, `error`, plus `:ping` every 15s |

**Two consequences that reshape the port:**

- **`deny_unknown_fields` is now enforced.** The 14 fields the Python translator silently dropped
  (§2.2 of the audit) will hard-**422**. Agnostic must own an explicit, tested translation layer —
  which is exactly design lesson 5 from the audit.
- **Live progress is unreachable over HTTP.** POST is synchronous and the event channel is torn down
  at crew finish, so a client that learns `crew_id` from the POST response can never attach a stream.
  The library path (`submit_crew` + the event bus directly) is the only clean answer.

**Known defect to work around:** `src/server/routes/mod.cyr:44` hardcodes `AGNOSAI_VERSION = "1.1.0"`
while `VERSION` is 2.0.1, so `/ready` and MCP `initialize` both under-report.

---

## 5. Capability gaps — searched, not assumed

Every claimed gap below survived an adversarial agent instructed to find it. Equally important is
§5.1: the things that *looked* missing and are not.

### 5.1 Refuted — assumed missing, actually shipped

| Assumed missing | Actually at |
|---|---|
| OpenTelemetry SDK | **`agnostik`** — the repo name contains neither "otel" nor "opentelemetry", which is why the first sweep missed it |
| PDF generation | **`mneme/src/io_export_pdf.cyr`** — 443 lines, test-green, proven to run |
| DB migration framework | **`szal/src/migration.cyr`** — versioned, ordered engine |
| OpenCV `matchTemplate` | **`rosnet` `conv2d_fwd`** — a 2D cross-correlation score-map generator |
| JSON Schema / validation | **`bote/src/schema.cyr`** — `compiled_compile:336`, `compiled_validate:527` |
| JWT minting (HS256) | **`secureyeoman/yeo-cy-test/src/auth.cyr:221`** — complete RFC 7519 JWS encoder |
| dotenv loader | **`argonaut/src/`** — the ecosystem calls it "env file", never "dotenv" |
| Prometheus exposition | **`agnosai/src/server/prometheus.cyr`** (235 lines) + `hoosh/src/lib/metrics.cyr:87-130` |
| Charting | Three implementations; and the oracle renders **zero** charts, so the requirement was overstated |
| Classical ML | **`pramana`** — not cloned locally, which is why it was missed |
| Redis client / non-loopback reach | Exists — `cyrius/lib/net.cyr:371` + majra backends |
| Screen capture | Three implementations, one in the stdlib (`syscalls_x86_64_agnos.cyr:136 SYS_GPU_READBACK_SHM`) |
| Project scaffolding | `cyrius init` — `programs/cyrius-init.cyr:656-865`, full scaffolder with in-place mode |

**The lesson: the ecosystem names things in Sanskrit, Arabic and Persian. English keyword greps
produce false negatives.** Search by concept and by function-name prefix, then ask.

### 5.2 Confirmed gaps

Sorted by how much they actually cost.

| Gap | Impact | Path forward |
|---|---|---|
| **Server-side HTTP keep-alive** | Real throughput ceiling — sandhi always writes `Connection: close`, so every request pays a fresh TCP+TLS handshake. SecureYeoman's 43-tool client polls | Patch sandhi, or accept it. Client-side pooling *does* exist (`sandhi_http_pool_*`), so Agnostic→AgnosAI/hoosh calls are fine |
| **patra: GROUP BY, OFFSET, DISTINCT, JOIN** | Oracle uses GROUP BY twice, OFFSET for pagination in three list endpoints | Aggregate in Cyrius: SELECT filtered rows `ORDER BY key`, fold with `lib/hashmap.cyr`. Emulate OFFSET over LIMIT |
| **patra: no float column type** | `metric_value`, `pass_rate`, `next_run_time` are all `sa.Float` | Fixed-point i64 micro-units — exactly what AgnosAI does with `cost_micro_usd` |
| **patra: one index per table** | `SCH_IDX_COL` is a single i64 slot that `CREATE INDEX` overwrites; `test_results` carries four | Highest-selectivity column gets the real index; covering shadow tables for the rest |
| **patra: no schema introspection** | Any migration runner needs to detect current state | Partial: `patra_result_col_name` / `_col_type` via `SELECT * FROM t LIMIT 1` |
| **CORS middleware** | WebGUI is a cross-origin SPA | Two in-ecosystem precedents to copy: `bote/src/bridge.cyr:205-208`, and secureyeoman's |
| **Cookie jar / session cookies** | Browser sessions; yantra-driven QA against cookie apps | sandhi tracks this as an open deferred request. `bote/src/session.cyr` has the server-side store |
| **multipart/form-data** | Definition packaging, visual-baseline uploads | Base64-in-JSON (what AgnosAI and daimon already do), or a ~120-line boundary splitter over `lib/string.cyr` memmem |
| **Statistics primitives** | Flaky-test detection, quality trends, p50/p95/p99 | Copy `agnosai/src/order.cyr:130 agnosai_percentile_i64` (quickselect); mean/variance are three lines on top |
| **SMTP client** | Scheduled report delivery by email | ~300 lines over `lib/net.cyr` + `tls_native.cyr` (STARTTLS), or deliver via webhook/SSE/file drop instead |
| **In-process WASM runtime** | Sandboxed tool execution | Keep kavach's shell-out to `wasmtime` — kavach 3.11.10 is the working floor |
| **AMQP / RabbitMQ** | — | **Do not port it.** `import celery` appears exactly once in the oracle; the broker path is dead weight. majra covers the real shape |
| **OpenAPI generation** | API docs | The load-bearing half (JSON Schema authoring/compile/validate) exists in bote. Document generation does not |
| **sandhi DNS resolver has no socket timeout** | Hangs on a dead resolver | Lift `dig/src/platform_linux.cyr:48 platform_set_recv_timeout_ms` (SO_RCVTIMEO) |

### 5.3 The one that needs a decision

**`yantra` drives browsers but cannot take a screenshot.** 46 verbs, Chromium over CDP and
Firefox/WebKit/Chrome/Safari over W3C WebDriver, plus Android/iOS over Appium — but the entire CDP
surface is three methods (`Page.navigate`, `Page.enable`, `Runtime.evaluate`), and there are **zero
occurrences of "screenshot" in `cyrius/lib/yantra.cyr`**. No pixel capture means the oracle's CV
self-healing and visual-regression baselines have no input.

Mitigating: **the oracle's CV is much weaker than it advertises.** It template-matches
*synthetically generated grey rectangles* (`np.ones(...) * 240` with a 180-value border) against the
screenshot, and its "semantic" and "DOM structure" healing are hardcoded f-string selector lists with
hardcoded confidence constants — no analysis at all.

Rebuilding on `chitra` 0.3.1 (PNG/JPEG → RGBA8) + `ranga` 2.0.0 (grayscale, histograms, transforms)
+ `rosnet` conv2d + a ~50-line normalized-cross-correlation loop is tractable — but it needs
`Page.captureScreenshot` added to yantra's CDP surface first.

---

## 6. Process rules inherited from the house

From `cyrius/CLAUDE.md` and `agnosai/CLAUDE.md` — these constrain *how* the work is done:

- **Atomic commits, packed releases.** Commits are one logical "bite"; a release bundles dozens.
  AgnosAI's whole port was two releases.
- **One change at a time.** Never bundle unrelated changes.
- **Test after every change**, not after the feature is done.
- **Research before implementation — vidya entry before code.**
- **When stuck, ASK.** Never defer, slip, re-slot, or split work mid-execution. Splits are decided
  *before* starting; reactive scope changes when stuck count as slipping.
- **Never hand-edit `VERSION`.** Run `sh scripts/version-bump.sh <new>` and let it write — it only
  rewrites CLAUDE.md's version line, the CHANGELOG header and the roadmap stamp when it sees a
  *change*, so pre-writing VERSION silently skips all of them.
- **Volatile state goes in `docs/development/state.md`**, so `CLAUDE.md` stays durable process only.
- A plan-of-record document fixes phase order, blockers and the parity definition — AgnosAI's is
  `docs/development/cyrius-port-plan.md`.

---

## 7. Decisions taken (2026-08-19)

| # | Decision | Consequence |
|---|---|---|
| **D1** | **AgnosAI gains a dist target and ships as 2.0.2.** Agnostic consumes it as `[deps.agnosai] modules = ["dist/agnosai.cyr"]` | Single binary. Everything in §3 is prerequisite work |
| **D2** | **Async crews via `agnosai_orchestrator_submit_crew`, with majra owning the queue and 202-then-poll semantics** | Live progress available off the event bus. 202-then-poll is the right shape for long-running crews regardless of who calls it |
| **D3** | **WebGUI is a static HTML/CSS/JS bundle served through sandhi.** A richer GUI comes later; a TUI is optional future work, not scope | Needs a static file handler + mime map written from scratch |
| **D4** | **Full 28 QA tools.** `Page.captureScreenshot` gets added to yantra's CDP surface first, then the CV pipeline is rebuilt on chitra + ranga + rosnet | yantra becomes a prerequisite repo alongside agnosai |
| **D5** | ~~Serve both MCP shapes to preserve SecureYeoman's live 43-tool client, treating `/api/v1/{crews,definitions,presets,gpu/*,a2a/receive}` + X-API-Key as a frozen wire contract~~ — **revised 2026-08-20, see §7.3** | JSON-RPC 2.0 MCP at `/mcp` is the standard shape; the REST shape must now earn its place on merit rather than on a migration constraint |

### 7.3 Revision — Agnostic stands on its own (2026-08-20)

**The premise behind D5 was wrong.** This brief assumed SecureYeoman reaches the engine *through*
Agnostic, which made SY's live 43-tool client a frozen wire contract and forced a second MCP shape
purely to avoid migrating it.

SY can consume **AgnosAI directly** — AgnosAI 2.0.2+ ships a `/mcp` surface, an `/api/v1/a2a/receive`
endpoint, and `dist/agnosai.cyr` for in-process linking. Nothing requires Agnostic to sit in front
of it.

Agnostic is therefore a **product in its own right, not a frontend layer**. What changes:

| Was | Now |
|---|---|
| Two MCP shapes, forced, to avoid migrating SY | JSON-RPC at `/mcp` is the standard; a REST shape ships only if it earns its own justification |
| `/api/v1/*` + X-API-Key a frozen contract | The API is designed for Agnostic's users, on merit |
| M7 gated on "SY green", inverting the usual ordering | Normal ordering — consumer-green comes after the tag |
| Identity option 3: SY as IdP | Weakest of the three — couples the two systems for no delivery benefit if SY is not in the path |
| v1.0 criterion "SecureYeoman green" | "At least one consumer green against the published API" |

This is a **scope reduction and a design freedom**, not new work. The one thing it does not license
is gratuitously breaking SY. If SY is ever pointed at Agnostic, the answer is a **compatibility
shim** — an additive translation layer over the published API — built then, against a real
requirement. It is explicitly out of scope for v1.0.

The design obligation that follows is small but real: **keep the seam shim-able.** Route tables and
request decoding stay separable from handler logic, so an alternate surface can be mounted without
touching either. Cheap to preserve now, expensive to retrofit.

⚠ It also removes the keep-alive worry's urgency (§5.2): that entry is justified by "SecureYeoman's
43-tool client polls". Agnostic→AgnosAI/hoosh calls use `sandhi_http_pool_*` client-side pooling and
are unaffected either way.

### 7.1 Prerequisite work in other repos

| Repo | Change | Version |
|---|---|---|
| `agnosai` | `[lib]` stanza + `cyrius distlib` → `dist/agnosai.cyr` (§3). Fix the hardcoded `AGNOSAI_VERSION = "1.1.0"` at `src/server/routes/mod.cyr:44` while there | 2.0.1 → **2.0.2** |
| `yantra` | `Page.captureScreenshot` on the CDP surface (D4) | TBD |

### 7.2 Still open

1. **Identity.** AgnosAI has a shared bearer secret or RS256 JWT, off by default. Agnostic needs
   users, roles, OAuth, API keys, tenant CRUD. Own it (patra + sigil), delegate to kavach, or make
   SecureYeoman the IdP with Agnostic only validating SY-issued JWTs.
2. **Preset canon.** The two sets differ — Agnostic has `complete-lean`, `quality-performance`,
   `quality-security`; AgnosAI has `security-lean/standard/large`. Which is canonical, and does
   Agnostic keep its own preset store given AgnosAI serves 18 over `GET /api/v1/presets`?
3. **PDF reports.** `mneme/src/io_export_pdf.cyr` works and is proven to run — lift it, wait for
   bayan's roadmapped `bayan_pdf_*`, or ship HTML+CSV+JSON only.
