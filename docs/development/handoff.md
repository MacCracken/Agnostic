# agnostic — Port Handoff

> **Start here.** This is the orientation document for picking up the Python → Cyrius port.
> It is deliberately short and links outward rather than restating.
> Last refreshed: **2026-08-21**, after M2.

Read in this order:

| Document | What it answers |
|---|---|
| **this file** | Where the port is, how to build it correctly, what to do next |
| [`state.md`](state.md) | Live numbers — versions, surface area, dep set, gates |
| [`roadmap.md`](roadmap.md) | M0–M9 sequencing and per-milestone gates |
| [`../../CYRIUS-PORT-BRIEF.md`](../../CYRIUS-PORT-BRIEF.md) | Research snapshot (2026-08-19): language notes, dep stack, **§7 decisions — binding** |
| [`../../ORACLE-AUDIT.md`](../../ORACLE-AUDIT.md) | 86 verified defects in the Python oracle. §3 gated M2; **§2.2 gates M3** |
| [`../adr/`](../adr/) | Two ADRs: health/readiness split, daimon Tier 1 deferral |

---

## 1. Where the port is

**M0, M1 and M2 are complete. M3 — definitions, presets, agents — is next.**

Agnostic runs crews today. On top of M1's HTTP foundation (pooled `sandhi` server, `:name` routing,
per-request arena, strict env config, JSON logging with thread-local trace ids, `/health` +
`/ready`, signal-driven graceful shutdown) it now submits crews to AgnosAI in-process and answers
**202-then-poll**: `POST /api/v1/crews`, `GET /api/v1/crews/{id}`, `.../cancel`, `.../events`.
17 source files, 4,148 lines, 269 top-level definitions.
**12 test suites, 496 assertions, 0 failed.**

Version is **0.1.0** and stays there. Per decision #4 the whole port ships as **one release,
1.0.0** — no intermediate tags, so `main` stays green continuously rather than being stabilised
once per milestone. Agnostic was never SemVer before (the Python line was CalVer, `2026.3.18`);
1.0.0 is the first.

`[deps.agnosai]` is pinned at **2.0.4**, linked in-process, and now genuinely exercised — the crew
surface calls `agnosai_orchestrator_submit_crew`, reads the registry, and drains the event bus.

---

## 2. ⚠ Build it correctly, or you will write a lock CI cannot reproduce

This has bitten twice and is the single most important operational fact here.

**The installed wrapper is `6.5.33`. The manifest pins `6.5.32`.** `cyrius build`, `cyrius deps` and
`cyrius lib sync` all provision from the **installed** toolchain, not the manifest pin. Running any
of them through the PATH wrapper under drift rewrites `lib/` and `cyrius.lock` with content CI —
which installs the pin — cannot reproduce. CI has a **fatal drift gate** precisely because of this.

So, until the pin moves:

```bash
~/.cyrius/versions/6.5.32/bin/cyrius build src/main.cyr build/agnostic
```

Two corollaries that are easy to get wrong:

- **`cyrius build` is not read-only.** It re-resolves `[deps.*]` as a side effect — even for a
  throwaway probe file outside `src/`. After any build you did not intend to be a provisioning step,
  run `git status --short` and revert stray `lib/` + `cyrius.lock` churn.
- **Never bump a `[deps.X]` tag or build the consumer while the sibling working tree is ahead of its
  tag.** `path = "../X"` means provisioning comes from the local tree, not the tag, so the lock ends
  up describing something unfetchable. Check `git tag --list N` in the sibling *and* that its
  `HEAD == tag`, and confirm the tag is actually pushed — via `curl` to the GitHub API, never `gh`.

`cyrius deps --verify` is read-only and safe to run freely.

**Gates before handing anything back** — all three must be run under the pin:

```bash
sh scripts/check-clean.sh && sh scripts/check-symbols.sh && cyrius test
```

---

## 3. What M2 established, and what M3 inherits

M2's gate was `ORACLE-AUDIT.md` §3 — four high-severity defects, three sharing one root cause: a
result type too thin to branch on. All four are designed out, each by a mechanism rather than by
care, and each pinned by a suite:

| Defect | Mechanism | Pinned by |
|---|---|---|
| §3.1 failed reported as completed | `_agnostic_outcome_normalise` demotes COMPLETED-with-no-results to FAILED before the record exists | `tests/outcome.tcyr` |
| §3.2 cancel addressing an unknown id | every id originates in `agnosai_crew_new`; a refusal is returned, not discarded | `tests/crews_route.tcyr` |
| §3.3 two task models | `tasks` required, no fallback path, an unlisted key is a 422 naming it | `tests/crew_request.tcyr` |
| §3.4 terminal overwritten | `agnostic_ledger_latch` refuses to write over a terminal status | `tests/ledger.tcyr` |

