# ADR-0001: Registry-first, source-pinned read-only capability

- **Status:** accepted for local proof of concept; production policy pending
- **Date:** 2026-10-23
- **Drivers:** Rootstock has its own contracts; Balancer SDK v6.2.0 embeds Balancer chain addresses; Rootstock uses a pnpm patch to redirect these; registries can hold duplicate contract names; autonomous tools need fail-closed identity.

## Decision

Implement `registry.list_networks` and `registry.resolve_deployment` first, backed by explicit locally supplied Rootstock deployment JSON files. Validate chain labels, Ethereum address shape and pinned Git blob. Resolve by `(chainId, contractName, optional exact task)`. Same-name/same-address duplicate tasks are coalesced with preserved provenance. Same-name/different-address results are **ambiguous and rejected** absent explicit task.

Expose JSON results with `source_blob_sha`, `source_pinned` and `onchain_code_verified=false`. Never imply this is an actual `eth_getCode` result. Reject mutated/unpinned sources by default; a conspicuous research-only override is permitted solely for offline reading.

## Rejected alternatives

- Call upstream `AddressProvider.Router(chainId)` with unpatched SDK and assume it points to Rootstock — wrong protocol identity.
- Duplicate upstream SDK logic inside a new CLI — needless drift.
- Pick first `StablePoolFactory` key in task iteration — may select deprecated address.
- Hardcode a full registry copy without a reviewed refresh path — stale and hard to audit.
- Treat a Git SHA as independent runtime bytecode verification — category error.

## Follow-up before production

Read actual pnpm installed artifact with the patch applied and cross-check all important names/chain addresses; record version/deployment matrix; independently query on-chain code and authorizer readbacks with block hashes; authenticate Git source/ref beyond raw blob equality; perform exact URL and registry update review; introduce production policy interception before any privileged capability.
