# Code + Documentation Audit (2026-02-11)

## Scope
- Repository audit of code, documentation, and WebGUI behavior
- Git baseline: current branch only

## Key Findings
1. **Architecture drift**: Documentation and WebGUI referenced legacy agents (SRE, accessibility, API, mobile, chaos) that are not present in the repo.
2. **Task routing mismatch**: QA Manager delegated work to non-existent agents and Celery task names that were never registered.
3. **Agent execution gaps**: QA Analyst, Performance, and Security & Compliance agents lacked Celery worker wrappers/Redis listeners for orchestration.
4. **Monitoring/reporting drift**: WebGUI exports and agent monitoring referenced legacy agent keys and data sources.
5. **Health check mismatch**: QA Manager Dockerfile healthcheck used an HTTP endpoint that does not exist.

## Remediation Applied
- Aligned documentation (README, DEPLOYMENT_GUIDE, AGENTS_INDEX, docs/api) to the active 6-agent system.
- Updated WebGUI commands, exports, history, and dashboard to use active agent keys.
- Updated QA Manager scenario plan and delegation routing to active agents only.
- Added Celery task wrappers + Redis listeners for QA Analyst, Security & Compliance, and Performance agents.
- Added performance result storage and manager notifications for performance/resilience runs.
- Updated QA Manager Dockerfile healthcheck to match runtime behavior.

## Remaining Recommendations
1. Add integration tests for Celery task routing and Redis pub/sub flows.
2. Define explicit schemas for agent result payloads and enforce in WebGUI exports.
3. Consider a single source-of-truth for agent registry to reduce drift.
4. Run a full system smoke test with docker-compose to validate orchestration end-to-end.
5. Review async/sync boundaries in `agents/manager/qa_manager.py` (async helpers invoked from sync tool).
