# agnostic — Port Handoff

> **Start here.** This is the orientation document for picking up the Python → Cyrius port.
> It is deliberately short and links outward rather than restating.
> Last refreshed: **2026-08-21**, at `919174d`.

Read in this order:

| Document | What it answers |
|---|---|
| **this file** | Where the port is, how to build it correctly, what to do next |
| [`state.md`](state.md) | Live numbers — versions, surface area, dep set, gates |
| [`roadmap.md`](roadmap.md) | M0–M9 sequencing and per-milestone gates |
| [`../../CYRIUS-PORT-BRIEF.md`](../../CYRIUS-PORT-BRIEF.md) | Research snapshot (2026-08-19): language notes, dep stack, **§7 decisions — binding** |
| [`../../ORACLE-AUDIT.md`](../../ORACLE-AUDIT.md) | 85 verified defects in the Python oracle. **§3 is a hard gate on M2** |
| [`../adr/`](../adr/) | Two ADRs: health/readiness split, daimon Tier 1 deferral |

---

## 1. Where the port is

**M0 and M1 are complete. M2 — AgnosAI integration — is next and is unblocked.**

Agnostic serves real HTTP today: pooled `sandhi` server, `:name` routing, per-request arena,
strict env config, JSON structured logging with thread-local trace ids, `/health` + `/ready`, and
signal-driven graceful shutdown. 12 source files, 1,741 lines, 129 top-level definitions.
**8 test suites, 229 assertions, 0 failed.**

Version is **0.1.0** and stays there. Per decision #4 the whole port ships as **one release,
1.0.0** — no intermediate tags, so `main` stays green continuously rather than being stabilised
once per milestone. Agnostic was never SemVer before (the Python line was CalVer, `2026.3.18`);
1.0.0 is the first.

`[deps.agnosai]` is pinned at **2.0.4** and already linked — `lib/agnosai.cyr` is in the compile
unit right now. **M2 is handler work, not integration plumbing.**

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

## 3. What M2 must do — and the four things it must not

M2 wires crew submit / status / cancel through `agnosai_orchestrator_submit_crew`, with `majra`
owning the queue and **202-then-poll** semantics (decision **D2**), and live progress off the event
bus.

⚠ **`ORACLE-AUDIT.md` §3 is a design gate, not background reading.** The oracle's integration layer
has four high-severity defects, and three of them are the *same* root cause — a result type too thin
to carry what the caller needs to branch on. Designing them out is a requirement of the milestone:

| Oracle defect | What M2 must do instead |
|---|---|
| §3.1 — a failed crew is reported as **completed** (`.status` is never read anywhere) | A result type that carries status **and** error **and** the remote id, with the caller branching on status |
| §3.2 — cancel POSTs a **local** UUID AgnosAI has never seen; 404 is discarded and the record is marked cancelled while the crew keeps running | Retain the id AgnosAI assigns; cancellation must **stop work**, not relabel a record |
| §3.3 — the two backends run structurally different work (a `tasks` array is silently discarded, so the single-task fallback always fires) | **One** task model |
| §3.4 — fleet/GPU failures return `{}, 0`, which `all()` treats as vacuously true, overwriting `failed` with success | Terminal states stay terminal |

The shared lesson: **an empty result set is not success.** `all()` over an empty collection is
vacuously true in Python, and the equivalent mistake is just as available in Cyrius.

Design obligation carried from §7.3: **keep the seam shim-able.** Route tables and request decoding
stay separable from handler logic, so an alternate surface can be mounted later without touching
either. Cheap now, expensive to retrofit.

---

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
  `python-port/`, 85 verified defects. Its identity surface in particular is mostly dead code — no
  `password_hash` writer, no user CRUD, no role assignment beyond a hardcoded `VIEWER` — and **none
  of that appears among the 85**. Anything reading it for an identity spec is reading machinery that
  never ran.
