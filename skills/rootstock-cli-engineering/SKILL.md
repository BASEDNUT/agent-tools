---
name: rootstock-cli-engineering
description: Design or build the Rootstock and Orchard read-only CLI after the source, pool discovery and data contracts are validated. Use for commands, JSON output, stable errors, dry-run conventions, SDK reuse, tests or later MCP wrapping.
compatibility: Requires a source checkout for implementation; this v0.1 skill defines behavior only and does not install or run a Rootstock CLI.
metadata:
  author: basednut-research
  version: "0.1.0"
---

# Design a reliable CLI that later supports MCP

## Dependencies

Consult `rootstock-source-audit` first; use `rootstock-pool-discovery` for pool enumeration and `orchard-data-integrity` for metrics. Do not write duplicated protocol logic into shell commands.

## First version: only read-only commands

- `rootstock --version` / `--help` / `doctor` — versions, environment, registry commit, provider availability; no secrets in output.
- `rootstock chains list` — explicit Base and Base Sepolia supported IDs.
- `rootstock deployments inspect --chain <id>` — registry data with source/status; no independent verification claimed without RPC readback.
- `rootstock pools list --chain <id>` / `pools inspect` — code-verified identities, unknown fields preserved, status and block provenance.
- `orchard metrics explain <resourceId>` — formula, required source fields and availability; **not** invented numeric values.

These command names are **proposals**, not executable commands in this package.

## Engineering contract

1. One typed domain library for queries and validation. CLI, API and future MCP call that library; do **not** route production MCP through brittle parsing of human CLI text.
2. Accept `--output json`; emit one machine-readable envelope with `{ok, data|null, error|null, meta}` and documented stable error codes. Print diagnostics to stderr only.
3. No TTY prompts in agent/JSON mode. No credential requirement for public read-only operations. Apply timeouts, retries, rate limits and RPC-provider health checks.
4. Make `--chain` explicit for identity-bearing commands; fail closed if unknown. Never infer addresses by token symbol. Persist block/source timestamps.
5. Future transaction commands must be separate, unimplemented until formally authorized. They require simulation, explicit risk/permission checks, signing separation and independent wallet review.
6. Publish command help and JSON schemas from one capability catalog; contract-test CLI outputs against fixtures.

See [references/CLI_SPEC.md](references/CLI_SPEC.md).
