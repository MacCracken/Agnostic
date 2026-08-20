# Deploying Agnostic on AGNOS OS

This guide covers running Agnostic on [AGNOS OS](https://github.com/MacCracken/agnosticos) — an AI-native Linux OS that provides a managed LLM gateway, agent runtime, and OS-level security sandboxing.

For the technical design, see [ADR-021: AGNOS OS Integration](../adr/021-agnosticos-integration.md).

---

## What Changes on AGNOS OS

| Capability | Standard Linux | AGNOS OS |
|------------|---------------|----------|
| LLM inference | Direct to Ollama/OpenAI | Via AGNOS LLM Gateway (port 8088) |
| Token accounting | None | Per-agent, OS-managed |
| Response caching | None | Shared TTL cache across all agents |
| Security sandboxing | Docker isolation only | + Landlock + seccomp-bpf (OS-enforced) |
| Audit logging | Agnostic app logs | + OS-level agent audit trail |

The Docker containers, Redis, RabbitMQ, Chainlit WebGUI, and all agent logic remain unchanged.

---

## Prerequisites

1. AGNOS OS installed and booted (or agnosticos dev build running)
2. `llm-gateway daemon` running on port 8088
3. Ollama running with your desired models loaded
4. Docker and Docker Compose available on the AGNOS OS host

---

## Setup

### 1. Clone Agnostic

```bash
git clone https://github.com/MacCracken/agnostic
cd agnostic
cp .env.example .env
```

### 2. Configure for AGNOS OS

Edit `.env` and set:

```env
# AGNOS OS LLM Gateway
AGNOS_LLM_GATEWAY_ENABLED=true
AGNOS_LLM_GATEWAY_URL=http://localhost:8088
AGNOS_LLM_GATEWAY_API_KEY=agnos-local

# Route agents through the AGNOS gateway
PRIMARY_MODEL_PROVIDER=agnos_gateway
FALLBACK_MODEL_PROVIDERS=ollama,openai

# Keep your cloud API keys for fallback
OPENAI_API_KEY=your_key_here
```

The `ollama` entries in `.env` can optionally be removed or set to the gateway URL, since the AGNOS gateway manages Ollama internally.

### 3. Start Agnostic

```bash
docker compose up -d
```

### 4. Verify Gateway Routing

```bash
# Confirm agents are calling the gateway
llm-gateway stats
# Should show token usage per agent after first QA session
```

---

## Running Without AGNOS OS

If AGNOS OS is not available (CI/CD, local dev on standard Linux), no changes are needed. Leave `AGNOS_LLM_GATEWAY_ENABLED=false` (the default) and the `fallback_providers` will be used. The `agnos_gateway` provider entry in `config/models.json` is inert when disabled.

---

## Troubleshooting

See [AGNOSTIC_INTEGRATION.md](../../agnosticos/docs/AGNOSTIC_INTEGRATION.md) in the agnosticos repository for full troubleshooting steps.

---

## Related

- [ADR-021: AGNOS OS Integration](../adr/021-agnosticos-integration.md)
- [ADR-007 in agnosticos](../../agnosticos/docs/adr/adr-007-agnostic-integration.md)
- [AGNOS Integration Guide](../../agnosticos/docs/AGNOSTIC_INTEGRATION.md)
