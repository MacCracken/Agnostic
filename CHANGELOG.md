# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added — M2, the crew surface: submit, poll, cancel, progress

**261 new assertions across 4 suites** (490 total across 12), 0 failed. All three gates green.
Verified live over a socket, not only under test.

AgnosAI is linked **in-process**, so there is no transport here — no client, no URL, no retry
policy. That removes a whole class of the oracle's defects by construction and leaves the ones that
were never about transport.

- **`src/engine/outcome.cyr`** — the result type the milestone turns on. Carries status **and**
  error **and** the engine-assigned crew id **and** the result set. The oracle's `BackendResult`
  had a `.status` that **no caller anywhere in the codebase read**.
- **`src/engine/ledger.cyr`** — what Agnostic remembers about the crews it submitted, and where a
  terminal status is latched.
- **`src/engine/request.cyr`** — one task model, allow-list decoded, dependency graph validated.
- **`src/engine/crew.cyr`** — the orchestrator bridge: submit, poll, cancel.
- **`src/routes/crews.cyr`** — `POST /api/v1/crews` (**202**), `GET /api/v1/crews/{id}`,
  `POST /api/v1/crews/{id}/cancel`, `GET /api/v1/crews/{id}/events`.

**202-then-poll**, not the engine's inline shape. `agnosai_route_create_crew_a` calls the blocking
`agnosai_orchestrator_run_crew` to keep parity with its Rust oracle, so a `POST` holds a worker for
the whole run. Agnostic submits and returns the id.

### Fixed — the four `ORACLE-AUDIT.md` §3 defects, designed out rather than avoided

- **§3.1 — a failed crew reported as completed.** `_agnostic_outcome_normalise` demotes a
  COMPLETED-with-no-results to FAILED *before* the record exists, so the vacuous success is never
  observable. ⚠ **This is not a Python-ism.** `agnosai_crew_runner_run` sets `COMPLETED` and only
  downgrades inside a loop over `results` — over an empty set the loop body never runs and the
  status stands. `all([])` in Cyrius, one dependency away.
- **§3.2 — cancel addressing an id the engine never saw.** Every id originates in
  `agnosai_crew_new`. Agnostic mints none, so there is no local UUID to substitute. A refusal from
  the engine is **returned, not discarded**, and the ledger is not relabelled.
- **§3.3 — two structurally different task models.** `tasks` is required and non-empty, there is no
  fallback path, and an unlisted key is a 422 naming it. The oracle's fallback fired on every
  request because its model declared no `tasks` field at all.
- **§3.4 — a terminal state overwritten by a later, wronger one.** `agnostic_ledger_latch` refuses
  to write over a terminal status — in one guard, at the only place a status is stored.

### Fixed — two engine behaviours that only bite the async path

Neither is in the 85 audited oracle defects; both were found building M2.

- **A cyclic DAG submitted asynchronously reports `pending` forever.**
  `agnosai_crew_runner_run` returns 0 on exactly one arm, and `_agnosai_orch_finish_err` then
  returns **without touching the crew map** — which `_agnosai_orch_register` has already seeded with
  PENDING. The blocking caller sees the 0; `_agnosai_orch_submit_thread` discards it. Closed at the
  front door: `agnostic_crew_req_has_cycle` rejects the graph before submission, so the arm is
  unreachable through Agnostic.
- **A finished crew can be evicted and then 404.** `_agnosai_orch_evict_locked` drops **every**
  finished crew once the registry holds 1000, so a successful run becomes indistinguishable from a
  typo'd id. The ledger answers from its own latched outcome; `AGNOSTIC_LEDGER_MAX` is deliberately
  above the engine's cap, and a suite asserts that ordering.

### Added — placeholder mode is disclosed, because nothing else can distinguish it

With no `AGNOSTIC_LLM_URL`, `agnosai_execute_task` takes its `client == 0` arm and
`_agnosai_crew_placeholder_result` echoes the task description back as output with status
`COMPLETED`. A crew of echoes therefore normalises to `completed`, every task complete — and **no
property of the result type can tell it from real model output**.

Closed by disclosure rather than by type: `engine_mode` is on every submit and poll response, and
mount logs a WARN.

### Removed — `AGNOSTIC_CREW_MAX_CONCURRENT_TASKS`, a knob that did nothing

Verified against the bundle: `agnosai_resource_budget_max_concurrent_tasks` has no reader outside
its own accessor and the budget serialiser, and `agnosai_orchestrator_budget` has **zero** call
sites. The field is stored, serialised, and enforced by nothing. Shipping it would have sold an
operator a concurrency ceiling that does not exist. `AGNOSTIC_CREW_TIMEOUT_SECS` is kept because
`max_duration_secs` genuinely *is* read, by `agnosai_orchestrator_timeout_secs`.

