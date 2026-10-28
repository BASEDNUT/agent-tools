---
name: rootstock-pool-discovery
description: Inspect and design read-only discovery of Rootstock Vault pools, factories, token wrappers and event history. Use for PoolRegistered logs, RPC scans, indexer cursors, reorg handling, duplicate events, unknown factory types, and chain-specific pool registries.
compatibility: Read-only source access; optional RPC to Base 8453 or Base Sepolia 84532. No signing.
metadata:
  author: basednut-research
  version: "0.1.0"
---

# Rootstock pool discovery

## Dependency

First apply `rootstock-source-audit` to identify the exact Vault and deployment scan start for the intended chain.

## Workflow

1. Record `(chainId, vaultAddress, deploymentFromBlock, factory mapping, code commit)`. Do not use a hardcoded network-global Vault or pool count.
2. Scan **Rootstock Vault** `PoolRegistered` logs from the proven deployment block, using bounded block windows and provider retries. Scanning factories alone misses direct pool registrations.
3. Separately collect factory `TokenCreated` and `WrapperCreated` events using factory-specific ABIs, addresses and start blocks. These are not pool registrations.
4. Deduplicate by `(chainId, txHash, logIndex)`; keep blockHash and parent block context. Re-scan a confirmation overlap and roll back replaced blocks on reorg.
5. Verify that each candidate pool is registered on the correct Vault, has deployed code and plausible token metadata at a consistent block. Distinguish verified factory type from unknown factory.
6. Emit typed records with explicit `unknown` values for missing classifications and `null` for unavailable metrics. Never fabricate TVL, APY, 24h volume or fees.
7. Cross-check source-repo baked registry only as a dated seed; new pools should be discovered from events rather than editing a finite hard-coded list.

## Output

`pool identity + chain/block provenance + factory + tokens/decimals + pool math + source status + unresolved fields + reorg/replay coverage`.

## Negative cases

- Wrong Vault on same chain: reject.
- Same symbol used by two different contracts: preserve two records.
- Direct pool missing factory event: include if Rootstock Vault registration verifies.
- Unknown factory: type `UNKNOWN`; do not guess a router or math family.
- Historical RPC log gaps: retry via independent provider or mark a range missing; never call partial history complete.

Read [references/EVENT_MODEL.md](references/EVENT_MODEL.md) for deterministic indexer test requirements.
