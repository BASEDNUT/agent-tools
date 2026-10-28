# Suggested indexer contract (provisional)

**Raw log key** `(chainId, txHash, logIndex)`; **canonical snapshot key** `(chainId, blockHash)`; **pool identity** `(chainId, vaultAddress, poolAddress)`.

Retain raw log, decoded event, source RPC, ABI version, status, scan cursor, confirmation policy, reorg rollback journal and hash of the input. Confirm all event signatures and indexed fields using the exact Rootstock-deployed ABI, not a memorized topic.

Read paths in the Rootstock codebase include `packages/lib/modules/pool/onchain-pool-discovery.ts` and `packages/lib/modules/primitives/`. The former has explicit separation between discovered pool identity and unavailable `dynamicData` analytics.

A deterministic test suite must cover: overlapping windows, duplicate logs, direct pool deployment, unknown factory, reorg with replaced block, RPC gaps, mismatched chain/Vault, token decimals (6/8/9/18), and wrapper rate changes. **No transaction execution** in this skill.
