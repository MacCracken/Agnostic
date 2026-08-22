# agnostic — Current State

> Refreshed every release. CLAUDE.md is preferences/process/procedures
> (durable); this file is **state** (volatile).
> Last refreshed: 2026-08-22, after M4 + agnosai 2.0.5 uptake + M5 part 1.
>
> **Picking this port up?** Start at [`handoff.md`](handoff.md) — orientation,
> the build procedure that avoids an unreproducible lock, and what M5 must do.
> This file is the numbers.

## Version

**0.1.0** — scaffolded 2026-08-20 via `cyrius init`. No releases yet; **1.0.0**
is the target cut, not 2.x. The Cyrius line is the first SemVer line — the
Python line was CalVer (`2026.3.18`).

## Toolchain

- **Cyrius pin**: `6.5.34` (`cyrius.cyml [package].cyrius`). Installed wrapper
  matches — **no drift**.
- ⚠ **The pin and `[deps.agnosai]` move TOGETHER.** agnosai 2.0.5 carries
  bote 3.3.3 → libro 2.8.10, which declares `[deps.patra] = 1.13.10`, and
  `cyrius deps` overlays a declared dep's copy on top of the `lib sync --full`
  snapshot on every resolve. Only a Cyrius folding 1.13.10 (**6.5.34**) leaves
  `lib/` matching the pin, and `check-clean.sh` allows no file to differ. Bumping
  one alone goes red in either direction — this is what kept agnosai's `main` red
  before 2.0.5. ⛔ The wrong fixes, both tried and rejected: a `[deps.patra]` hold
  in this manifest, and a `check-clean` allowance.
- ⚠ **An earlier version of this section claimed `6.5.32/lib` and `6.5.33/lib`
  were byte-identical. That was wrong** — they differ in `lib/vani.cyr`. Check
  what a release folds with `git show <tag>:lib/<mod>` in `~/Repos/cyrius`.
- ⚠ **`~/.cyrius/versions/<pin>/bin/cyrius` does NOT pin `cycc`.** It resolves the
  compiler through `$CYRIUS_HOME/bin` → `~/.cyrius/current`, not relative to
  itself and not via `PATH`. To certify against a pin the wrapper does not match,
  build a `CYRIUS_HOME` shim (`bin`, `lib`, `versions`, `deps` symlinks plus a
  `current` file) and confirm the drift line is absent. Filed:
  `cyrius/docs/development/issues/2026-08-22-versioned-wrapper-does-not-pin-cycc.md`.
- ⚠ **Never read `~/.cyrius/versions/<V>/lib/` as ground truth.** A concurrent
  session working on cyrius rewrites those files in place; that produced a wrong
  diagnosis on 2026-08-22 ("6.5.33 folds patra 1.13.10" — it does not).

## Dependencies

`[deps.agnosai]` is **tag-only — no `path`**. `path` beats `tag` when a checkout is
present, so a local resolve silently vendors the sibling's work-in-progress into
`lib/` and the lock: content matching no tag, which CI cannot fetch. Deleting it
took the lock from **1 commit pin to 9**.

| dep | pin | how it arrives |
|---|---|---|
| `agnosai` | **2.0.5** | direct, `git` + `tag` |
| `sigil` | 3.12.9 | transitive via agnosai; also declared in `[deps].stdlib` |
| `bote` | 3.3.3 | transitive |
| `libro` | **2.8.10** | transitive via bote — the audit chain |
| `patra` | **1.13.10** | folded into the 6.5.34 stdlib |
| `kavach` | **3.12.2** | transitive |
| `majra` / `ai-hwaccel` / `tyche` | 2.6.7 / 2.3.18 / 1.0.1 | transitive |

⚠ **Two work-arounds in `src/engine/store.cyr` are now removable and still present.**
libro 2.8.9 fixed `PatraStore` faulting off the opening thread (so audit verification
need no longer run only at open) and patra 1.13.10 stopped `patra_init` clobbering the
host log level. Both fixes have landed here; removing the work-arounds is deliberately
left as its own change.

## Source

**M4 complete; M5 complete** — 36 files, 9530 lines, 578 top-level
definitions, all `agnostic_*`-prefixed. 837 of those lines are the generated
`src/presets_data.cyr`.

**Tests: 22 suites, 1,103 assertions, 0 failed** (`cyrius test`). Gates green:
`check-symbols.sh` (**now 4 rules** — Rule 4 is the new `lib/`↔`lib/` constant
check), `check-clean.sh`, `deps --verify` 115/0.

