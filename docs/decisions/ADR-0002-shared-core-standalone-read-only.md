# ADR-0002 — One implemented core, multiple standalone read-only adapters

Status: accepted for beta testing; does NOT authorize write operations.
Date: 2026-10-23

## Context
The earlier v0.3 workspace had a useful registry CLI and skills but no MCP, SDK packaging or self-contained client setup. Implementing separate logic in each transport would produce drift and inconsistent security checks.

## Decision
- `Toolchain.run(name,args)` is the only capability dispatcher. All surface inputs validate against the same schemas.
- Interfaces: `rootstock` CLI; `rootstock-mcp` stdio; `rootstock-api` local HTTP; importable Python SDK; portable Agent Skills.
- Modern MCP is 2026-07-28 (stateless, request `_meta`, `resultType`) and legacy 2025-11-25 is supported for existing clients.
- Read-only RPC and source-locked deployments only. No general `eth_call` exposed for the model, no `eth_sendRawTransaction`, no wallets. Resource access to bundled skills is read-only.
- Registry bootstrap requires an explicit download; full canonical files are NOT synthesized from fixture subsets. CLI commands that do not need the registries still work before setup.

## Consequences
- Safe read-only sandbox operations are independently runnable using Python >=3.11 and zero runtime dependencies.
- Protocol-specific reads can later be shared across interfaces; application itself is not modified.
- Financial execution is out of scope until actual policy and signing infrastructure exists.
- Tests exercise real stdio messages and local fake-RPC transport, but no live chain execution.
