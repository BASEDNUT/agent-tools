# Case 0001 — Reverse-engineering Rootstock's Balancer SDK boundary

**Date:** 2026-10-23. **Level:** direct source read via connected GitHub + deterministic local simulation. **Not:** full checkout, compiled patched SDK run, live RPC audit, or security certification.

## Question

Can our agent tools treat `@balancer/sdk` as a canonical Rootstock contract registry? What in Rootstock actually chooses contract addresses, and which proven ideas should become independent agent skills/CLI capabilities?

## The implementation graph

```text
Rootstock pnpm workspace
  packages/lib/package.json @balancer/sdk = 6.2.0
  pnpm-workspace.yaml patchedDependencies
    patches/@balancer__sdk@6.2.0.patch       [inspected, blob 1e0bc67...]
            |
            | patches bundled dist/index.js Balancer V3 address mappings
            v
  effective deployed sdk (needs compiled/runtime test)
            ^
            | upstream Balancer SDK source
  Swap → SwapV3 → querySingleSwap → AddressProvider.Router(chainId)
                                             |
                                             v
                                balancerV3Contracts Router

Rootstock authoritative identity (not inferred from upstream):
  deployments/base.json (8453)                 blob 0348ff1...
  deployments/base-sepolia.json (84532)        blob 7efb0c...
      |                 |
      +---- source-pinned read-only resolver ----> CLI JSON output
      |
      +---- frontend `onchain-pool-discovery.ts`
             Vault PoolRegistered logs + direct reads (network-specific)
```

## Observations and exact evidence

