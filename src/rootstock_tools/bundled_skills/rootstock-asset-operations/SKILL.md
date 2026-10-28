---
name: rootstock-asset-operations
description: Use when an agent needs to inspect ERC20 metadata, explicit token balances, ERC4626 underlying assets, and pool token identities for Rootstock.
metadata:
  author: Rootstock/Orchard research workspace
  version: "0.5.0-beta"
---

# Rootstock asset and pool inspection

## Procedure

1. Resolve network ID and actual Rootstock Vault from an authenticated source; never use Balancer upstream deployment addresses.
2. Use `rootstock call assets.lookup --args '{"chain_id":8453,"address":"0x..."}'` for symbol, decimals, name, supply, code presence.
3. Use `rootstock call pools.inspect --args '{"chain_id":8453,"pool":"0x..."}'` to call Rootstock `Vault.getPoolTokens`, optional token-info reserves and token metadata. Unknown pool math stays UNKNOWN.
4. Use `assets.wrapper_underlying` only to probe ERC4626 `asset()`. Non-ERC4626 Rootstock wrappers may not support it; never guess underlying relationships.
5. For portfolio, use `accounts.positions` with one explicit ERC20 or LP token address; this is not exhaustive wallet discovery.

[ABI boundaries](references/ABI.md). Every call is read-only `eth_call`. Never authorize signing or approve a token from symbol-only evidence.
