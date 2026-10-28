---
name: rootstock-upstream-integration
description: Use when adapting Balancer SDK or other upstream DeFi libraries to Rootstock, reviewing inherited contract routing, dependency upgrades, deployment registry drift, swap quotations, simulation, or unsigned transaction construction.
metadata:
  author: basednut-research
  version: "0.3.0"
---

# Rootstock upstream integration — read-only audit first

**This skill grants no execution privileges.** Load canonical Rootstock `deployments/base.json` or `base-sepolia.json` and record the exact source blob before inspecting an upstream adapter. Verify current protocol contracts separately via chain RPC and provenance sweeps when tools are available.

## Decision process

1. Identify the exact upstream package and installed version. Rootstock currently references `@balancer/sdk` version 6.2.0; its **inspected** pnpm patch rewrites Router/Vault-related mappings for Base and Base Sepolia. Do not assume unpatched upstream addresses are used in its actual application; verify the effective installed bundle and regression-test the patch before claiming runtime parity.
2. Trace each upstream public operation to its underlying address source. In Balancer SDK v6.2.0, `SwapV3.querySingleSwap` uses `AddressProvider.Router(chainId)`. On Base, upstream Balancer's Router and Rootstock's Router are different addresses.
3. Never substitute Balancer's production `balancerV3Contracts` constants for Rootstock's Vault/router/factory deployments. Determine whether the upstream API permits injection; do not work around by mutating dependency internals without review.
4. Separate `query` and simulation (read-only) from `buildCall` (unsigned preparation), and signing/broadcast (privileged). Reject unknown targets, chains, selectors, pool types, missing metadata and ambiguous registry names.
5. A contract name can appear in several deployment tasks. Never choose the first match. If distinct addresses match one name, require an explicit task, audited designation, or valid historical block range.
6. For pool discovery, follow Vault `PoolRegistered` event source and block provenance, not factory events alone. Keep unknown pool math as `UNKNOWN`, and do not fabricate indexed TVL/volume. Block height is not a wall-clock time.
7. Inspect security skill before changing any non-read operation. Do not introduce wallet or private-key requirements for reads.

Before coding a protocol adapter, read [integration evidence and failure cases](references/BALANCER_SDK_BOUNDARIES.md), then add an offline rejection test and, when possible, a real RPC/fork validation test. Feed source-backed corrections into skill text and CLI implementation.
