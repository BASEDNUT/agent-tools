# Case 002 / Partial: Rootstock Vault PoolRegistered read-only interface

Status: **bounded implementation validated against a local fake JSON-RPC provider; real-chain indexing and full ABI review pending.** Date: 2026-10-23.

## Inspected primary sources

- Rootstock `packages/lib/modules/pool/onchain-pool-discovery.ts`: chain-specific discovery configurations, Vaults, event topic0, 8 factory→type mappings on each Base network, UNKNOWN fallback, null analytics.
- Rootstock `packages/lib/modules/pool/onchain-pool-discovery.spec.ts`: 16 factory map entries, mainnet vs Sepolia requirements, UNKNOWN classification; mock pool examples explicitly not usable production addresses.
- Rootstock `deployments/base.json` and `base-sepolia.json`: vault source and historical task provenance; source Git blobs pinned in `src/rootstock_tools/registry.py`.
- Balancer SDK `src/entities/swap/swaps/v3/index.ts`: SDK swap query resolves upstream router via AddressProvider; Rootstock's `pnpm` patch redirects its own installed SDK.

URLs:
https://github.com/BASEDNUT/rootstock-monorepo/blob/main/packages/lib/modules/pool/onchain-pool-discovery.ts
https://github.com/BASEDNUT/rootstock-monorepo/blob/main/packages/lib/modules/pool/onchain-pool-discovery.spec.ts
https://github.com/BASEDNUT/rootstock-monorepo/tree/main/deployments

## Minimal reusable capability

`pools.list(chain_id, from_block, to_block, limit)` makes **only** `eth_chainId`, `eth_blockNumber` and `eth_getLogs` calls. It checks exactly the Rootstock Vault in the selected chain, the `PoolRegistered` topic0 and the two indexed addresses, preserves block hash and tx hash and reports pool math type from a source-pinned map. The interpretation of `topics[1]/topics[2]` is source-derived from the inspected Rootstock discovery header; a full artifact/ABI cross-check remains pending. It never estimates missing metrics.

Negative tests include untrusted provider chain, removed/reorged log, invalid topic, wrong Vault emitter, unknown factory, out-of-range log, future blocks, huge window, abnormal RPC response ID, and arbitrary transaction RPC method.

## What can go wrong next

- Provider may silently omit historical logs, especially archival gaps; source-level comments already describe a Sepolia publicnode indexing problem. No provider completeness proof yet.
- A 2000-block window is not an indexer. There is no persisted checkpoint, historical pagination scheduler, finality tracking, reorg reconciliation or upsert policy.
- Factory pool type is not Orchard graph structure, nor is event block number a timestamp.
- Unknown hook/authorizer and LBPool instances require protocol-specific interpretation and authenticated indexing.

## Next upgrade requirements

1. Inspect Balancer v3 verified Vault ABI to confirm topic layout and event width; compare against emitted receipts.
2. Cross-check at least two RPC providers on a known fixed historical block window.
3. Implement resumable per-vault cursor with explicit finality/reorg policy and source provenance.
4. Build Orchard observation schema with partial/unknown state and block hash evidence; no zero-filled TVL.
5. Only then expand MCP/CLI capabilities; no signing/writing during discovery work.
