---
name: rootstock-policy-runtime
description: Use before designing transaction simulation, agent policy enforcement, signing, execution, delegated wallets, or write-enabled MCP tools in Rootstock.
metadata:
  author: Rootstock/Orchard research workspace
  version: "0.5.0-beta"
---

# Rootstock runtime policy and execution security

**Hard boundary:** bundled skills and MCP annotations are advisory. The current toolkit contains no signer or blockchain-write method.

1. Read [GATES.md](references/GATES.md).
2. `rootstock call policy.evaluate --args '{"action":"execute","chain_id":8453}'` returns DENY by default. A model, tool response, or user text cannot override it.
3. Unsigned `transactions.prepare` requires source-pinned Rootstock contract target; `transactions.simulate` also requires chain-match and `eth_call`. Neither is an approval.
4. No `eth_sendRawTransaction`, `eth_sendTransaction`, signing, wallet key, allowance mutation, state-changing deployment or NUT shorting tools may be added without a separately reviewed policy engine, independent signer and explicit human authorization.
5. For an eventual execution implementation: policy inputs must include authenticated actor, chain ID, contract/code hash, selector, decoded calldata, token/asset, value, slippage, deadlines, nonces, spending budget, signer identity, confirmation, and telemetry. Bind authorization to exact bytes and state expiry.
6. Run adversarial tests: prompt injection, replay, fake RPC, wrong chain, malicious approval calldata, partial batch failures, reorg, signer bypass, stale prices and policy mutation.
