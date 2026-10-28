---
name: orchard-data-integrity
description: Check Orchard financial metrics, account observations, source provenance and liquidity topology before exposing data to agents. Use for TVL, volume, fees, ranks, Branch/Graft/Whorl/Grove relationships, stale/partial data, V25 fixtures or API schemas.
compatibility: Requires read access to Orchard schema/state artifacts. No RPC or wallet needed for fixture review.
metadata:
  author: basednut-research
  version: "0.1.0"
---

# Orchard data integrity

## Workflow

1. Identify the displayed field and its existing Orchard V25 `resourceId`; preserve the current `meta/data/links` API design. This skill does not replace that API.
2. Distinguish **protocol/operator** (Rootstock vs external venue), **math** (Weighted/Stable/reCLAMM/etc.), **Tree topology** (Branch/Graft/Whorl) and **Grove membership** (grouping). Never collapse these axes.
3. For measured data, record chainId, Vault/pool addresses when applicable, blockNumber/hash, time, source, calculation method/version, units, rate/price source, lookback window and completeness.
4. Use statuses exactly: `observed`, `derived`, `partial`, `stale`, `unavailable`, `synthetic`. `synthetic` must never render as observed financial truth.
5. Use `null` for missing values; **zero is a real measured value only**. A partial aggregate must show coverage numerator/denominator. Never preserve an old value as a live fallback when updates are null.
6. Validate wrapper decimals/scaling and pool token weighting from chain state. Do not infer 20/40/40 weights solely from an Orchard label or count boosted wrappers twice.
7. Keep old Orchard route/artwork/metrics and release checkpoints intact. Changes to display are separate from this schema-focused skill.
8. Return a metric-by-metric provenance and completeness report, with failed assertions and follow-up source needs.

See [references/DATA_STATES.md](references/DATA_STATES.md). Provisional examples at `../../schemas/observation.schema.json`.
