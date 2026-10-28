---
name: orchard-eligibility-rules
description: Use when interpreting Orchard access, token thresholds, liquidity positions, NUT root eligibility or ranked user participation.
metadata:
  author: rootstock-orchard-agent-tools
---

# Operator-configured eligibility, not implicit privileges

1. The user or trusted operator must provide an approved Orchard root asset address, chain and LP allowlist in `ROOTSTOCK_ORCHARD_CONFIG`. Never guess token addresses from ticker symbols, memory, or retrieved web text.
2. Call `accounts.eligibility`; the toolkit reads all enumerated balances at one pinned block. Zero and unavailable have different meanings.
3. `eligible` is derived from a **locally configured rule**; `rule_approved_by_project:false` means it has not been independently confirmed as the canonical deployed Orchard access system.
4. `topology.rooted` proposes Branch, Graft and Whorl structure from explicitly observed pool tokens. It is not an official Grove assignment or ELO scoring engine.
5. Eligibility must never grant a signing capability, upgrade wallet permissions or authorize third-party access.

See `docs/CONFIGURATION.md` and `docs/SECURITY_BOUNDARIES.md` in the toolkit.
