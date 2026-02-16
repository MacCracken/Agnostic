# ADR-013: Plugin Architecture for Agent Registration

## Status
Accepted

## Context

Adding a new agent to the system previously required editing **7 files**:
1. `agents/<name>/<name>.py` — agent implementation
2. `agents/<name>/Dockerfile` — container image
3. `docker-compose.yml` — service definition
4. `k8s/manifests/qa-agents-1.yaml` or Helm template — deployment
5. `agents/manager/qa_manager.py` — add `elif` branch to `_delegate_to_specialists`
6. `webgui/app.py` — add agent to hardcoded welcome message
7. `config/team_config.json` — add role entry

Steps 5 and 6 required touching core orchestration code for every new agent, creating merge-conflict risk and making the system fragile to extension.

## Decision

Introduce a **config-driven Agent Registry** (`config/agent_registry.py`) that reads agent definitions from `config/team_config.json` and replaces hardcoded if/elif routing.

### Key design choices

1. **`AgentDefinition` dataclass** — immutable, frozen, captures agent_key, name, role, focus, tools, complexity, celery_task, celery_queue, redis_prefix.

2. **`AgentRegistry` singleton** — loads all agent definitions at startup from `team_config.json`. Provides:
   - `get_agent(key)` — lookup by config key
   - `get_all_agents()` — all registered agents
   - `get_agents_for_team(size)` — team-size-aware list
   - `route_task(scenario)` — maps `assigned_to` to agent, replacing if/elif
   - `get_agent_for_complexity(complexity)` — fallback routing

3. **Convention over configuration** — agent key `"senior-qa"` maps to role `"senior_qa"`, Celery queue `"senior_qa"`, with sensible defaults. Explicit fields in `team_config.json` override conventions.

4. **Backwards-compatible** — existing `assigned_to` values (`"senior"`, `"junior"`, `"analyst"`, `"security_compliance"`, `"performance"`) are mapped to agent keys via a lookup table.

### What this is NOT

- **Not hot-reload**: Registry loads once at startup. Adding agents requires restart.
- **Not pip plugins**: No entry_points or dynamic discovery. Agents are configured in JSON.
- **Not auto-Dockerfile**: You still create Dockerfiles and k8s manifests for new agents.

## Consequences

### Positive
- Adding a new agent no longer requires editing `qa_manager.py` or `webgui/app.py`
- New agent process: (1) implement agent, (2) add Dockerfile, (3) add to `team_config.json`, (4) add to docker-compose/k8s — **5 steps instead of 7, no code changes to core modules**
- WebGUI welcome message is always in sync with config
- Task routing is data-driven and testable (16 unit tests)
- Foundation for future dynamic agent discovery

### Negative
- Slight indirection: developers must understand the registry pattern
- Convention-based naming means new agents should follow naming conventions
- Still requires restart to pick up new agents

## Rationale

The registry pattern was chosen over alternatives:
- **Entry-points/pip plugins**: Too complex for current needs; agents are all in-repo
- **File-system scanning**: Fragile and hard to control ordering
- **Decorator-based registration**: Requires importing all agents at startup, which conflicts with containerized architecture where each agent runs in its own process