⚠ **The lesson generalises, and M3 inherits it: an empty result set is not success.** `all()` over an
empty collection is vacuously true in Python — and `agnosai_crew_runner_run` makes the identical
mistake in Cyrius, setting COMPLETED and only downgrading inside a loop over `results` that does not
execute when the set is empty. Assume any new aggregate has the same hole until you have looked.

**M3 is definitions, presets and agents**, and its gate is field forwarding: every field either
forwarded or explicitly rejected, never silently dropped. That pattern is already built and under
test — `src/engine/request.cyr` is the worked example. Extend it rather than re-inventing it.

⚠ **`gpu_strict` is the field to understand before touching agent definitions.** It is **not**
`gpu_required`: the oracle declares both (`agents/base.py:61-62`) and hard-fails only on
`gpu_required AND gpu_strict` (`config/gpu_scheduler.py:196`) — `required` asks for a GPU, `strict`
says fail rather than silently fall back to CPU. The Cyrius engine cannot express strictness at all:
zero occurrences in `lib/agnosai.cyr`, and `agnosai_agent_with_gpu` takes no such parameter. M2
therefore **refuses** it, with a message naming the missing capability rather than reading like a
typo. Do not "fix" this by mapping it onto `gpu_required` — that reinstates the exact silent CPU
fallback `ORACLE-AUDIT.md` §3.11 records.

⚠ **Verify the oracle's 18 presets are viable before porting them.** A preset naming a tool the
Cyrius registry cannot resolve fails **silently** — the crew assembles empty rather than erroring,
which is §3.1's shape in different clothes. Agnostic's preset library is canonical (see §4).

### Three things M2 leaves open, deliberately

- **Placeholder mode is indistinguishable from real work by results alone.** With no
  `AGNOSTIC_LLM_URL`, `agnosai_execute_task` takes its `client == 0` arm and echoes the task
  description back as output with status COMPLETED. Closed by *disclosure* — `engine_mode` on every
  submit and poll response, plus a WARN at mount — not by type, because no property of a result type
  can separate them. **Any new surface reporting crew output must disclose it too.**
- **The crew routes are unauthenticated.** `agnostic_route_needs_auth` answers 1 for all four, but
  the dispatch ladder's auth rung is still a comment until M5. The loopback default bind is the only
  thing in front of them.
- **Results are memory-resident and capped** — 1,024 crews, 256 progress events each. Past that a
  poll answers `unknown`, never a wrong answer. Durable results are M4's, and
  `src/engine/ledger.cyr` is the seam they land on.

## 4. Settled — do not re-open

All six open decisions are closed. The record is `CYRIUS-PORT-BRIEF.md` §7.2, §7.2.1 and §7.3;
the roadmap carries each one against its milestone.

| | Decision |
|---|---|
| Identity | **Own it, thin** — adapt `secureyeoman/yeo-cy-test/src/auth.cyr`. kavach struck (zero identity surface) |
| Presets | **Agnostic's library is canonical** — the two sets share names and nothing else |
| PDF reports | **HTML + CSV + JSON only** in 1.0; wait for `bayan_pdf_*` |
| Release shape | **One release, total** — M1–M9 ship together as 1.0.0 |
| Daimon Tier 1 | **Deferred** — ADR 0002; it cannot be implemented as written |
| MCP transports | **Both shapes**, justified on merit; the 5–8 tool figure is a soft guideline, not a ceiling |

⚠ **Agnostic stands on its own** (§7.3). It is a product, not a frontend layer — SecureYeoman can
consume AgnosAI directly. This is a scope *reduction*. What it does not license is gratuitously
breaking SY: if SY is ever pointed at Agnostic, the answer is an additive compatibility shim built
then, against a real requirement. Out of scope for v1.0.

---

## 5. Cyrius footguns that have already cost time

- **One flat symbol namespace, last-definition-wins.** The compiler warns on a duplicate `fn` and is
  **silent** on a duplicate `var`. Every `check-symbols.sh` in the ecosystem scans `src/` only, so a
  `lib/`↔`lib/` collision between two dependencies is invisible to compiler and linter at once.
  This is not theoretical — see §6. `tests/deps_symbols.tcyr` now guards it here.
- **Enum qualifiers are cosmetic.** `Backend.WASM` and `KavachBackend.WASM` both resolve to the
  member `WASM`; the type name plays no part in resolution. Renaming an enum *type* does not protect
  its *members*.
- **No `free()`.** `lib/alloc.cyr` is a bump allocator with only `alloc_reset()`. Per-request arenas
  are mandatory, and only `sandhi_server_run_pooled` populates one — `run`, `run_opts`, `run_async`
  and `run_pooled_tls` do not, so every `_a` site needs a bare-form fallback.
