---
name: rootstock-rpc-validation
description: Use when checking Base or Base Sepolia Rootstock RPC identity, interpreting Vault PoolRegistered events, diagnosing missing or duplicate pools, assessing reorg and RPC coverage risks, or designing bounded on-chain read-only scanner tests.
metadata:
  author: basednut-research
  version: "0.4.0"
---
# Rootstock RPC validation

1. Check chain identity (`eth_chainId` must match 8453 or 84532) **before** any reading.
2. Resolve the **Rootstock** Vault for the selected chain; never accept an arbitrary Vault supplied by agent text, an upstream Balancer default, or search results.
3. Specify **inclusive** scan block start and end; scan windows cannot exceed 2,000 blocks. No implicit multi-million-block RPC queries.
4. Decode `PoolRegistered` topic0, `topics[1]` pool and `topics[2]` factory; confirm log emitter is the chain's configured Rootstock Vault and reject removed/reorged logs.
5. Keep pool address, factory, pool math classification, Orchard graph structure, block number, timestamp, and analytics conceptually distinct. A block number is never a timestamp.
6. Preserve transaction hash, block hash, log index, source RPC and selected window. The configured provider is **not** independently verified by a second provider.
7. UNKNOWN factories remain UNKNOWN. An empty window means that provider returned no matching events **for that window**, not that the protocol has no pools.
8. Test with a local fake JSON-RPC server before deploying to an indexing worker. Do not change existing Orchard terminal code in this skill.

Reference: [references/EVENT_BOUNDS.md](references/EVENT_BOUNDS.md).
