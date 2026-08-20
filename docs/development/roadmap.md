# agnostic — Roadmap

> Milestone plan through v1.0. State lives in [`state.md`](state.md);
> this file is the sequencing — what ships, in what order, against
> what dependency gates.

## Shape of the port

**Agnostic 1.0.0 is roughly a third of the Python tree.** AgnosAI owns the entire *engine* tier —
crews, tasks, agents, DAG/priority scheduling, agent scoring, LLM routing through hoosh, the tool
registry with four sandbox tiers, fleet coordination, multi-tenant budgets, approvals, the audit
chain, durable state, SSE, Prometheus and OTLP telemetry, RL learning, definition
versioning/packaging, the crew assembler and the preset library.

What remains is the **product** tier: the HTTP and MCP surfaces consumers bind to, the QA domain
tools, identity and tenancy, persistence and reporting, and the GUI. Sequencing below follows
dependency order, not the Python tree's layout — see [`../../CYRIUS-PORT-BRIEF.md`](../../CYRIUS-PORT-BRIEF.md)
for the three-way split of ported / delegated / dropped.

The oracle at `python-port/` is a **behavioural reference, not a specification**.
[`../../ORACLE-AUDIT.md`](../../ORACLE-AUDIT.md) records 85 verified defects in it; several of its
paths are wrong, and reproducing them faithfully would reproduce the bugs. Check that document
before porting any behaviour.

## v1.0 criteria

- [ ] Public API frozen — every exported symbol documented and tested
- [ ] `python-port/` retired — the Cyrius tree has equal or better coverage
      (`first-party-standards.md:53`). ⚠ The benchmark half of that rule cannot be satisfied as
      written: `ORACLE-AUDIT.md` §4 shows the oracle's published numbers are invalid, so parity is
      assessed on coverage and behaviour, not on its timings.
- [ ] Benchmarks captured in `BENCHMARKS.md` with a CSV trail
- [ ] SecureYeoman green against the frozen wire contract (see M7)
- [ ] CHANGELOG complete from v0.1.0 onward
- [ ] Security audit pass re-run (`docs/audit/YYYY-MM-DD-audit.md`)
- [ ] Zugot recipe published (`zugot: marketplace/agnostic.toml`)

## Milestones

### M0 — Scaffold + P(-1) hardening (v0.1.0) — ✅ 2026-08-20

- `cyrius init --language=none .` scaffold, GPL-3.0-only, pin 6.5.32
- Root docs, `scripts/{check-symbols,check-clean,version-bump,bench-history}.sh`
- CI raised to the three spec-required jobs (`build`, `security`, `docs`), plus a
  **fatal toolchain-drift gate** — the failure mode that broke AgnosAI 2.0.2 in CI
- P(-1) complete: audit-clean, 0 CRITICAL/HIGH/MEDIUM, baseline benches seeded

### M1 — HTTP foundation (v0.2.0)

The first milestone where untrusted bytes reach a buffer, so it re-opens audit points 1–4
simultaneously.

- `sandhi` HTTP/1.1 server, `:name` routing, per-request arena with SPILL policy
- Config from environment; `sakshi` structured logging and trace ids
- `/health`, `/ready`
- `bayan_json_v_*` request/response codecs with allow-list decoding

**Gates:** arena-exhaustion path tested (a `Str` of 0 is indistinguishable from a valid one — there
is no error channel through the `_a` families). Security audit re-run.

### M2 — AgnosAI integration (v0.3.0)

- `[deps.agnosai]` → `dist/agnosai.cyr`, linked in-process
- Crew submit / status / cancel via `agnosai_orchestrator_submit_crew` (**D2**)
- `majra` owns the queue; 202-then-poll semantics
- Live progress off the event bus

**Gates:** ⚠ the four failure modes in `ORACLE-AUDIT.md` §3 must be designed out, not inherited —
a result type that carries status *and* error *and* the remote id; terminal states that stay
terminal; one task model rather than two; cancellation that stops work rather than relabelling a
record.

