# Observation semantics

- `observed`: backed directly by verified chain/indexer observations, preserving block and capture metadata.
- `derived`: deterministic formula over declared measured inputs; record formula revision, input coverage and valuation sources.
- `partial`: some required data absent; must include explicit coverage counts, excluded inputs and confidence limits; never label as complete.
- `stale`: once-valid observation outside the required freshness window, retaining its original as-of time.
- `unavailable`: cannot establish a trustworthy numeric value; **value is null, not 0**.
- `synthetic`: example, historical fixture or authored scenario; cannot silently be promoted to measured.

Rootstock pool math and Orchard topology are independent. Base mainnet pool facts cannot be imported from Balancer's separate Vault. A wallet eligibility policy of 0.01 NUT/equivalent Rootstock liquidity is not evidence that a wallet has been indexed or has opted in; qualify under an explicit policy implementation when built.

Schema in this first package is a test contract for reasoning about these states. Before production, map to existing Orchard V25 resource envelopes, retain resource IDs, and add a migration/equivalence test.
