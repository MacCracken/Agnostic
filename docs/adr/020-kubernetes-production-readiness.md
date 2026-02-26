# ADR-020: Kubernetes Production Readiness

**Status**: Accepted
**Date**: 2026-02-22
**Deciders**: Platform Engineering

---

## Context

With the core Kubernetes manifests and Helm chart in place (ADR-008), the deployment lacked critical production-readiness controls needed before promoting the system to a live environment:

1. **Availability under node maintenance** — rolling upgrades and node drains can terminate all replicas of a single-replica deployment simultaneously, causing service outages.
2. **Uncontrolled resource growth** — without autoscaling, agent pods are fixed at 1 replica regardless of queue depth or CPU utilization.
3. **Lateral movement risk** — a compromised agent pod could reach any service in the cluster without restriction.
4. **Namespace resource exhaustion** — a single runaway pod could consume all cluster resources, starving other services.

---

## Decision

Four independent production-readiness controls were added to both the raw Kubernetes manifests and the Helm chart templates:

### 1. HorizontalPodAutoscaler (HPA)

Added `autoscaling/v2` HPAs for all 7 deployments (6 agents + WebGUI). Configuration:

| Deployment | Min | Max | CPU target | Memory target |
|---|---|---|---|---|
| qa-manager | 1 | 3 | 80% | 80% |
| senior-qa | 1 | 3 | 80% | 80% |
| junior-qa | 1 | **5** | 80% | 80% |
| qa-analyst | 1 | 3 | 80% | 80% |
| security-compliance | 1 | 3 | 80% | 80% |
| performance-agent | 1 | 3 | 80% | 80% |
| webgui | 1 | **5** | **70%** | 80% |

Scale-up is aggressive (stabilization 30–60 s, 100% increase per period). Scale-down is conservative (stabilization 300 s, 10% reduction per period) to prevent thrashing. Junior QA and WebGUI have higher max replicas because they receive burst demand directly from users and Celery queues.

### 2. PodDisruptionBudget (PDB)

Added `policy/v1` PDBs for all 7 deployments with `minAvailable: 1`. This prevents Kubernetes from evicting the last running pod during voluntary disruptions (node drains, cluster upgrades), ensuring continuous agent availability.

### 3. NetworkPolicy

Added `networking.k8s.io/v1` NetworkPolicies to enforce least-privilege network access:

- **QA agents** (`component: qa-agent`): ingress from other agents and WebGUI only on health ports 8001–8006; egress to Redis (:6379), RabbitMQ (:5672), DNS (:53), and public internet (for LLM API calls) — private CIDR blocks excluded.
- **Redis**: ingress from agents and WebGUI on :6379 only; no egress.
- **RabbitMQ**: ingress from agents and WebGUI on :5672 and :15672 only; no egress.
- **WebGUI**: ingress from ingress-nginx namespace on :8000 only; egress to Redis, RabbitMQ, agent health ports, DNS, and public internet.

### 4. ResourceQuota

Added a namespace-level `ResourceQuota` capping total resource consumption in `agentic-qa`:

```
CPU requests: 16 cores    CPU limits: 32 cores
RAM requests: 32 Gi       RAM limits: 64 Gi
Pods: 20   Services: 20   Secrets: 20   ConfigMaps: 20   PVCs: 10
```

Quota is enabled by default in raw manifests and opt-in (`resourceQuota.enabled: false`) in the Helm chart to avoid blocking minimal local deployments.

---

## Helm Chart Changes

The Helm chart was updated to expose all four controls via `values.yaml`:

```yaml
autoscaling:
  enabled: true          # HPA on/off for all agents + WebGUI
  minReplicas: 1
  maxReplicas: 3
  juniorQaMaxReplicas: 5
  webguiMaxReplicas: 5

networkPolicy:
  enabled: true          # NetworkPolicies on/off

podDisruptionBudget:
  enabled: true          # PDBs on/off
  minAvailable: 1

resourceQuota:
  enabled: false         # Off by default; enable in production
  requests:
    cpu: "16"
    memory: "32Gi"
  limits:
    cpu: "32"
    memory: "64Gi"
  pods: "20"
  ...
```

New Helm templates added: `hpa.yaml`, `pdb.yaml`, `resource-quota.yaml`. The existing `network-policy.yaml` template was wired to `networkPolicy.enabled`.

---

## Consequences

### Positive

- **Zero-downtime maintenance**: PDBs prevent evicting the last pod during rolling updates or node drains.
- **Cost efficiency**: HPA scales workers down during idle periods, reducing cloud spend.
- **Blast radius containment**: NetworkPolicies prevent lateral movement if any pod is compromised.
- **Cluster stability**: ResourceQuota prevents a single namespace from monopolizing cluster resources.
- **Parity**: Raw manifests and Helm chart now render equivalent production-ready infrastructure.

### Negative / Trade-offs

- **metrics-server required**: HPA depends on the Kubernetes Metrics Server being installed in the cluster. Local clusters (kind, minikube) need it enabled explicitly.
- **CNI dependency**: NetworkPolicies are enforced only if the cluster's CNI plugin supports them (Calico, Cilium, WeaveNet, etc.). AWS VPC CNI and GKE Dataplane V2 support them natively; others may not.
- **PDB with minReplicas=1**: A PDB with `minAvailable: 1` on a single-replica deployment will block node drain until the pod is rescheduled elsewhere, which requires available node capacity.

### Mitigations

- Helm chart defaults are non-disruptive (`autoscaling.enabled: true`, `networkPolicy.enabled: true`, `podDisruptionBudget.enabled: true`, `resourceQuota.enabled: false`).
- Operators can disable any control independently without affecting others.
- Environment-specific values files (`values-dev.yaml`, `values-prod.yaml`) are provided as starting points.

---

## Alternatives Considered

| Alternative | Reason Not Chosen |
|---|---|
| KEDA (Kubernetes Event-Driven Autoscaling) | Requires additional operator install; HPA v2 with CPU/memory is sufficient for current workloads. Revisit if RabbitMQ queue-depth-based scaling is needed. |
| Istio service mesh for network policy | Too heavyweight for current scale; native NetworkPolicy covers the isolation requirements without sidecar overhead. |
| VPA (Vertical Pod Autoscaler) | Causes pod restarts on resize; HPA horizontal scaling is preferred for agent workloads. |
| Quota on individual agents | Namespace-level quota is simpler to manage and prevents total runaway scenarios. |

---

## Related ADRs

- [ADR-008](008-deployment-strategy.md) — Deployment Strategy (raw manifests + Helm)
- [ADR-010](010-security-strategy.md) — Security Strategy (network isolation, hardened containers)
- [ADR-015](015-observability-stack.md) — Observability (metrics that drive HPA decisions)
- [ADR-016](016-communication-hardening.md) — Communication Hardening (circuit breaker at application layer)
