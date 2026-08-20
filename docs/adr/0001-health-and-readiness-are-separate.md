# 0001 — Health and readiness are separate probes

**Status**: Accepted
**Date**: 2026-08-20

## Context

Kubernetes and every comparable orchestrator distinguish two probes, and they act on them very
differently:

- **Liveness** — "is this process wedged?" A failure gets the container **killed and restarted**.
- **Readiness** — "should traffic go here right now?" A failure gets the pod **removed from the
  load-balancer**, and nothing is restarted.

The Python oracle at `python-port/` exposes `/health` and `/ready`, but `/health` pings Redis and
opens a TCP connection to RabbitMQ, returning 503 when either is unreachable.

That inverts the contract. A dependency outage is not a wedged process, and restarting the process
cannot fix a Redis that is down. Under an orchestrator the consequence is an amplification loop: one
Redis blip fails the liveness probe on *every* replica simultaneously, all of them are killed, they
restart, they still cannot reach Redis, and they are killed again — turning a degraded dependency
into a total outage of the thing that depends on it, plus a thundering-herd reconnect when Redis
returns.

The oracle hit this and patched around it rather than at it. Its own CHANGELOG records:

> **Health check degraded status** — `/health` now returns HTTP 200 for "degraded" state (no agent
> heartbeats, RabbitMQ down). Only "unhealthy" (Redis/DB down) returns 503. Fixes false-negative
> liveness failures in fresh containers and e2e tests.

That is the right *direction* — stop failing liveness on dependency state — reached by carving out
exceptions while keeping Redis and the DB as liveness-fatal. The underlying conflation stayed.

`ORACLE-AUDIT.md` establishes the standing rule for this port: `python-port/` is a behavioural
reference, not a specification, and a behaviour is not carried over merely because it is there.

## Decision

**`/health` is liveness and reads no dependency.** It answers `200 {"status":"ok"}` unconditionally.
If the process can accept a connection and run a handler, it is alive; that is the entire question
being asked.

**`/ready` is readiness and runs a check registry.** It answers `200 {"status":"ready", ...}` when
every registered check passes, or `503 {"status":"not_ready", ...}` when any fails. The body reports
each check by name so an operator can see *which* dependency is down without correlating logs.

Checks register through `agnostic_ready_register(name, fp)` at **mount time only** — the registry is
read lock-free by every worker, and `sandhi_server_run_pooled` spawns those workers after mount, so
registration before the run call is safe and registration after it is a data race. M2 (AgnosAI) and
M4 (patra) add checks without editing the handler.

## Consequences

- **Positive** — a dependency outage degrades traffic routing instead of triggering a restart storm.
  The failure mode the oracle patched around cannot occur.
- **Positive** — `/ready` names the failing dependency, so a 503 is actionable rather than a prompt
  to go read logs.
- **Positive** — the registry keeps the handler closed to modification as dependencies are added.
- **Negative** — `/health` no longer detects a process that is running but useless. That is
  deliberate: readiness detects it, and readiness is the probe whose remedy actually matches.
- **Negative** — a genuinely wedged process that still accepts connections will pass liveness. Real,
  and not solvable by dependency pinging either — it needs a watchdog on request progress, which is
  out of scope for M1.
- **Neutral** — anything deploying Agnostic must point its liveness probe at `/health` and its
  readiness probe at `/ready`. Pointing both at `/health` restores the old behaviour by
  configuration.

## Alternatives considered

**Keep the oracle's behaviour for compatibility.** Rejected. Nothing consumes Agnostic's `/health`
yet — this is a rewrite at 0.1.0, before any consumer exists — so there is no compatibility to
preserve, and preserving it would mean deliberately shipping a known amplification loop.

**One `/health` endpoint with a `?deep=1` query parameter.** Rejected. It puts the correctness of
the deployment in the *caller's* hands: an operator who configures the liveness probe without the
parameter, or with it, silently gets the wrong semantics. Two endpoints make the distinction
impossible to get wrong by omission.

**Report degraded-but-serving as a third state, as the oracle ended up doing.** Rejected for
liveness, where the probe result is binary — the orchestrator either kills the container or does
not, so a third state has to collapse to one of two anyway. `/ready`'s per-check `checks` object
carries that nuance where something can actually act on it.
