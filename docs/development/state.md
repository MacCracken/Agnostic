# agnostic — Current State

> Refreshed every release. CLAUDE.md is preferences/process/procedures
> (durable); this file is **state** (volatile).
> Last refreshed: 2026-08-21.

## Version

**0.1.0** — scaffolded 2026-08-20 via `cyrius init`. No releases yet; **1.0.0**
is the target cut, not 2.x. The Cyrius line is the first SemVer line — the
Python line was CalVer (`2026.3.18`).

## Toolchain

- **Cyrius pin**: `6.5.32` (`cyrius.cyml [package].cyrius`).
- ⚠ **The installed wrapper is currently `6.5.33` — drift.** CI treats drift as
  fatal, and CI installs the pin, so CI is unaffected. Locally it means
  `cyrius build`, `lib sync` and `deps` must be run through
  `~/.cyrius/versions/6.5.32/bin/cyrius`, **not** the PATH wrapper: all three
  provision from the *installed* toolchain rather than the manifest pin, and
  syncing under drift is exactly how a lock CI cannot reproduce gets written.
- For the record, `6.5.32/lib` and `6.5.33/lib` are byte-identical — only
  `cycc` differs — so this particular drift cannot change `lib/`. That is luck,
  not a reason to skip the precaution.

## Source

**M1 complete** — 12 files, 129 top-level definitions, all `agnostic_*`-prefixed.

| module | role |
|---|---|
| `src/config.cyr` | env config, strictly parsed; a malformed value refuses to start |
| `src/strcase.cyr` | ASCII case folding without allocating |
| `src/trace.cyr` | thread-local W3C trace ids (sakshi's is a process global) |
| `src/log.cyr` | sakshi emit hook, one JSON object per event |
| `src/http/{status,response,codec,router}.cyr` | status table, response records, JSON allow-list codec, route matching |
| `src/routes/health.cyr` | `/health` and `/ready` |
| `src/server/serve.cyr` | the only module that touches a socket |
| `src/main.cyr` | entry; thin by convention |

The Python implementation is retained at `python-port/` as a behavioural oracle.
It is never built or shipped, and it is **not** a specification —
[`ORACLE-AUDIT.md`](../../ORACLE-AUDIT.md) records 85 verified defects in it.

## Tests

**8 suites, 229 assertions, 0 failed** (`cyrius test`, run under the pin).

⚠ Counts here are assertion-suite lines only. `cyrius test`'s final
`N passed, 0 failed` line is the **suite** tally, not a suite — earlier figures
in this repo (`222`) and in agnosai (`8,038`) double-counted it.

- `tests/{agnostic,codec,config,health,log,router,trace}.tcyr` — M1 coverage (7 suites, 215 assertions)
- `tests/deps_symbols.tcyr` — **14 assertions**, cross-dependency symbol integrity;
  see Hardening below
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

### The gap `check-symbols.sh` does not cover

⚠ **It scans `src/` only.** Cyrius has one flat symbol namespace with
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

## Next

See [`roadmap.md`](roadmap.md). M2 is AgnosAI integration, which must design out
the four defects recorded in `ORACLE-AUDIT.md` §3.