The ceiling that does work is per-request `max_concurrency` on process `parallel` — which is
accepted only alongside `parallel`, because a field that is accepted and then has no effect is the
same defect in miniature.

### Added — `scripts/check-log-lengths.py`, after two silent miscounts shipped

sakshi takes `(pointer, length)` pairs, so every log message's byte count is hand-written and
nothing checked it. Both failure modes are silent, and both were in one commit: one call declared
76 for a 75-byte message and shipped the **NUL terminator inside a JSON string**; another declared
45 for 46 and **truncated** the message by a character. Not a compile error, not a lint warning, and
invisible to suites that assert on handler behaviour rather than log text.

Wired into `check-clean.sh`. Mutation-verified: changing any declared length by one fails it.

### Changed — `check-symbols.sh` rule 3 now scans enum members on both sides

It compared only `^(fn|var)` against `lib/`. Cyrius enum qualifiers are **cosmetic** — `Backend.WASM`
and `KavachBackend.WASM` both resolve to the bare member `WASM` — so a `src/` enum member colliding
with a `lib/` one silently replaced it for the whole program, with no diagnostic from compiler or
linter. That is the same mechanism as the `BACKEND_COUNT` memory-safety defect below, in the one
declaration kind the gate did not cover. M2 adds ~50 enum members; all verified collision-free.

Mutation-verified: injecting a member named `AGN_CREW_ID` fails the gate, naming both sites.

### Added — a mount-time warning where the two size ceilings interact

A request body is parsed into the per-request arena, whose exhaustion policy is `ARENA_FULL_SPILL` —
overflow is satisfied from the global bump, which has **no `free()`**. The defaults make this
reachable (64 KiB arena, 1 MiB body limit), and the engine's own caps admit several megabytes of
entirely legal crew request. Not a startup failure, since the safe configuration depends on the
deployment; an operator gets a warning naming the arena size.


### Changed — agnosai 2.0.3 → 2.0.4, closing a memory-safety defect in this binary

Agnostic is the binary where the defect actually lived, because Agnostic is what links kavach and
ai-hwaccel together — transitively, through agnosai.

Both libraries defined `var BACKEND_COUNT`, 10 and 18. Cyrius has one flat symbol namespace with
last-definition-wins and is **silent** on a duplicate `var`, so the constant resolved to **18** while
kavach used it as the bounds check in `_backend_fp` over a **10-slot** table (`_backend_table[320]`
at `BACKEND_SLOT_SIZE = 32`). The guard admitted ids 0–17; `_backend_slot(17)` sits at byte 544, 224
bytes past the end, and `backend_dispatch_exec` then calls the result as a function pointer.
Renamed upstream to `KAVACH_BACKEND_COUNT` / `AIHW_BACKEND_COUNT` in kavach 3.11.15 and
ai-hwaccel 2.3.18, which agnosai 2.0.4 folds.

### Added — `tests/deps_symbols.tcyr`, a guard for the class rather than the instance

**14 assertions.** The instance is fixed upstream; this suite exists because *nothing caught it*.
The compiler warns on a duplicate `fn` and is silent for `var`, and every `check-symbols.sh` in the
ecosystem — including this repo's — scans `src/` only. A collision between two dependencies inside
`lib/` is therefore invisible to the compiler and the linter simultaneously, and Agnostic is the
repo where such a collision lands.

The suite pins both counts as distinct values, ties kavach's guard to its table's real slot count,
and records the out-of-bounds arithmetic the old value produced. Mutation-tested: three mutants —
restoring 18, resizing the table to 18 slots, and drifting an enum member — each killed.

⚠ It also pins the enum *members* (`PROCESS`, `WASM`, `OCI`, `NOOP`), because in Cyrius an enum
qualifier is **cosmetic** — `Backend.WASM` and `KavachBackend.WASM` both resolve to the member
`WASM`, asserted here directly. The upstream type rename therefore protected nothing on its own;
those members remain generic and unprefixed, and a future library defining `WASM` would collide the
same silent way.

### Fixed — `lib/vani.cyr` did not match the pinned toolchain snapshot

Pre-existing and unrelated to the dep bump: the vendored copy matched **no** installed toolchain, so
`scripts/check-clean.sh` failed at HEAD. `vani` is not in `[deps].stdlib` and `src/` has zero
references to it, but the snapshot check requires every file in the pinned snapshot to be present
*and* byte-identical, so removing it would fail too. Re-synced from the 6.5.32 snapshot.

⚠ Provisioning was done with the **pinned** toolchain binary rather than the PATH wrapper, which had
drifted to 6.5.33. `lib sync` and `deps` provision from the *installed* toolchain, not the manifest
pin, so syncing under drift is how a lock that CI cannot reproduce gets written.

### Added — M1, the HTTP foundation

