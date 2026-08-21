# agnostic — Port Handoff

> **Start here.** This is the orientation document for picking up the Python → Cyrius port.
> It is deliberately short and links outward rather than restating.
> Last refreshed: **2026-08-21**, after M3.

Read in this order:

| Document | What it answers |
|---|---|
| **this file** | Where the port is, how to build it correctly, what to do next |
| [`state.md`](state.md) | Live numbers — versions, surface area, dep set, gates |
| [`roadmap.md`](roadmap.md) | M0–M9 sequencing and per-milestone gates |
| [`../../CYRIUS-PORT-BRIEF.md`](../../CYRIUS-PORT-BRIEF.md) | Research snapshot (2026-08-19): language notes, dep stack, **§7 decisions — binding** |
| [`../../ORACLE-AUDIT.md`](../../ORACLE-AUDIT.md) | 86 verified defects in the Python oracle. §3 gated M2, §2.2 gated M3; **§3.15 is M6's problem** |
| [`../adr/`](../adr/) | Two ADRs: health/readiness split, daimon Tier 1 deferral |

---

## 1. Where the port is

**M0 through M3 are complete. M4 — persistence and the audit chain — is next.**

Agnostic runs crews and serves its own catalogue. On M1's HTTP foundation it
submits crews to AgnosAI in-process with **202-then-poll**, serves the canonical
**18-preset library**, and offers **agent-definition CRUD**. 25 source files,
6,502 lines, 396 top-level definitions.
**14 test suites, 702 assertions, 0 failed.**

Version is **0.1.0** and stays there. Per decision #4 the whole port ships as
**one release, 1.0.0** — no intermediate tags, so `main` stays green continuously
rather than being stabilised once per milestone.

`[deps.agnosai]` is pinned at **2.0.4** and genuinely exercised: the crew surface
submits, polls the registry and drains the event bus; the definition surface
builds engine agent records through its setters.

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

## 3. What M2 and M3 established, and what M4 inherits

**M2's gate was `ORACLE-AUDIT.md` §3** — four defects, all designed out by
mechanism and each pinned by a suite: the vacuous-success demotion in
`outcome.cyr`, engine-assigned ids only, one task model, and the terminal latch
in `ledger.cyr`.

**M3's gate was §2.2** — fourteen fields dropped in translation. It grew a third
disposition in the doing, and that is the part worth carrying:

> A field is **FORWARDED** when the engine has a slot that acts on it, **REFUSED**
> with a 422 naming the missing capability when it does not, and **RETAINED** when
> Agnostic's own content carries it but the engine cannot use it — kept,
> round-tripped, and **named in `unforwarded`**. Three, all visible on the wire.
> There is no fourth.

⚠ **Two lessons generalise past their milestone:**

- **An empty result set is not success.** `all()` over an empty collection is
  vacuously true in Python, and `agnosai_crew_runner_run` makes the identical
  mistake in Cyrius. Assume any new aggregate has the same hole until you look.
- **An unspecified value must not acquire a concrete one.** M3 shipped a bug
  where `gpu_required` alone overwrote the engine's "no floor" sentinel with 0,
  putting a value on the wire the caller never sent. Found by live testing, not
  by the suite — the same class of defect as a dropped field, in the other
  direction.

**M4 is persistence and the audit chain**, and two seams were built for it:

- `agnostic_definitions_*` — nine functions and one storage literal.
  `src/routes/definitions.cyr` touches the store only through them, so M4
  reimplements against `patra` and changes no handler. `"storage":"memory"`
  becomes `"patra"` and nothing else on the wire moves.
- `src/engine/ledger.cyr` — the same shape for crew outcomes, which are also
  memory-resident and capped today.

⚠ **Agent keys are `[a-z0-9][a-z0-9-]*`, at most 100 bytes, and that is
load-bearing for M4.** A key that cannot contain `/` or `.` makes an on-disk path
built from one safe **by construction** rather than by validation — which is the
cheap version of M4's "path-traversal validation on every externally-derived
path" bullet. Do not widen the character set.

⚠ **`patra` constraints to design around, not discover:** one index per table,
per-write fsync by default, and single-writer. All three are in the M5 section of
the roadmap and they apply to M4's tables just as much.

### Carried forward, still open

- **Placeholder mode is indistinguishable from real work by results alone** —
  closed by disclosure (`engine_mode` on every crew response, a WARN at mount),
  not by type. Any new surface reporting crew output must disclose it too.
- **Every route past `/health` and `/ready` is unauthenticated.**
  `agnostic_route_needs_auth` answers 1 for all eleven, but the dispatch ladder's
  auth rung is still a comment until M5. The loopback default bind is the only
  thing in front of them, and M3 widened the surface considerably.
- **§3.15 is M6's.** The 38-name tool manifest is pinned by `tests/presets.tcyr`;
  two of the names have no implementation anywhere. A registry miss must be an
  **error**, never a silently smaller agent.

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
- **A Cyrius line continuation KEEPS the newline.** `"abc\<newline>def"` is 7
  bytes, not 6 — verified with a probe. So a generated string literal must never
  break inside a JSON string: the newline would be spliced into the value, and a
  raw newline inside a JSON string is illegal JSON. There is no C-style
  adjacent-literal concatenation to split with either, and `#skip-lint` is scoped
  to a **line**, so it cannot be placed on an offending line that sits inside a
  literal. `scripts/gen-presets.sh` breaks only between JSON tokens for this
  reason, and `check-clean.sh` skips lint for files marked `GENERATED FILE`.
- **`src/app.cyr` holds the include order; add new modules there.** Every suite
  reaching the router includes it. Putting the order in `main.cyr` meant a new
  route module broke all of them with "undefined function" — three times before
  the file existed. And a key used by two modules belongs in
  `src/http/status.cyr`, which is included first: a top-level `var` initialiser
  reading a global declared later silently evaluates to 0.
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
