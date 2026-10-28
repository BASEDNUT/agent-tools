# Live end-to-end verification — v0.8.0 — 2026-10-27

Executed by Peanutoshi Nutkamoto from the Agent Zero container against live
Base mainnet (8453) and Base Sepolia (84532), targeting BASED NUT / ROOTSTOCK
production deployments. All calls read-only; no signing or broadcast path
exists in the toolkit.

## Environment

- Python 3.13.14, package under test: source tree with `PYTHONPATH=src` and,
  for the bridge, a built wheel installed into `/opt/venv`.
- RPC defaults: `https://base.publicnode.com` (mainnet), `https://sepolia.base.org`
  (Sepolia). Archive-block reads on mainnet used the documented
  `ROOTSTOCK_RPC_BASE=https://base.gateway.tenderly.co` override (Tenderly
  public gateway serves 1000-block archive ranges; publicnode walls archive
  requests behind a personal token).

## Results

| # | Surface / capability | Target | Result |
|---|---|---|---|
| 1 | `setup registries` | pinned monorepo commit f64acbb5, deployments/base.json + base-sepolia.json | both files fetched, Git blob SHA verified (`0348ff1e` / `7efb0c38`), no writes on conflict |
| 2 | `registry.resolve_deployment` | Vault @ 8453 | `0x0a3af0Da0175afa0Cc05a6ad9092dC740155a0E7`, task v3/20250321, source_pinned true |
| 3 | `rpc.get_health` | 8453 + 84532 | both live: head block + hash, chain id enforced |
| 4 | `pools.list` (Sepolia) | registration window 47265020-47265052 | found PoolRegistered for Rootstock WETH/BAL Pool `0x1aba4e89...77c7` at block 47265032 (tx `0x8ac424c5...f4c9`, factory classified WEIGHTED, block hash present) |
| 5 | `transactions.status` | real pool-create tx `0x8ac424c5...f4c9` @ 84532 | included, success true, canonical at provider head, 3.87M confirmations, finality honestly unverified |
| 6 | `pools.inspect` | our Sepolia pool | real WETH/BAL balances from Vault, 0.3% static fee, tvl_usd null (no fabricated USD) |
| 7 | `accounts.balances` | workbench `0x135b...1F65` with NUT/SNUT/wNUT/PIPS | live balances; wNUT `1249643455268467` EXACT-matched an independent raw `eth_call` oracle; PIPS 7.797M consistent with S80-era state |
| 8 | `index sync` + `history.events` | Sepolia window 47265020-47265052 | 2 events indexed, checkpoints correct, history read returns PoolRegistered + SwapFeePercentageChanged with full provenance |
| 9 | MCP stdio | legacy 2025-11-25 handshake | initialize OK, 34 tools listed, live `rpc.get_health` returned, unknown tool correctly -32602 |
| 10 | HTTP API | loopback :8791 | openapi.json + /v1/networks + /v1/pools served; 127.0.0.1 only |
| 11 | `skills install` | /tmp target | 20 skills installed |
| 12 | Node bridge | wheel-installed CLI on PATH | 5/5 tests pass (earlier 2/5 failures were a PATH artifact — `python` resolving to system Python without the package) |
| 13 | `pools.list` (mainnet) | registration windows around baked-registry blocks via Tenderly | all 22 ROOTSTOCK mainnet pools discovered live: tsPHILO 0x93ef211b (STABLE), tsPRETA/tsLOAM/iENG (RECLAMM), rtFRAX/rtUSD+/rtcbETH/rtcbBTC, NUTMOG, MAXCHAD, rks-NUT-WETH, rks-TBTC-CBBTC, rks-WETH-CBETH-SURGE, pNUT 0xf64ae6f6, gtINF/gtAGT/gtETH/gtBTC/gtFX/gtSIL, nutSALT-rCLP, pipsUSDC-rCLP — every address + math type matches the monorepo baked registry |
| 14 | `quotes.swap` | drained Sepolia pool | chain revert surfaced verbatim (selector `0x67f84ab2`) — fail-closed, no fabricated quote |

## Fixes made during this pass (TDD)

1. **User-Agent transport fix**: public JSON-RPC endpoints 403-reject the default
   `Python-urllib/3.x` header. `rpc.py` and `bootstrap.py` now send
   `rootstock-agent-tools/0.8`. Regression test `tests/test_live_transport.py`
   (RED -> GREEN). Full suite 139/139.
2. **Optional tooling deps declared** (`pyyaml`, `jsonschema`) — the audit scripts
   imported them without declaring them.

## Known data flag (monorepo, not this package)

The pinned `deployments/base.json` (byte-identical to monorepo HEAD at the time
of testing) still lists four contracts superseded by the S113-fix owner/oracle
redeployment as resolvable registry entries: TokenPairRegistry `0xb3D9...AeBd59`,
CowSwapFeeBurner `0x9614...5147`, ERC4626CowSwapFeeBurner `0xc9E8...90b6`,
BalancerFeeBurner `0xE6C1...e22d`. The registry is provenance data; resolution
must not be read as approval. These entries should be marked superseded
upstream. `registry.verify_contract` against these addresses performs a presence
check only and must never be used as a basis for interaction.

## Not covered

- Full-archive backfills beyond probed windows (provider range walls).
- Independent multi-provider quorum for log completeness (single provider per
  call, by design).
- Signing/broadcast: structurally absent from every surface.
