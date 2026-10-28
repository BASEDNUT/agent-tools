# Rootstock/Orchard DeFi-specific security checklist

## Chain and contracts

- [ ] Requested chain is Base 8453 or Base Sepolia 84532; explicitly identify environment.
- [ ] Rootstock Vault/factory/router references originate from current project deployment manifests, not Balancer's default addresses, symbols or an unauthenticated web page.
- [ ] Critical contract addresses, bytecode, ABI and immutable parameters have independent read-back where necessary; discrepancies fail closed.
- [ ] Pool registration is observed on the exact Rootstock Vault. Factory classification must be independently reconciled; `UNKNOWN` must stay unknown.
- [ ] Wrapped/rate-bearing asset semantics and ERC4626 exchange rates are validated; chain/address/decimals distinguish tokens.

## Financial data

- [ ] Observations carry source status, chain, block number/hash, timestamp, aggregation method/window and freshness.
- [ ] Zero, null, synthetic, partial, observed and derived are not interchangeable.
- [ ] TVL uses common-block Vault balances, valid prices/rates and double-count controls.
- [ ] Swap fees account for hooks, dynamic fees and protocol/LP splits; no `volume * nominalFee` shortcut.
- [ ] LP accounting distinguishes principal, fees, accrued value, unrealized gains, realized PnL and gas.

## Transaction preparation (not authorized in v0.2)

- [ ] Beneficiary, router, pool, Vault, token addresses and chain verified against trusted allowlist.
- [ ] Exact calldata including subcalls, approvals, spender, permits, asset amounts, price limits, slippage, deadline, nonce and gas is decoded and reviewed.
- [ ] Simulate intended bundle under known block state; re-simulate/revalidate on state changes and verify receipt after submission.
- [ ] Per-operation and aggregate limits enforced in external runtime and wallet; don't confuse Safe spending caps with a recipient allowlist.
- [ ] Higher-risk action requires approval bound cryptographically to complete payload; reviewer can see every transfer and target.
- [ ] Emergency revoke/stop, incident response and independent audit events tested.

**Prohibited in this foundation:** signing, approval, trading, liquidity changes, deployment, funds movement and enabling short positions against NUT. Future write capabilities require their own design review and executable security tests.