The first milestone where untrusted bytes reach a buffer. **215 assertions across 7 suites**, 0
failed; all CI gates green. Verified live over a socket, not only under test.

- **`src/config.cyr`** — environment config, strictly parsed. A malformed value **refuses to start**
  rather than silently defaulting, because an operator discovering in production that
  `AGNOSTIC_PORT` never applied is worse than a startup failure that names the problem.
- **`src/strcase.cyr`** — ASCII case folding. The stdlib has no case-insensitive compare and
  `str_lower_cstr` allocates; comparing an env value to a literal should not.
- **`src/trace.cyr`** — thread-local W3C trace ids. sakshi's is a process global, so under a worker
  pool concurrent requests would overwrite each other's id and misattribute every log line.
- **`src/log.cyr`** — sakshi emit hook rendering one JSON object per event, formatter split out as a
  pure function so tests assert bytes without a pipe.
- **`src/http/{status,response,codec,router}.cyr`** — status vocabulary, handler return type,
  allow-list decoding, route table with a `:name` matcher.
- **`src/routes/health.cyr`** — `/health` liveness and `/ready` readiness with a check registry.
- **`src/server/serve.cyr`** — the sandhi adapter: arena/SPILL wiring, cstring→`Str` boundary,
  `signalfd` graceful shutdown.

### Decisions

- **ADR 0001** — health and readiness are separate probes. The oracle's `/health` pings Redis and
  RabbitMQ and 503s when they are down; under an orchestrator that manufactures an outage, since one
  Redis blip fails liveness on every replica and restarting cannot fix a dependency.
- **ADR 0002** — Daimon Tier 1 deferred. It cannot be implemented as written: daimon serves no agent
  heartbeat route, and registration for an externally-started process keys supervisor maps to pid 0.
  Zero first-party projects perform it at runtime, including the one the standard names as canonical.
- All six open port decisions closed — identity (own it thin, adapted from SecureYeoman's Cyrius
  probe), preset canon (Agnostic's is canonical), PDF (wait for `bayan_pdf_*`), release shape (one
  total release), Daimon (deferred), MCP transports (both shapes stand, on merit).

### Fixed — three oracle defect classes designed out, each locked by a mutation-tested assertion

- **Silent config fallback.** The oracle reused its u16 port parser for a rate limit, so any value
  above 65535 fell back to the default with no error. `parse_bounded` is deliberately a separate
  function; aliasing it back to `parse_port` fails two named assertions.
- **`extra='ignore'` field dropping.** Pydantic silently discarded 14 fields including `gpu_strict`,
  turning a hard-fail GPU requirement into a silent CPU fallback, and elsewhere ate an entire
  `tasks` array. Replacing the allow-list check with `return 1` fails
  *"an unlisted field is rejected, not silently dropped"*.
- **Liveness conflated with readiness.** See ADR 0001. The suite asserts `/health` stays 200 with a
  failing dependency registered.

### Fixed — two upstream defects avoided that the reference implementation still has

- `GET /health?probe=1` returns 200. AgnosAI never strips the query string, so its own health
  endpoint 404s for any caller appending a cache-buster.
- `/ready` reports a version **derived** from `${file:VERSION}`. AgnosAI hardcodes its equivalent and
  has reported 1.1.0 since shipping 2.0.x.

### Filed upstream

- `cyrius 2026-08-20-pkgver-not-visible-in-included-files` — `CYRIUS_PKG_VERSION` resolves only in
  the entry file's own text; any `include`d file referencing it fails to compile. That is where the
  symbol is least useful, since `/version` and `/ready` handlers live in modules. Worked around by
  threading it from `main.cyr` at mount, so the version stays derived rather than hardcoded.

## [0.1.0]

### Hardening — P(-1) pass complete

`first-party-standards.md:817` requires the audit-and-tighten pass before any feature work: *"Build
features on an unaudited foundation and every feature inherits the foundation's shortcuts."*
Exit criteria per `:869` all met — audit-clean, fmt/lint/vet/deny clean, security clean, baseline
benchmarks captured.

- `docs/audit/2026-08-20-audit.md` — the eight-point security process worked against the code that
  exists rather than the code that is planned. **0 CRITICAL / 0 HIGH / 0 MEDIUM / 2 LOW**, both LOW
  closed in the pass. Six of the eight points are N/A on a 34-line scaffold with no external input,
  no buffers, no file handling and no subprocess execution — so each N/A row records **which
  milestone re-opens it**, making the document a checklist for M1–M9 rather than a one-time
  clearance.
- `scripts/bench-history.sh` — written to the full four-clause contract at
  `first-party-standards.md:443-447`. The sibling implementation drops two of them: it records no
  commit hash (so a row cannot be attributed to code, defeating the point of a history trail) and
  emits no Markdown table. This one writes `date,version,commit,branch,benchmark,time_ns` and
  regenerates `BENCHMARKS.md` with human-readable units.
