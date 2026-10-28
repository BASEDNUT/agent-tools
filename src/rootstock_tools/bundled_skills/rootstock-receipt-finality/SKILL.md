---
name: rootstock-receipt-finality
description: Use when checking Ethereum/Base receipts, confirmations, reorgs, transaction status, or safe event polling.
metadata:
  author: rootstock-orchard-agent-tools
---

# Transaction evidence and finality

- Call `transactions.status` with the chain ID and exact 32-byte tx hash. It checks receipt.blockHash against the current RPC block header, and reports count of confirmations.
- `canonical_at_provider_head` is provider-relative. `finality_verified:false` stays false: Base L2 finality requires independent knowledge of L1 batches/proofs/chain-specific safe or finalized heads.
- Reject a missing header or changed hash; do not turn a disputed receipt into an unverified success.
- For index polling use `watch.cursor` `(since_block, since_log_index)` to avoid dropping later events inside the same block. The index must separately report scanned intervals.
- Never interpret an unconfirmed receipt, quote, `eth_call`, or indexed event as authority to execute a transaction.

Reference: [Rootstock event index](https://github.com/BASEDNUT/rootstock-monorepo) and [Balancer Vault events](https://github.com/balancer/balancer-v3-monorepo/blob/main/pkg/interfaces/contracts/vault/IVaultEvents.sol).
