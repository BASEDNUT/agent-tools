# v0.9.1 — superseded-deployment guard + registry repin (2026-10-28)

- Upstream resolved: monorepo commit `6206c91643e2e87c43164be90f963c91a11329ab` syncs
  the S113-fix redeploys into the canonical registries and adds an explicit
  `superseded` never-use map (11 defective deployments: 7 mainnet incl. 3 oracle
  factories with zero sequencer feed, 4 Sepolia owner-defect contracts).
- `CANONICAL_BLOBS` repinned (base.json `39997741...`, base-sepolia.json `825ecb8d...`);
  `SOURCE_COMMIT` repinned to `6206c9164`.
- New defense-in-depth: `KNOWN_SUPERSEDED` — 11 hardcoded addresses; any registry
  (pinned or `--allow-unpinned`) that lists one under a resolvable task fails closed
  at load time.
- New registry `superseded` map parsing: shape-validated (address keys, name,
  `superseded_by` must be deployed in tasks, `never_use: true`); declared-superseded
  addresses are refused at resolve time even if some task still lists them.
- Fixtures mirror the post-sync upstream shape (live addresses + superseded map).
- 168 tests green (10 new superseded-guard tests, RED -> GREEN).

# v0.9.0 — guarded execute layer (2026-10-27)

- Added signer (env-key EIP-1559; key never appears in repr/str/exceptions),
  ExecutePolicy (chain allowlist, registry-pinned router allowlist, per-tx +
  daily wei caps, kill switch), and Executor (mandatory simulate-first,
  receipt verification).
- Execute-mode RPC: broadcast methods only reachable on an explicitly
  execute=True transport; read client structurally cannot send transactions.
- New capabilities: `transactions.send`, `transactions.call_router`,
  `transactions.approve_router` (spender must be an allowlisted router).
- Default remains OFF: no `ROOTSTOCK_SIGNER_KEY` = no signing path reachable.
- Live-proven on Base Sepolia (hot wallet): zero-value self-send, funded
  0.0001 ETH transfer, ERC20 approve, and a real 0.01 BAL -> WETH swap on the
  Rootstock WETH/BAL pool — all receipts verified, deltas reconciled exactly.
  Over-cap and kill-switch refusals adversarially proven live. 158 tests green.

# v0.8.0 — live-chain completion (2026-10-27)

- Fixed live HTTP transport: the toolkit now sends its own User-Agent
  (`rootstock-agent-tools/0.8`); public RPC endpoints (e.g. base.publicnode.com)
  403-reject the default Python-urllib header. Regression test added
  (tests/test_live_transport.py).
- Declared `[project.optional-dependencies].tools` (pyyaml, jsonschema) for the
  audit/verification scripts; the core runtime remains stdlib-only.
- License selected: MIT.
- Live end-to-end verification executed against BASED NUT deployments on
  Base mainnet (8453) and Base Sepolia (84532): registry bootstrap from the
  pinned monorepo, pool discovery via Vault PoolRegistered events (22 mainnet
  pools + the Sepolia Rootstock WETH/BAL pool), pool inspection, multi-token
  balances cross-checked against an independent raw eth_call oracle,\  transaction status on a real deployment receipt, local SQLite event sync
  with history/cursor reads, MCP stdio round-trip (34 tools, correct -32602
  unknown-tool error), loopback HTTP API, wheel install + Node bridge 5/5,
  and skills install (20). Evidence: docs/E2E_EVIDENCE_2026-10-27.md.
- Known data flag: the pinned monorepo registry still lists the four superseded
  S113-fix contracts as resolvable entries; they are read-only provenance data
  and must never be approved or used.

# v0.7.1-beta — independent corrective audit (2026-10-23)

- Fixed Keccak-256 rate-boundary padding: 135+136*k byte inputs previously hashed incorrectly. Cross-checked against OpenSSL KECCAK-256 vectors.
- Fixed overlapping SQLite index rescans deleting already verified coverage outside the rescan interval.
- Added provider-relative snapshot stability checks after pool inspection, wallet position/multi-asset reads and successful ERC4626 probes. Cannot prove independent provider honesty.
- Pin token bytecode and ERC-20 metadata to one verified provider snapshot, rejecting observed reorgs.
- Reject receipt transaction-hash mismatches and non-boolean EIP-658 execution statuses.
- Return JSON-RPC -32602 for unknown MCP tool names, consistent with the 2026-07-28 MCP tools specification.
- Added eight new adversarial regressions; 138 Python tests and five Node tests passing locally with the package on Python's module path.
- Strengthened release verification to cross-check **all Python source modules in the wheel** against source, not just skills.
- This is a development beta, not audited on-chain execution software; no live transactions or signer.

# Changelog

## v0.7.0-beta — October 23, 2026

- Preserved v0.6 foundation and 16 previous skills, extended to 20.
- Patched two quote-state races: fixed same-block Vault membership/Router quote and reorg header check.
- Pinned wallet balance reads to one block, added bounded 32-token portfolio snapshot.
- Receipt verification now compares its block hash to the provider's header and reports provider-relative confirmations, not protocol finality.
- ERC4626 inspection now offers a source-labeled one-share `convertToAssets` probe.
- Added source-qualified partial ABI read catalog, selector inventory, independent unknown signature rejection.
- Added operator-provided pool TVL arithmetic with strict source/chain/block/decimal matching and unverified-price labels.
- Added operator-configured Orchard root/LP eligibility and preliminary Branch/Graft/Whorl classification; no guessed project addresses.
- Added log-index cursor event reads and fixed registration-event retrieval after high-volume swaps.
- Added integration/adversarial tests, aligned schema manifests and updated security boundaries.

## Inherited from v0.6 and older

- Source-pinned Rootstock registry and SDK-patch alignment audit; explicit read-only JSON CLI, MCP stdio, Python SDK and Node bridge.
- Bounded Vault log-index and pool discovery, chain-specific views, policy-scoped reads, local SQLite history/reorg checks, onchain token rates, static fees, raw indexed analytics, forward index following.

## Release boundaries

Offline integration tests alone cannot certify live-chain data, complete historical coverage, source-authentic prices, canonical Orchard ELO, or secure financial signing/broadcast. Those dependencies remain required. Production Rootstock, Orchard and user machines unchanged.