- Baseline captured — `noop` at 2 ns. This is the starting line for the 3-point
  baseline → optimized → current trend.

### Fixed — LOW-1, unprefixed globals in the generated harnesses

`cyrius init` emitted `var r = main();` into the bench and fuzz harnesses and `var exit_code` into
the test suite. Cyrius has one flat symbol table with last-definition-wins, and a test binary links
all of `lib/`, which exports ~180 unprefixed names.

Verified *not* currently exploitable — `lib/` declares no single-letter or `exit_code` globals — so
this was latent, not live. But the dependency set is about to grow by six packages, and the same
class caused a real upstream incident (four duplicated enum constants, three with different values,
three of them struct sizes passed straight to `alloc()`). Renamed to `_agnostic_{bench,fuzz,test}_exit_code`.

LOW-2 (exit-code masking in `.bcyr`/`.fcyr`, which do not clamp `& 0xFF` the way the `.tcyr` does)
was assessed and **accepted without a code change**: neither harness returns a failure count, so no
path to a value ≥256 exists. Recorded so the first harness returning a count adds the clamp.

### Added — roadmap through v1.0

`docs/development/roadmap.md` replaced its placeholder milestones with M0–M9 in dependency order,
each carrying its gates, its prerequisite repos, and the audit points it re-opens. Three decisions
are marked open and one milestone (M5, identity) is explicitly **blocked** on the user answering
it — per `cyrius/CLAUDE.md:66`, that is settled before the milestone opens rather than discovered
inside it.

### Added
- Initial project scaffold, generated by `cyrius init --language=none .` against
  the Cyrius 6.5.32 toolchain. The Python implementation is retained at
  `python-port/` as a behavioural oracle and is never built or shipped —
  see `ORACLE-AUDIT.md` for the 85 verified defects in it.
- Root docs the scaffolder does not emit: `CONTRIBUTING.md`,
  `CODE_OF_CONDUCT.md`, `SECURITY.md`. `SECURITY.md` is written for Agnostic's
  own surface (inbound API, delegated execution, targets under test, stored
  artefacts, credentials) rather than adapted from a sibling.
- `scripts/check-symbols.sh` and `scripts/check-clean.sh`, adapted from AgnosAI.
  Two inherited assumptions had to be removed: a `gen-presets.sh` generated-source
  check for a file this repo does not have, and a `deps --verify` step that
  assumed a lockfile — Agnostic declares no git deps yet, and
  `first-party-standards.md:135` makes "no lockfile" the documented default. The
  lock check re-arms automatically once a `[deps.NAME]` block appears.
- `[release]` manifest section declaring `bins` and `cross_bins`.

### Changed — CI raised to the first-party standard

The scaffolded `ci.yml` had a single 4-step job. It now carries the three jobs
`first-party-standards.md:364-386` requires — `build`, `security`, `docs` — with
fmt/lint/vet/deny via `check-clean.sh`, the symbol gate, a DCE build, ELF
verification, an aarch64 cross-build, and `cyrius bench` behind
`continue-on-error`.

`release.yml` gained the aarch64 build, made fatal rather than skipped: the
standard's DON'T list (`:963`) names "release without aarch64 builds" explicitly,
and a tagged release that silently ships one architecture is the failure that
guards against. Both binaries are now checksummed and attached, along with
benchmark results per `:419`.

⭐ **New gate: toolchain drift is fatal.** `cyrius lib sync --full` and
`cyrius deps` provision from the *installed* toolchain, not the manifest pin, so
a developer whose wrapper has drifted ahead writes a `lib/` and `cyrius.lock`
describing a version CI will never install — and every local build stays green
because the polluted lib agrees with the polluted lock. This is exactly how
AgnosAI 2.0.2 reached main with a 6.5.30-shaped lock under a 6.5.27 pin and lost
the entire stdlib in CI. The CLI already prints
`manifest-pin: X (drift — wrapper is Y)`; this treats that line as fatal in both
workflows. Mutation-verified in both directions: injecting a pin mismatch fails
the gate, restoring it passes.

Relatedly, the lockfile step **fails** on a mismatch rather than emitting a
`::notice` and continuing, which is what let the bad lock through upstream.

### Fixed
- The scaffolder's generated entry point declared `var r = main();` — a bare
  unprefixed top-level global in Cyrius's single flat symbol table.
  `check-symbols.sh` failed on it immediately; renamed `_agnostic_exit_code`.
  Filed against the toolchain rather than patched, together with the missing
  scaffold files and the absent `--language=python` port mode:
  `cyrius/docs/development/issues/2026-08-20-cyrius-port-language-python.md`.