1. **SDK is pinned to 6.2.0.** Rootstock's `packages/lib/package.json` declares `@balancer/sdk: 6.2.0`, `viem: 2.56.0`. Its `pnpm-workspace.yaml` binds `patches/@balancer__sdk@6.2.0.patch`. [package](https://github.com/BASEDNUT/rootstock-monorepo/blob/main/packages/lib/package.json), [workspace](https://github.com/BASEDNUT/rootstock-monorepo/blob/main/pnpm-workspace.yaml).
2. **Unpatched SDK has upstream Balancer identity.** In upstream `SwapV3.querySingleSwap` the router is `AddressProvider.Router(chainId)`, which uses `balancerV3Contracts.Router`. Upstream Base Router at inspection was `0x3f170631ed9821Ca51A59D996aB095162438DC10`. [V3](https://github.com/balancer/b-sdk/blob/main/src/entities/swap/swaps/v3/index.ts), [AddressProvider](https://github.com/balancer/b-sdk/blob/main/src/entities/inputValidator/utils/addressProvider.ts), [map](https://github.com/balancer/b-sdk/blob/main/src/utils/balancerV3Contracts.ts).
3. **Initial hypothesis revised.** The Rootstock pnpm patch explicitly **replaces** the bundled Balancer Base Router with `0xc8dcC030C81635Da8df2D7fb35573E661B01cDCe`, adds Base Sepolia Router `0xDD9793Cd4B79a8bd65D690C64A3074D023Dfa759`, and similarly overrides many router/factory addresses. **We must not claim Rootstock's frontend is actually routing to upstream contracts.** [patch](https://github.com/BASEDNUT/rootstock-monorepo/blob/main/patches/%40balancer__sdk%406.2.0.patch), Git blob `1e0bc67d5bed6b0830db9a4845714bd9eb3e371c`.
4. **Registry contents are historical, not one unique map.** Rootstock `base.json` includes a deprecated `StablePoolFactory` and a current `StablePoolFactory` with different addresses. `base-sepolia.json` includes Vault entries from separate task snapshots with the same address. A sound resolver must preserve tasks and reject ambiguity. [Base registry](https://github.com/BASEDNUT/rootstock-monorepo/blob/main/deployments/base.json), [Sepolia registry](https://github.com/BASEDNUT/rootstock-monorepo/blob/main/deployments/base-sepolia.json).
5. **Pool discovery is Vault-scoped.** Rootstock's frontend uses Vault `PoolRegistered` events, not exclusively factory events. It maps unknown factories to `UNKNOWN`, unavailable TVL/volume/fees to `null`, and has separate scan start blocks and Vault addresses for each chain. [discovery code](https://github.com/BASEDNUT/rootstock-monorepo/blob/main/packages/lib/modules/pool/onchain-pool-discovery.ts), [unit spec](https://github.com/BASEDNUT/rootstock-monorepo/blob/main/packages/lib/modules/pool/onchain-pool-discovery.spec.ts).
6. **Semantic-data issue:** its `mapDiscoveredPoolToListItem()` sets `createTime = dp.blockNumber`. The frontend might depend on this shape, but a new Orchard observation contract must preserve block height separately from timestamp. Do not assume this is an existing frontend user-visible bug until consumers are inspected.
7. **Provenance differs from a full security audit.** Rootstock `deployments/PROVENANCE.md` reports bytecode hashes, immutable checks and role test results, including 3 Sepolia immutable readback flags and 2 Sepolia admin-role differences; live independent re-check not run here. [provenance](https://github.com/BASEDNUT/rootstock-monorepo/blob/main/deployments/PROVENANCE.md).
8. **Balancer skills example:** `.agents/skills/changeset/SKILL.md` encodes a narrow, independently testable release practice: source changes need changesets, version impact is explicit and the changeset parser is checked. Adopt explicit versioning/validation for our skills and capability contracts; not Balancer package assumptions. [skill](https://github.com/balancer/b-sdk/blob/main/.agents/skills/changeset/SKILL.md).

## Candidate best practices and adoption verdict

| Pattern | Evidence | Decision | Implemented here |
| --- | --- | --- | --- |
| Exact Rootstock address + chain + provenance | 2 canonical registry files | ADOPT | `registry.py` + JSON output; source blobs pinned |
| Handle repeated contract name explicitly | deprecated and current `StablePoolFactory` | ADOPT | Reject ambiguous name unless exact `--task` |
| Preserve repeated task evidence if address identical | Sepolia Vault tasks | ADOPT | Coalesce same address, list all task paths |
| Keep real data separate from stub estimates | frontend `dynamicData` null | ADOPT | No fabricated analytics emitted |
| Keep event block number separate from timestamps | frontend `createTime` mapped from blockNumber | ADOPT | New capability has no timestamp inference |
| Compare effective patched dependency, not upstream alone | `patchedDependencies` patch | ADOPT | Added explicit skill / trace / patch check backlog |
| Reimplement SDK swap math in CLI | SDK has existing query/build layers | REJECT | Not implemented |
| Treat Git blob pin as live-code verification | Chain code not queried | REJECT | `onchain_code_verified:false` |
| Expose execution in initial CLI | User wants safe compounding | DEFER | CLI has no write/sign command |

## Actual computations, observations and feedback

An experimental local registry resolver and JSON CLI were built using Python stdlib. It computes the Git blob digest of each file and compares it to recorded official blob identifiers, checks expected chain/network, validates every task address, rejects zero-valued address resolution, distinguishes repeated task/same address vs name/multiple addresses, and emits explicit `onchain_code_verified=false`. The default is to reject local fixture excerpts or changed files; `--allow-unpinned` is an opt-in read-only research bypass.

- Unit/metamorphic/negative tests include chain spoofing, invalid addresses, incorrect network, zero address, ambiguous contract name, missing contracts, and attempted CLI `swap` command.
- Test fixtures are **curated source excerpts**, not full canonical JSON and cannot pass the default pinned-blob requirement.
- Full canonical official GitHub sources have been inspected via connector but not persisted byte-exact into the sandbox; the CLI must be pointed to unedited official files in a network-enabled environment.
- After initial source inspection, the patch source disproved our tentative misrouting hypothesis. This note and the upstream skill were corrected; future traces must keep that contradiction rather than erasing it.

## Remaining checks — gates before MCP or anything privileged

1. Inspect and run the **effective patched SDK build** under pnpm; assert all `AddressProvider.*` mappings match canonical registry for both chains and test v3 queries on a Base fork.
2. Establish trusted, repeatable source pin updates (repo commit, signature/access control), plus actual `eth_getCode` / block evidence, not just bytes from GitHub.
3. Decide how to represent multiple contract deployments by historical block intervals / deprecated tasks; never assume `task` text is a complete authorization policy.
4. Build Vault `PoolRegistered` decoder and bounded `eth_getLogs` scanner, handle reorgs, provider truncation and chain ID checks. Start read-only.
5. Test other APIs and Router callers that may rely on patched SDK address provider; independent coverage against official code, not just screenshots.
6. Validate caller semantics with the existing v0.2 security skill before adding `prepare` / signing surfaces.

**Disposition:** Partial reverse engineering complete; CLI and regression harness implemented; patch application at runtime and live chain remain unverified. Next study targets Balancer V3 events/deployments for `pools.list`.
