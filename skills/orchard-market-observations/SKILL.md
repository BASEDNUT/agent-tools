---
name: orchard-market-observations
description: "Validate market and wallet metrics for Orchard before use by agents: indexed swap volume, pool balances, TVL, token pricing, turnover, rankings, historical coverage, timestamps and provenance. Use when creating or consuming analytics or portfolio datasets."
metadata:
  author: Rootstock/Orchard toolchain
  version: "0.6.0-beta"
---

# Orchard market observation integrity

Orchard is the analytics and graph layer above the Rootstock DEX. Do not mistake the frontend as a persistent indexer or authoritative blockchain data source.

## Verification

- For every observation, record chain ID, contract, measurement type, block number/hash, source, unit, numeric precision and timestamp. **Only call it observed if those facts have been read or independently reproduced.**
- Distinguish swap volume in input **token base units** from normalized token units, and from dollar valuation. Never report token sums as USD.
- A time-windowed metric needs complete scanned coverage and timestamps for every contributing event. The absence of timestamps is partial data, not zero volume.
- TVL requires a verified token balance snapshot at a specified block plus trusted price and wrapper/rate evidence from the same appropriate time/height. `analytics.tvl` intentionally returns unavailable otherwise.
- Turnover = verified volume divided by compatible TVL. Do not divide a 500-event sample by a current pool balance and label it 24h turnover.
- Wallet ELO and vanity ranks need a documented canonical Orchard formula; observed swap counts are NOT player ELO.
- Preserve Rootstock pool type, pool math, Orchard graph structure, Grove, address and source status as separate dimensions.

## Acceptance tests

Test missing decimals, wrapper scaling, synthetic prices, multiple chains, reorged history, unknown pool factories, empty vs missing events, partial time coverage, old prices, zero balances, broken source links and stale snapshots.

Read `schemas/observation.schema.json` and the package's `docs/CAPABILITY_COVERAGE.md` before declaring analytics complete.

## Wallet security boundary

This is a **read-only** data-validation skill; it never signs a wallet transaction, controls custody, or grants agent wallet permissions.
