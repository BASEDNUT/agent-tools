---
name: orchard-valuation-provenance
description: Use when deriving Rootstock pool TVL, swap metrics, token valuations, turnover, rates, provenance or comparing observed versus estimated values.
metadata:
  author: rootstock-orchard-agent-tools
---

# Source-qualified financial measurements

1. Pull pool balances from `pools.inspect` at one pinned block and require token decimals. Missing data means **null**, not zero.
2. Only compute USD TVL if the trusted operator provides an explicit `ROOTSTOCK_PRICE_BOOK` with the same chain ID, block height and hash; the price source and all token prices must be present.
3. `analytics.tvl` returns `derived_from_operator_prices`, not verified market TVL, because matching the block hash does not cryptographically attest quoted prices.
4. Do not calculate genuine 24h turnover from lifetime indexed events and a single point-in-time price sheet. A fully indexed, timestamp-aligned historical USD volume and TVL series is required.
5. Never aggregate raw balances from tokens with different decimals, mistake token rates for price data, or use the model to invent missing prices.

See `docs/CONFIGURATION.md` for input contracts.
