# 0002 — Daimon Tier 1 registration is deferred

**Status**: Accepted
**Date**: 2026-08-20

## Context

`first-party-standards.md:636-669` defines Daimon integration tiers. Tier 1 —
`register_agent()` plus a heartbeat, wired through `src/ai.cyr` — is marked **"Always required"**
for long-running daemons. Agnostic is an HTTP server, so it qualifies on the text.

Investigating how to implement it turned up a problem with the requirement rather than with our
willingness to meet it.

**The endpoint it needs does not exist.** daimon's router serves `POST /v1/agents` and
`GET /v1/agents/{id}` and nothing else under `/v1/agents`. There is **no agent heartbeat route at
all** — the only heartbeats in daimon are edge-fleet and federation, which are a different
subsystem. So the "plus a heartbeat" half of Tier 1 has nowhere to send anything.

**Registration buys close to nothing for an externally-started process.** It seeds supervisor
health, quota and circuit-breaker maps keyed to a pid, and that pid stays `0` for a process daimon
did not spawn. Those maps are the payoff; keyed to 0 they do not function.

**No first-party project performs it at runtime.** Not AgnosAI. Not hoosh, majra, bote, patra or
libro. Not even **agnoshi**, which the standard names at `:669` as *"the canonical daimon/hoosh
consumer"*. Two projects — phylax and prakash — define `register`/`heartbeat` functions but never
call them, and both target `/v1/agents/register`, a path daimon's router does not match. That is the
signature of a requirement written against an intended API rather than a shipped one.

**The frozen oracle did integrate with daimon**, but through a different door: its MCP tool
registry, opt-in and default-off (`DAIMON_MCP_AUTO_REGISTER` defaults `"false"`). That path
registers *tools*, not the process, and it works.

Closing the gap properly needs work on daimon's side — its socket layer and HTTP layer both need
adapting before an agent-heartbeat contract exists to implement against.

## Decision

**Agnostic does not implement Daimon Tier 1 for 1.0.0.** No `register_agent()`, no process
heartbeat, no `src/ai.cyr` DaimonClient.

**At M7, Agnostic ships the daimon integration that does work**: an env-gated, default-off registrar
that POSTs each QA tool to daimon's tool endpoint — the same shape and the same default as the
oracle's.

This is recorded as a deferral, not a refusal. When daimon's socket and HTTP layers are adapted and
an agent-heartbeat API exists, Tier 1 becomes implementable and this ADR should be superseded.

## Consequences

- **Positive** — no dead code. The alternative is shipping a `register_agent()` whose heartbeat half
  cannot be written and whose supervisor maps key to pid 0, which is what phylax and prakash already
  did, twice, without either noticing.
- **Positive** — the tool-registration path that genuinely works still ships, so daimon consumers
  are not left with nothing.
- **Negative** — Agnostic is knowingly non-conformant against a "**Always required**" clause. Held
  deliberately and in writing rather than quietly: every other first-party project is in the same
  position, including the one the standard names as canonical.
- **Neutral** — creates an upstream conversation: either daimon grows the heartbeat API, or the
  standard's Tier 1 wording is corrected to match what daimon actually serves.

## Alternatives considered

**Implement `register_agent()` and skip the heartbeat.** Rejected. Half of Tier 1 is not Tier 1, and
registration alone seeds maps against pid 0 — the appearance of conformance with none of the effect.
That is strictly worse than an honest deferral, because it stops anyone asking the question again.

**Implement against `/v1/agents/register`, as phylax and prakash do.** Rejected — daimon's router
does not match that path, so the calls 404. Both projects avoid discovering this only because
neither ever calls its own registration code.

**Wait for daimon before starting M7.** Rejected. The daimon-side work is a socket-layer and
HTTP-layer adaptation on someone else's schedule, and the M7 tool-registration path does not depend
on it. Blocking a milestone on an unscheduled upstream change trades certain delay for uncertain
conformance.
