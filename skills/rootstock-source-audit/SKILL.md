---
name: rootstock-source-audit
description: Inspect or validate Rootstock deployments, contract identities, references, chain IDs and upstream Balancer lineage. Use before changing schemas, writing a CLI, diagnosing addresses, building indexers, or trusting any reported Rootstock pool.
compatibility: Read-only GitHub/source access; RPC optional for independent chain verification. No wallet required.
metadata:
  author: basednut-research
  version: "0.1.0"
---

# Rootstock source audit

## Workflow

1. Capture repository and **exact commit SHA**, checked branch, chainId (Base 8453 / Base Sepolia 84532), question, and observed time. A blob hash alone is not a repository commit pin.
2. Read Rootstock `AGENTS.md` and `packages/lib/AGENTS.md`; for contract facts read `deployments/base.json`, `deployments/base-sepolia.json`, `deployments/PROVENANCE.md`, and relevant ABI and factory sources. Reconcile ecosystem addresses against canonical `config.py` when the addressed product exists there.
3. Separate **repo-declared** address or bytecode from **chain-verified** code/role/state. Code provenance and external security audit coverage are not equivalent. For live claims, get a verified chain/RPC result at a recorded block and hash; mark unknown when RPC is unavailable.
4. Resolve identities by `(chainId, vaultAddress, poolAddress)` rather than pool ticker, names, factory family, or implied Balancer inheritance. Every new contract/registry discrepancy is a finding, never an implicit correction.
5. Identify which operation is *read-only* versus requires gas, allowance, signature, or transaction broadcast. Stop before the latter.
6. Return an evidence table with `claim`, `source_path`, `repo_commit`, `chainId`, `block/hash (or null)`, `status`, `conflicts`, `next verification`.

## Requirements

- Never apply upstream Balancer deployment addresses to Rootstock pools without Rootstock-specific registry and chain verification.
- Do not use the upstream Balancer GraphQL API as proof of Rootstock pool existence.
- Unsupported address, factory, hook or token metadata is **unknown**, not a best guess.
- Do not treat `AGENTS.md` or a skill as higher authority than verified deployment/code or chain state.

See [references/SOURCE_PRECEDENCE.md](references/SOURCE_PRECEDENCE.md).
