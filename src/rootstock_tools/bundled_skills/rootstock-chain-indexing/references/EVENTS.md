Official Balancer V3 `Vault` events (ABI source: `https://github.com/balancer/b-sdk/blob/main/src/abi/v3/vault.ts`):

- `PoolRegistered(address indexed pool,address indexed factory,...)`
- `Swap(address indexed pool,address indexed tokenIn,address indexed tokenOut,uint256 amountIn,uint256 amountOut,uint256 swapFeePercentage,uint256 swapFeeAmount)`.
- `LiquidityAdded`/`LiquidityRemoved` have indexed pool, provider, kind, then dynamic amount arrays.

Signatures generated with Ethereum Keccak-256, not SHA3-256. Indexer currently stores raw event data for liquidity dynamic arrays; it does not claim decoded cash-flows or LP P&L. Events are recognized strictly by topic0 and Vault address. SQL checkpoint hashes are source observations, not finalized independent proofs.