- **Arena exhaustion returns 0, and a `Str` of 0 is indistinguishable from a valid one.** No option
  type, no error channel through the `_a` families. Constructors return 0 rather than a half-built
  record; callers must check. `ARENA_FULL_SPILL` is applied to sandhi's arena so an oversized
  response degrades instead of faulting.
- **sandhi accessors return NUL-terminated cstrings, not `Str`.** Passing one through unwrapped reads
  the pointer as a `Str` header and every downstream length is garbage.
- **sakshi takes `(pointer, length)`, and a miscount fails silently.** One too many puts the NUL
  terminator inside the message — an escaped NUL in JSON output; one too few truncates it. Neither
  is a compile error, a lint warning, nor a test failure, because the suites assert on handler
  behaviour rather than log text. Both shipped in one M2 commit.
  `scripts/check-log-lengths.py` now gates it, from `check-clean.sh`.
- **⚠ The compiler's line numbers for `src/` warnings are wrong.** Two pre-existing
  "assigning non-pointer to typed pointer" warnings in `src/http/router.cyr` were reported at lines
  44 and 56 before M2 and at 98 and 110 after — a shift of exactly the number of lines added
  *elsewhere* in the file. The columns stayed stable, so the diagnostic knows the site and
  mis-attributes the line. **Do not chase a `src/` warning by line number**; find it by column and
  construct. Worth filing upstream — and never patch the cyrius tree from a consumer repo.
- **Two AgnosAI behaviours bite only the async path.** A cyclic DAG submitted through `submit_crew`
  leaves the crew reporting `pending` **forever** — the error return is discarded on the submit
  thread and the registry keeps the PENDING entry `_agnosai_orch_register` seeded — and
  `_agnosai_orch_evict_locked` drops **every** finished crew once the registry holds 1000, so a
  completed crew can 404. Both are worked around in `src/engine/`, not upstream; read those module
  headers before changing either.
- **`CYRIUS_PKG_VERSION` resolves only in the entry file**, not in `include`d files — filed upstream
  (`2026-08-20-pkgver-not-visible-in-included-files.md`, open at 6.5.33). Workaround in place: read
  it in `main.cyr` and hand it to the module via a setter.

⚠ **Never modify the cyrius tree from a consumer repo.** File an issue or proposal instead. Two are
already filed from this port.

---

## 6. Cross-repo state

All three sibling releases this port depends on are tagged and consumed:

| Repo | Version | Note |
|---|---|---|
| `agnosai` | **2.0.4** | The engine tier, linked in-process |
| `kavach` | **3.11.15** | Arrives transitively |
| `ai-hwaccel` | **2.3.18** | Arrives transitively |

**2.0.4 closed a memory-safety defect that only manifested in *this* binary**, because Agnostic is
what links kavach and ai-hwaccel together. Both defined `var BACKEND_COUNT` (10 and 18); it resolved
to 18, disabling kavach's `_backend_fp` bounds check over a 10-slot table so that an out-of-range id
read past `_backend_table[320]` and was called as a function pointer. Renamed upstream to
`KAVACH_BACKEND_COUNT` / `AIHW_BACKEND_COUNT`. Full write-up: the addendum to
[`../audit/2026-08-20-audit-m1.md`](../audit/2026-08-20-audit-m1.md).

### Owed, not blocking

- **`yantra`** — needs `Page.captureScreenshot` on its CDP surface before **M6**'s QA tool surface
  (decision D4). Not started.
- **`bayan`** — a `bayan_pdf_*` request should be filed before **M8** reports.
- **`agnosai`** — streamline its preset library to examples, now that Agnostic's is canonical.
- **`kavach` / `ai-hwaccel`** — uncommitted CHANGELOG corrections sit in both working trees
  (the released entries overstate the enum rename as breaking). Deliberately left to be picked up
  with a future update.
- **Known and deferred**: kavach's enum members are generic and unprefixed; kavach ↔ sigil share the
  whole `syserr_*` family and seven `agnosys_*` helpers; `libro` and `majra` both define `_sub_new`.
  20 duplicate-`fn` warnings at build. All are `fn`, so they announce themselves — unlike the `var`
  case above, which did not.

---

## 7. Two counting corrections worth carrying

- **`cyrius test`'s final `N passed, 0 failed` line is the *suite* tally, not a suite.** Summing it
  with the per-suite lines inflates the total. M1 is **215 assertions across 7 suites**, not 222;
  agnosai is **98 suites / 7,940 assertions**, not 99 / 8,038. The wrong agnosai figure is in that
  repo's `state.md`, which is already tagged.
- **The oracle is a behavioural reference, not a specification.** 203 Python files at
  `python-port/`, 86 verified defects. Its identity surface in particular is mostly dead code — no
  `password_hash` writer, no user CRUD, no role assignment beyond a hardcoded `VIEWER` — and **none
  of that appears among the 85**. Anything reading it for an identity spec is reading machinery that
  never ran.
