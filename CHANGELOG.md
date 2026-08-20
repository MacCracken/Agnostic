# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added — M1, the HTTP foundation

The first milestone where untrusted bytes reach a buffer. **222 assertions across 7 suites**, 0
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
