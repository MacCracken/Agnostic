# Documentation & Test Audit (2026-02-16)

## Scope
Follow-up to the [2026-02-11 code/docs audit](2026-02-11-code-docs-audit.md). This audit focuses on documentation overlap, stale references, test coverage gaps, and configuration duplication.

## Findings & Remediations

### 1. Duplicate pytest configuration
**Finding**: Both `pytest.ini` and `pyproject.toml` defined pytest config. `pyproject.toml` was the superset (included `security` marker).
**Remediation**: Deleted `pytest.ini`. `pyproject.toml` is now the single source of truth.

### 2. Duplicate test fixtures
**Finding**: `sample_requirements` and `sample_test_results` were defined in both `tests/unit/conftest.py` and `tests/fixtures/common.py`. No test file imported from `common.py` directly.
**Remediation**: Consolidated all fixtures (`mock_redis`, `mock_celery`, `mock_llm`) into `tests/unit/conftest.py`. Replaced `common.py` with a pointer comment.

### 3. Stale version references
**Finding**: CLAUDE.md and `docs/development/setup.md` hardcoded exact versions ("CrewAI 0.75.0 + LangChain 0.2.16") that didn't match `pyproject.toml` ranges (`crewai>=0.11.0,<1.0.0`; `langchain>=0.1.0,<0.2.0`).
**Remediation**: Updated to version ranges matching `pyproject.toml`. README.md already used range-style versions.

### 4. Path errors in contributing.md
**Finding**: Lines 120, 122, 133, 136 referenced `doc/` instead of `docs/`.
**Remediation**: Fixed all `doc/` to `docs/` references.

### 5. Stale `tests/end-to-end/` references
**Finding**: `setup.md` and `contributing.md` referenced a `tests/end-to-end/` directory that doesn't exist.
**Remediation**: Removed end-to-end bullets from both files.

### 6. Duplicate security documentation
**Finding**: `docs/SECURITY.md` and `docs/security/assessment.md` contained identical content.
**Remediation**: Replaced `docs/SECURITY.md` with a short pointer to `security/assessment.md` plus vulnerability reporting instructions. `assessment.md` remains authoritative.

### 7. Overlapping setup.md / quick-start.md
**Finding**: ~30% content overlap between the two guides (architecture diagrams, env vars, troubleshooting).
**Remediation**:
- `quick-start.md`: Removed duplicated architecture table, dev setup section, and env vars reference. Added cross-references to `setup.md`.
- `setup.md`: Removed duplicated troubleshooting section. Added cross-reference to `quick-start.md`.

### 8. Missing agent READMEs
**Finding**: 3 of 6 agents (senior, junior, security_compliance) lacked README files. Only manager, analyst, and performance had them.
**Remediation**: Created READMEs for all three agents following the pattern from `agents/manager/README.md`.

### 9. Missing unit tests
**Finding**: Only 3 of 6 agents had unit tests (manager, analyst, senior). Junior, security_compliance, and performance had none.
**Remediation**: Created `test_junior_qa_tools.py`, `test_security_compliance_tools.py`, and `test_performance_tools.py` following existing test patterns.

### 10. No testing strategy ADR
**Finding**: No ADR covered the testing approach despite 11 existing ADRs.
**Remediation**: Created ADR-012 covering test structure, fixture management, mock strategy, coverage targets, and CI enforcement. Updated ADR index.

### 11. Pre-commit hook version drift
**Finding**: Pre-commit hooks used significantly older versions than `pyproject.toml` requirements (e.g., Black 24.8.0 vs >=25.1.0, Ruff v0.5.7 vs >=0.9.0).
**Remediation**: Updated Black (25.1.0), Mypy (v1.14.0), Ruff (v0.9.0), and Bandit (1.8.0) to match pyproject.toml lower bounds.

## Files Modified
- **Deleted**: `pytest.ini`
- **Modified**: `tests/unit/conftest.py`, `tests/fixtures/common.py`, `CLAUDE.md`, `docs/development/setup.md`, `docs/development/contributing.md`, `docs/SECURITY.md`, `docs/getting-started/quick-start.md`, `docs/adr/README.md`, `.pre-commit-config.yaml`
- **Created**: `agents/senior/README.md`, `agents/junior/README.md`, `agents/security_compliance/README.md`, `tests/unit/test_junior_qa_tools.py`, `tests/unit/test_security_compliance_tools.py`, `tests/unit/test_performance_tools.py`, `docs/adr/012-testing-strategy.md`, `docs/audits/2026-02-16-docs-test-audit.md`

### 12. Kubernetes implementation review
**Finding**: Multiple issues across raw manifests and Helm chart:
- `qa-agents-2.yaml` and `qa-agents-3.yaml` referenced 6 non-existent agents (SRE, Accessibility, API, Mobile, Compliance, Chaos)
- `kustomization.yaml` had stale resource refs, broken `{{ date }}` annotation, and a `NODE_ENV` patch irrelevant to Python agents
- Helm chart was missing `rabbitmq.yaml`, `serviceaccount.yaml`, and `ingress.yaml` templates
- WebGUI Helm template had broken `$(REDIS_HOST)` env var expansion and missing RABBITMQ_URL
- RABBITMQ_URL in all Helm agent templates used base64-encoded password instead of plaintext
- Security context was permissive (no readOnlyRootFilesystem, no capability drops)
- Resource limits were misaligned between Helm values, raw manifests, and docker-compose
- Ingress exposed RabbitMQ management publicly