**M5 — identity and tenancy — is done.** `src/auth/` holds credential primitives
(`crypto`), users and API keys (`store`), HS256 tokens (`jwt`), the static
role→permission table (`perm`), tenancy and key-prefixing (`tenant`), the
credential→principal path (`authn`), login-abuse controls (`ratelimit`) and
callback signatures (`webhook`). The dispatch ladder's auth rung at
`src/http/router.cyr` is **wired**, not a comment.

⚠ **`AGNOSTIC_AUTH` defaults to `off`, and `agnostic_serve_mount` REFUSES TO
START with it off on any bind but loopback.** There is no bootstrap route yet, so
nothing could authenticate on a fresh deployment — the refusal is what keeps that
from being fail-open rather than a promise that it is not.

⚠ **Every security property in `src/auth/` is mutation-verified.** The suites are
written so that removing a guard breaks a named assertion: the bucket re-checks,
the JWT signature compare and `exp` rule, the permission table, tenant unscoping,
the role-from-row rule, the rate limiter's position before Argon2, and the
webhook timestamp being inside the MAC. Re-run those mutations before trusting a
refactor of any of it.

| module | role |
|---|---|
| `src/config.cyr` | env config, strictly parsed; a malformed value refuses to start |
| `src/strcase.cyr` | ASCII case folding without allocating |
| `src/trace.cyr` | thread-local W3C trace ids (sakshi's is a process global) |
| `src/log.cyr` | sakshi emit hook, one JSON object per event |
| `src/http/{status,response,codec,router}.cyr` | status table, response records, JSON allow-list codec, route matching |
| `src/engine/outcome.cyr` | the result type carrying status + error + engine id + results |
| `src/engine/ledger.cyr` | what Agnostic remembers about submitted crews; the terminal latch |
| `src/engine/request.cyr` | one task model, allow-list decoded, DAG validated |
| `src/engine/crew.cyr` | the orchestrator bridge — submit, poll, cancel |
| `src/engine/reject.cyr` | how a request says no; the typed-field readers |
| `src/engine/agentdef.cyr` | **one** agent model — forwarded, retained, or refused |
| `src/engine/definitions.cyr` | the definition store — **patra-backed** since M4 |
| `src/engine/store.cyr` | the one patra handle the durable tables share |
| `src/engine/crewstore.cyr` | terminal crew outcomes, durable |
| `src/engine/audit.cyr` | the tamper-evident trail, libro over patra |
| `src/engine/presets.cyr` | the canonical preset library, parsed once at mount |
| `src/presets_data.cyr` | **generated** — the 18 documents as Cyrius literals |
| `src/routes/health.cyr` | `/health` and `/ready` |
| `src/routes/crews.cyr` | the crew surface |
| `src/routes/definitions.cyr` | agent definition CRUD |
| `src/routes/presets.cyr` | the preset surface, read-only |
| `src/server/serve.cyr` | the only module that touches a socket |
| `src/app.cyr` | the canonical include order — **no definitions** |
| `src/main.cyr` | entry point alone; includes `app.cyr` |

⚠ **`src/app.cyr` exists so adding a route stops breaking every suite.** The
include order used to live in `main.cyr` and every suite reaching the router
reproduced it, so a new route module failed them all with "undefined function"
rather than "missing include" — three times across M2 and M3. `main.cyr` cannot
serve that role itself: its two trailing top-level statements run at include time
and would start a server inside a suite.

The crew surface, and what each code means:

| route | codes |
|---|---|
| `POST /api/v1/crews` | **202** accepted · 400 semantic · 422 shape · 503 engine down |
| `GET /api/v1/crews/{id}` | 200 · 404 never submitted · 422 malformed id |
| `POST /api/v1/crews/{id}/cancel` | 200 · 404 · **409 already terminal** · 422 · 503 |
| `GET /api/v1/crews/{id}/events` | 200 · 404 · 422 |
| `GET /api/v1/presets` | 200 — summaries, not documents |
| `GET /api/v1/presets/{name}` | 200 · 404 unknown name |
| `GET /api/v1/agents/definitions` | 200 |
| `POST /api/v1/agents/definitions` | **201** · 400 · **409** · 422 · **507** |
| `GET /api/v1/agents/definitions/{key}` | 200 · 404 · 422 |
| `PUT /api/v1/agents/definitions/{key}` | 200 · 400 · 404 · 422 |
| `DELETE /api/v1/agents/definitions/{key}` | 200 · 404 · 422 |

⚠ **201 for a definition, 202 for a crew.** A crew is accepted work that is not
finished; a definition *is* complete when the call returns. **No upsert** in
either direction: `POST` to an existing key is 409, `PUT` to an absent one is 404
— an upsert turns a typo'd key into a second silently-created definition.

⚠ `GET /api/v1/crews` is in the table with no handler, so it answers **405**
rather than a 404 claiming the collection does not exist. A listing endpoint
needs pagination and a tenancy scope; both arrive with M4/M5.

The Python implementation is retained at `python-port/` as a behavioural oracle.
It is never built or shipped, and it is **not** a specification —
[`ORACLE-AUDIT.md`](../../ORACLE-AUDIT.md) records 86 verified defects in it.

## Tests

**16 suites, 771 assertions, 0 failed** (`cyrius test`, run under the pin).

⚠ Counts here are assertion-suite lines only. `cyrius test`'s final
`N passed, 0 failed` line is the **suite** tally, not a suite — earlier figures
in this repo (`222`) and in agnosai (`8,038`) double-counted it.

- `tests/{agnostic,codec,config,health,log,router,trace}.tcyr` — M1 coverage (7 suites, 215 assertions)
- `tests/deps_symbols.tcyr` — **14 assertions**, cross-dependency symbol integrity;
  see Hardening below
- `tests/outcome.tcyr` — **63 assertions**, the result type. Carries the §3.1 barrier:
  an engine COMPLETED with an empty result set must demote to FAILED
- `tests/ledger.tcyr` — **53 assertions**, the §3.4 barrier: a terminal status
  cannot be moved, in either direction, by any later observation
- `tests/crew_request.tcyr` — **92 assertions**, the §3.3 barrier: `tasks` is
  required, there is no fallback, and a cyclic graph is refused before submission
- `tests/crews_route.tcyr` — **59 assertions**, the surface end to end, including
  the §3.2 barrier: an id we never submitted is a 404 that relabels nothing
- `tests/crewstore.tcyr` — **25 assertions**, terminal-only persistence, written
  once, and durable across a reopen
- `tests/audit.tcyr` — **35 assertions**, the trail: durable across a reopen, and
  a byte edited on disk is **detected** with the failing entry named
- `tests/agentdef.tcyr` — **106 assertions**, the one agent model: every field
  forwarded, retained or refused by name, plus the store's no-upsert and
  never-evict policies
- `tests/presets.tcyr` — **71 assertions**, the canonical library: all 18 parse,
  the declared order, the off-canon `complete` domain, and the **38-name tool
  manifest** that is M6's contract
- `tests/agnostic.bcyr` — benchmark stub · `tests/agnostic.fcyr` — fuzz stub

## Dependencies

One `[deps.*]` block: **agnosai 2.0.4** (`modules = ["dist/agnosai.cyr"]`),
linked in-process rather than called over HTTP. Everything crew/task/agent/
scheduling-shaped lives there; Agnostic owns the product tier.

`cyrius.lock` — **115 deps locked**, 1 commit-pinned, `deps --verify` 115/0.
`lib/` holds 108 `.cyr`: 101 from the pinned toolchain snapshot plus 7 arriving
transitively through agnosai (`kavach`, `ai-hwaccel`, `bote-core`, `libro`,
`majra`, `tyche`, and `agnosai` itself).

Transitive versions that matter: **kavach 3.11.15**, **ai-hwaccel 2.3.18**.

## Consumers

_None yet._ SecureYeoman may pull agnosai directly without this frontend tier —
Agnostic is built to stand on its own, not as a required layer.

## Hardening

**P(-1) complete — 2026-08-20**, re-audited at M1.

| Criterion | Status |
|---|---|
| audit-clean | [`2026-08-20-audit-m1.md`](../audit/2026-08-20-audit-m1.md) — 0 CRITICAL / 0 HIGH / 1 MEDIUM / 2 LOW; the MEDIUM is accepted with a documented bound |
| fmt / lint / vet / deny | `check-clean.sh` OK |
| symbols | `check-symbols.sh` OK — 129 definitions, no duplicates, all prefixed |
| security | CI `security` job clean |
| baseline benches | `bench-history.csv` seeded — `noop` 2 ns @ `830216c` |
| documented | `BENCHMARKS.md` generated |

### Two gates added at M2

**`check-symbols.sh` rule 3 now scans enum members on both sides.** It compared
only `^(fn|var)` against `lib/`. Cyrius enum qualifiers are **cosmetic**, so a
`src/` enum member colliding with a `lib/` one silently replaced it for the whole
program — the same mechanism as the `BACKEND_COUNT` defect below, in the one
declaration kind the gate did not cover. Mutation-verified.

**`scripts/check-log-lengths.py`**, wired into `check-clean.sh`. sakshi takes
`(pointer, length)` pairs, so every message's byte count is hand-written and
nothing checked it. Both failure modes are silent and both shipped in one M2
commit: a count one too high put the **NUL terminator inside a JSON string**, and
one too low **truncated** a message. Invisible to the compiler, to lint, and to
suites that assert on handler behaviour rather than log text. Mutation-verified.

### The gap `check-symbols.sh` still does not cover

⚠ **Rules 1 and 2 scan `src/` only.** Cyrius has one flat symbol namespace with
last-definition-wins; the compiler warns on a duplicate `fn` but is **silent**
on a duplicate `var`. A collision between two *dependencies* inside `lib/` is
therefore invisible to the compiler and the linter at the same time — and
Agnostic, linking kavach and ai-hwaccel through agnosai, is where such a
collision lands.

That is not hypothetical: `BACKEND_COUNT` was 10 in kavach and 18 in
ai-hwaccel, and resolved to 18, disabling kavach's `_backend_fp` bounds check
over a 10-slot table. Fixed upstream; `tests/deps_symbols.tcyr` now guards the
class rather than the instance.

A full `lib/`-wide sweep at this dep set found **no remaining silent collision**:
of 3,040 top-level `var`s, only `AT_FDCWD` and `TASK_SIZE` differ across files,
and both are platform-variant families (`syscalls_*`, `async_*`) where exactly
one variant is prepended per target. `HTTP_OK`/`HTTP_NOT_FOUND` are defined by
both `http.cyr` and `sandhi.cyr` with identical values — redundant, not a defect.

⚠ Still open, and visible only as build warnings (all `fn`, so they warn):
kavach ↔ sigil share the whole `syserr_*` family and seven `agnosys_*` helpers;
`libro` and `majra` both define `_sub_new`. 20 duplicate-`fn` warnings in total.
Deferred deliberately — they are upstream, and they announce themselves.

## Preset library

**18 documents, 76 agents, 45 distinct agent keys, 38 distinct tool names.**
Checked in at `src/presets/*.json` and embedded into `src/presets_data.cyr` by
`scripts/gen-presets.sh`, because Cyrius has no `include_str!`. The generated file
is committed; `check-clean.sh` runs the generator's `--check` mode so it cannot
go stale.

Parsed **once at mount** into a name-keyed registry — `agnosai_builtin_presets()`
re-parses all eighteen on every call and the engine has no name lookup at all.
A parse shortfall refuses to start rather than serving a quieter, smaller library.

⚠ **The listing returns summaries, not documents.** The library is 61,412 bytes of
compact JSON against a 65,536-byte default request arena, and the arena spills
into the no-`free()` global bump — a full-document listing would leak permanently
on every call. Measured live: the listing is **4,416 bytes** and the largest
single document (`quality-large`) is **7,064**, so the default arena has ample
headroom and was left unchanged.

⚠ **The 38 tool names have never resolved to anything** — `ORACLE-AUDIT.md` §3.15.
`agnostic_preset_tool_*` pins the union as M6's contract; two of the names
(`ArtifactManagementTool`, `CIPipelineIntegrationTool`) have no implementation
anywhere and M6 owes a decision on each.

## Agent definitions

**One model, three dispositions, all of them visible on the wire.** A crew's
`agents` array and a stored definition are decoded by
`agnostic_agent_def_decode_a` and by nothing else.

| Disposition | Count | What it means |
|---|---|---|
| FORWARDED | 12 | the engine has a slot that acts on it |
| RETAINED | 2 | `focus`, `allow_delegation` — kept, round-tripped, and **named** in `unforwarded` |
| REFUSED | 12 | a 422 naming the missing capability |

Membership of RETAINED was decided by one test: does the canonical preset library
carry it? All 76 preset agents carry `focus`; 18 carry `allow_delegation`.
Neither reaches the engine, so saying so beats dropping it.

⚠ **`agent_key` is refused with a message pointing at `key`.** The oracle and the
engine both spell it `agent_key`; Agnostic spells it `key`, because M2's crew
decoder already did and one model cannot have two spellings.

⚠ **`hardware` is the one field refused despite the engine having a slot** — the
record is `ai-hwaccel`-shaped and Agnostic has no decoder for it. Every other
refusal is refused because the engine genuinely cannot act on it.

✅ **The store is durable, in patra, since M4.** `"storage": "patra"` on all five
responses; the nine store functions kept their signatures and
`src/routes/definitions.cyr` was not touched. A definition created in one process
is served by another after a restart — asserted in `tests/agentdef.tcyr` and
verified live.

The stored document is the **wire form**, read back through the same decoder that
validates a client request — so there is no second serialiser, a row that no
longer decodes is caught rather than half-read, and the two retained fields
persist without a column each.

⚠ `AGNOSTIC_DEFINITIONS_MAX` is now a **decode-cache bound, not a store ceiling**
— there is still no `free()`, so decoding per `GET` would leak. The cache assumes
this process is the only writer; patra is flock-arbitrated and multi-process, so
if that changes the cache goes rather than gets patched.

## Persistence

**One patra database, two tables**, behind `src/engine/store.cyr`:
`agnostic_definitions (dkey, doc)` and `agnostic_crews (crew_id, cname, cstatus,
doc)`. patra allows exactly **one index per table** — `SCH_IDX_COL` is a single
slot in the schema page — so each gets it on the column everything looks up by.
The audit chain has its own file: `patrastore_open` opens its own handle.

⚠ **Only terminal crew outcomes are stored.** A running crew's thread dies with
the process, so persisting non-terminal state would load a crew that claims to
run and never will. A crew interrupted mid-flight 404s after a restart.

⚠ **Two sibling-library defects are worked around, both filed upstream
2026-08-21.** `patra_init` stomps the host's log level (saved/restored in
`store.cyr`); libro's `PatraStore` caches prepared statements that fault on any
thread but the opener's, so audit verification runs once at open. Both
work-arounds carry a pointer to the filing and can be removed when they land.