**Unblocked:** D1's prerequisite shipped — AgnosAI 2.0.2 added the `[lib]` stanza and
`dist/agnosai.cyr`; 2.0.3 moved to Cyrius 6.5.31.

### M3 — Definitions, presets, agents (v0.4.0)

- Agent definition CRUD; preset listing
- Every field either forwarded or explicitly rejected — never silently dropped
  (`ORACLE-AUDIT.md` §2.2 lists six fields the oracle dropped, `gpu_strict` being the sharp one:
  a hard-fail GPU requirement became a silent CPU fallback)

**Open decision:** preset canon. The two sets differ — Agnostic has `complete-lean`,
`quality-performance`, `quality-security`; AgnosAI has `security-lean/standard/large`. Does
Agnostic keep its own store given AgnosAI serves 18 over `GET /api/v1/presets`?

### M4 — Persistence + audit chain (v0.5.0)

- `patra` for sessions, crews, results, tenants
- `libro` tamper-evident audit chain
- Path-traversal validation on every externally-derived path (re-opens audit point 6)

⚠ `patra` is an embedded single-file store, `flock`-arbitrated, with **no client/server mode** —
the oracle's multi-container "everyone talks to postgres" topology cannot be reproduced.

### M5 — Identity + tenancy (v0.6.0)

- API keys (`sigil` SHA-256 + `ct_eq_bytes`), tenant CRUD, roles
- Webhook HMAC signatures

⛔ **Blocked on an open decision.** Own it (patra + sigil), delegate to kavach, or make
SecureYeoman the IdP with Agnostic only validating SY-issued JWTs. Per `cyrius/CLAUDE.md:66`
("When stuck, ASK the user"), this is answered *before* M5 opens, not discovered inside it.

### M6 — QA tool surface (v0.7.0)

- All 28 QA tools (**D4**). The 5–8 figure in `first-party-standards.md:625` is a soft guideline
  for typical projects, not a ceiling for platform-scale ones.
- Sandboxing **delegated to kavach** — `first-party-standards.md:76`: *"kavach owns the sandbox,
  not the application."* The oracle hand-rolled an rlimit subprocess; do not repeat it.
- Browser automation via `yantra`; CV pipeline on chitra + ranga + rosnet

**Prerequisite:** `yantra` needs `Page.captureScreenshot` on its CDP surface.

### M7 — MCP dual surface + A2A (v0.8.0)

- REST at `/api/v1/mcp/invoke` for SecureYeoman's live 43-tool client
- JSON-RPC 2.0 at `/mcp` for new consumers (**D5**), on `bote`
- A2A callback endpoint

🔒 **Frozen wire contract:** `/api/v1/{crews,definitions,presets,gpu/*,a2a/receive}` and X-API-Key
auth. SecureYeoman is live against these *now* — this milestone must not break it, which inverts
the usual "consumer green comes after the tag" ordering.

### M8 — Reports (v0.9.0)

- HTML + CSV + JSON export; quality trends and comparison reports

**Open decision:** PDF. Lift `mneme/src/io_export_pdf.cyr` (works, proven to run), wait for bayan's
roadmapped `bayan_pdf_*`, or ship without.

### M9 — WebGUI (v1.0.0)

- Static HTML/CSS/JS bundle served through sandhi (**D3**)
- Needs a static file handler + mime map written from scratch

## Release shape

`cyrius/CLAUDE.md:96` permits 1–2 releases for a multi-phase arc; AgnosAI used two. The natural cut
is **M1–M7** (headless: API + both MCP shapes — everything SecureYeoman needs) then **M8–M9**
(reports + GUI). The user owns that call.

## Out of scope for v1.0

- **A TUI.** D3 scopes the GUI to a static bundle; a richer GUI comes later and a TUI is optional
  future work.
- **Re-implementing anything AgnosAI owns.** If a capability lives in the engine tier, Agnostic
  calls it — it does not fork it.
- **Kubernetes topology parity.** The oracle's multi-container postgres deployment does not survive
  the move to embedded `patra`.
- **The oracle's benchmark numbers as a performance target** — they are invalid
  (`ORACLE-AUDIT.md` §4). The Cyrius line starts its own baseline.
