# agnostic — Current State

> Refreshed every release. CLAUDE.md is preferences/process/procedures
> (durable); this file is **state** (volatile).

## Version

**0.1.0** — scaffolded 2026-08-20 via `cyrius init`. No releases yet.

## Toolchain

- **Cyrius pin**: `6.5.32` (in `cyrius.cyml [package].cyrius`) — matches the
  installed wrapper, verified by a CI gate that treats drift as fatal

## Source

Initial scaffold only — `src/main.cyr` + `src/test.cyr`, 34 lines, 4 top-level
symbols, all `_agnostic_*`-prefixed.

The Python implementation is retained at `python-port/` as a behavioural oracle.
It is never built or shipped, and it is **not** a specification —
[`ORACLE-AUDIT.md`](../../ORACLE-AUDIT.md) records 85 verified defects in it.

## Tests

- `tests/agnostic.tcyr` — primary suite (smoke + math; passes on `cyrius test`)
- `tests/agnostic.bcyr` — benchmark stub (no-op)
- `tests/agnostic.fcyr` — fuzz stub

## Dependencies

Direct (declared in `cyrius.cyml`):

- stdlib — string, fmt, alloc, io, vec, str, syscalls, assert, bench

No `[deps.NAME]` git dependencies yet, therefore no `cyrius.lock` — the
documented default (`first-party-standards.md:135`). The lockfile gates in
`check-clean.sh` and `ci.yml` re-arm automatically when the first one lands.

## Consumers

_None yet._

## Hardening

**P(-1) complete — 2026-08-20.** Exit criteria per `first-party-standards.md:869`:

| Criterion | Status |
|---|---|
| audit-clean | [`docs/audit/2026-08-20-audit.md`](../audit/2026-08-20-audit.md) — 0 CRITICAL / 0 HIGH / 0 MEDIUM, 2 LOW both closed |
| fmt / lint / vet / deny | `check-clean.sh` OK |
| symbols | `check-symbols.sh` OK — 4 definitions, no duplicates, all prefixed |
| security | CI `security` job clean |
| baseline benches | `bench-history.csv` seeded — `noop` 2 ns @ `830216c` |
| documented | `BENCHMARKS.md` generated |

Re-run before each minor cut. The audit records, per checklist point, **which
milestone re-opens it** — M1 alone re-opens input validation, buffer safety,
syscall review and pointer validation simultaneously, because that is where
untrusted bytes first reach a buffer.

## Next

See [`roadmap.md`](roadmap.md).