## Next

See [`roadmap.md`](roadmap.md). **M5 — identity and tenancy.** Two things it
inherits:

✅ **patra's single index per table does NOT bind here — corrected 2026-08-21.**
The earlier note said M5 needs users by id *and* by email and would therefore
need two tables, a scan, or a patra change. It needs none of them.

`tbl_create` (`lib/patra.cyr:3437`) **auto-indexes column 0 when its type is
`COL_INT`**, so deriving the key from the value — `uid = trunc64(sha256(lower(email)))`
— makes one index serve both lookups, and M5 issues **zero `CREATE INDEX`**
statements. The same trick keys API keys by `trunc64(sha256(raw_key))` and
tenants by `trunc64(sha256(tenant_id))`.

⚠ **A truncated hash is a bucket, not an identity.** patra re-checks *STR* index
hits itself but gives no such re-check for an app-computed INT key — its INT
equality is exact on the truncated value stored. A 64-bit collision without an
app-side full compare is an **authentication bypass**, so every hit must be
re-verified against the full value with `ct_eq_bytes` before it authenticates
anything.

The limit may still be worth fixing upstream on its own merits, but M5 is not
the forcing case it was thought to be.

⚠ **Agent keys are `[a-z0-9][a-z0-9-]*`** so an identifier can never become a
path component. Audit point 6 is answered for M4 (no filesystem call in `src/`
takes request input) and genuinely re-opens at **M8**, where report filenames are
built from user text. Keep the character set narrow. The
field-forwarding gate it turns on is already built and under test:
`src/engine/request.cyr` establishes the pattern M3 extends.

⚠ **`gpu_strict` is refused, not forwarded, and that is deliberate.** It is a
field distinct from `gpu_required` — the oracle hard-fails only on
`gpu_required AND gpu_strict` — and the Cyrius engine cannot express strictness
at all (`gpu_strict` appears zero times in `lib/agnosai.cyr`). M2 refuses it with
a message naming the missing capability rather than accepting and dropping it.

⚠ **Carried into M3 and beyond, from M2:**

- **Placeholder mode is indistinguishable from real work by results alone.**
  Without `AGNOSTIC_LLM_URL` the engine echoes task descriptions back with status
  COMPLETED. Closed by disclosure (`engine_mode` on every response, a WARN at
  mount), not by type — so any *new* surface that reports crew output must
  disclose it too.
- **The crew routes are unauthenticated.** `agnostic_route_needs_auth` answers 1
  for all four, but the dispatch ladder's auth rung is still a comment until M5.
  The default bind is loopback, which is the only thing standing in front of them.
- **Results are memory-resident and capped.** The ledger retains 1,024 crews and
  256 progress events each; beyond that a poll answers `unknown` rather than a
  wrong answer. Durable results are M4's.