**Remediation**:
- Deleted `qa-agents-2.yaml` and `qa-agents-3.yaml`; rewrote `qa-agents-1.yaml` with all 5 non-manager agents
- Rewrote `kustomization.yaml` with correct resource paths
- Created missing Helm templates: `rabbitmq.yaml`, `serviceaccount.yaml`, `ingress.yaml`
- Fixed WebGUI template: corrected REDIS_URL, added RABBITMQ_URL, fixed double-tagged image
- Added `rabbitmqPasswordPlain` to values.yaml; updated all agent templates to use it
- Hardened security context: `readOnlyRootFilesystem: true`, `capabilities.drop: [ALL]`, `seccompProfile: RuntimeDefault`
- Added emptyDir volumes for `/tmp` and `/app/logs` to all pods
- Aligned resource limits across all deployment targets
- Removed RabbitMQ from Ingress; added rate-limiting annotations
- Updated `docs/deployment/kubernetes.md`, `docs/deployment/docker-compose.md`, `CLAUDE.md`, `k8s/helm/agentic-qa/README.md`, and `docs/project/changelog.md`

## Files Modified (K8s review)
- **Deleted**: `k8s/manifests/qa-agents-2.yaml`, `k8s/manifests/qa-agents-3.yaml`
- **Rewritten**: `k8s/kustomization.yaml`, `k8s/manifests/qa-agents-1.yaml`
- **Modified**: `k8s/manifests/qa-manager.yaml`, `k8s/manifests/webgui.yaml`, `k8s/manifests/ingress.yaml`, `k8s/helm/agentic-qa/values.yaml`, all 7 Helm agent/webgui templates
- **Created**: `k8s/helm/agentic-qa/templates/rabbitmq.yaml`, `k8s/helm/agentic-qa/templates/serviceaccount.yaml`, `k8s/helm/agentic-qa/templates/ingress.yaml`
- **Docs updated**: `docs/deployment/kubernetes.md`, `docs/deployment/docker-compose.md`, `CLAUDE.md`, `docs/project/changelog.md`, `k8s/helm/agentic-qa/README.md`

## Resolved Items (2026-02-16 Follow-up)

The following Critical/High priority issues from the audit have been resolved:

1. **OAuth2 JWT Signature Verification** (Critical) — Resolved: JWKS verification for Google/GitHub/Azure AD, SAML guard added
2. **Hardcoded RabbitMQ Credentials** (High) — Resolved: docker-compose.yml uses `${RABBITMQ_USER}`/`${RABBITMQ_PASSWORD}`
3. **Docker Health Checks Non-Functional** (High) — Resolved: Agent health checks now perform Redis `r.ping()`
4. **PDF Export Placeholder** (High) — Resolved: Real PDF generation with ReportLab, HTML fallback
5. **CLAUDE.md Tool Inventory Wrong** (High) — Resolved: All tool names match code
6. **CLAUDE.md Aspirational API Docs** (High) — Resolved: Separated implemented vs planned endpoints
7. **Missing Dependencies** (Medium) — Resolved: Added PyJWT[crypto], faker, reportlab, requests to pyproject.toml
8. **`.env.example` Duplicates** (Medium) — Resolved: Removed duplicates, added 11 missing vars
9. **Undocumented Modules** (Medium) — Resolved: Added to CLAUDE.md Key modules section
10. **Agent README Gaps** (Medium) — Resolved: All 3 agent READMEs updated with complete tool lists

## Resolved Items (2026-02-16 Phase 2)

11. **Agent Registry Single Source of Truth** — Resolved: `config/agent_registry.py` reads from `team_config.json`, replaces hardcoded routing (ADR-013)
12. **WebGUI REST API** — Resolved: 18 FastAPI endpoints in `webgui/api.py` wrapping existing managers (ADR-014)
13. **CI/CD Broken Dependencies** — Resolved: Fixed `pip install` to use `pip install -e ".[dev,test,web,ml]"`
14. **CI/CD Missing Security Scan** — Resolved: Added Bandit security scan and Helm lint jobs
15. **Test Coverage Gaps** — Resolved: 48 new unit tests for agent_registry, webgui auth, webgui exports, webgui API, config environment

## Resolved Items (2026-02-16 Phase 3)

16. **No Observability Infrastructure** — Resolved: `shared/metrics.py` (Prometheus metrics with no-op fallback), `shared/logging_config.py` (structured logging), `/api/metrics` endpoint, LLM call instrumentation (ADR-015)
17. **No Circuit Breaker for LLM Calls** — Resolved: `CircuitBreaker` in `shared/resilience.py`, wired into all 6 LLM methods in `config/llm_integration.py` (ADR-016)
18. **No Celery Retry/Reliability Config** — Resolved: `task_acks_late`, `task_reject_on_worker_lost`, retry config in `config/environment.py` (ADR-016)
19. **No Graceful Shutdown** — Resolved: `GracefulShutdown` context manager replaces bare `except KeyboardInterrupt` in all 6 agents (ADR-016)
20. **`datetime.utcnow()` Deprecation** — Resolved: 4 occurrences in `webgui/auth.py` replaced with `datetime.now(timezone.utc)`
21. **Pydantic Test Collection Errors** — Resolved: Broadened except clauses in 7 agent tool test files

## Remaining Items
1. Integration tests for Celery task routing (carried from 2026-02-11 audit)
2. Explicit schemas for agent result payloads
3. Full docker-compose smoke test validation
