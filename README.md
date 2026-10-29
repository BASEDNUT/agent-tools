# ROOTSTOCK / ORCHARD Agent Tools

**BASED NUT's official agent toolchain** — read + guarded execution — for the ROOTSTOCK DEX and the
Orchard ecosystem on Base (chain 8453) and Base Sepolia (84532).

One tested domain core, five surfaces:

- **CLI**: `rootstock` (JSON in, JSON out)
- **MCP stdio server**: `rootstock-mcp` (37 tools: read by default, execute opt-in)
- **Python SDK**: `rootstock_tools.Toolchain`
- **Node/TypeScript bridge**: `sdk-ts/`
- **Loopback HTTP API + OpenAPI**: `rootstock-api` (127.0.0.1 only)

Plus **20 installable Agent Skills** (`rootstock skills install`).

**Two operating modes, structurally separated:**

- **Default = read-only.** No signer env key set = no signing code reachable.
  The read client cannot broadcast (method allowlist, structural).
- **Opt-in guarded execution.** Set `ROOTSTOCK_SIGNER_KEY` + `ROOTSTOCK_EXECUTE_CHAINS`
  to enable: EIP-1559 signing (key never in any output), chain allowlist,
  router allowlist from the pinned registry, per-tx + daily wei caps,
  mandatory simulate-first, kill switch (`ROOTSTOCK_EXECUTE_KILL=1`).
  `pip install '.[execute]'` for eth-account.

## Install

```sh
python3 -m pip install .            # core runtime is stdlib-only
python3 -m pip install .[tools]     # + audit script deps (pyyaml, jsonschema)
```

## Quick start

```sh
rootstock networks
rootstock setup registries          # explicit, pinned-source download (BASEDNUT/rootstock-monorepo)
rootstock resolve --chain 8453 --name Vault
rootstock capabilities
rootstock skills list
```

Set custom RPC endpoints via `ROOTSTOCK_RPC_BASE` and
`ROOTSTOCK_RPC_BASE_SEPOLIA` (e.g. an archive gateway for deep block ranges —
public endpoints wall archive reads).

## Live-verified examples (BASED NUT deployments, 2026-10-27)

```sh
# All 22 ROOTSTOCK mainnet pools discovered live via Vault PoolRegistered events
ROOTSTOCK_RPC_BASE=https://base.gateway.tenderly.co   rootstock pools list --chain 8453 --from-block 52707735 --to-block 52707830

# Rootstock WETH/BAL Pool on Base Sepolia (block 47265032)
rootstock pools list --chain 84532 --from-block 47265020 --to-block 47265052

# Real pool state: balances, fee, token metadata — no fabricated USD
rootstock call pools.inspect --args '{"chain_id":84532,"pool":"0x1aba4e89fd64e41fe3081fabf6ce33cb613977c7"}'

# Receipt status for the pool-create transaction
rootstock call transactions.status --args '{"chain_id":84532,"hash":"0x8ac424c53e1bd26802d47f7014349c9b19315acd14d8c247ee25d16ea44df4c9"}'

# Multi-token balances (pinned to one block, cross-checked vs raw eth_call oracle)
rootstock call accounts.balances --args '{"chain_id":8453,"wallet":"0x135b208ac2480B0d876944416De16E7a3B9A1F65","tokens":["0xb8de15fb529d98c93c749de63c749d48d25a30df","0xAC130701aa31c284c36609E2489f150F419AD7AD"]}'
```

Full live end-to-end evidence: `docs/E2E_EVIDENCE_2026-10-27.md`.

## Python SDK

```python
from rootstock_tools import Toolchain
kit = Toolchain()
print(kit.run('rpc.get_health', {'chain_id': 8453}))
print(kit.run('registry.resolve_deployment', {'chain_id': 8453, 'name': 'Vault'}))
```

## MCP

```sh
rootstock-mcp   # stdio; 2025-11-25 legacy handshake + 2026-07-28 stateless era
```

## Boundaries

- Read mode signs nothing. Execute mode broadcasts ONLY through the policy
  executor: sim-first mandatory, caps structural, kill switch absolute.
- `eth_call` and unsigned envelopes are not authorization to move funds.
- Payments/x402 features are **excluded by user direction**; do not add them
  back without a new request.
- The optional policy file restricts tools inside a trusted process; it is not
  a sandbox for arbitrary local code.
- The HTTP API binds 127.0.0.1 only and must not be exposed publicly.
- The pinned registry is provenance data. Resolution is not approval.
- Superseded S113-fix deployments (11 addresses) are refused at load and resolve time — hardcoded blocklist + registry `superseded` map enforcement.
  Four contracts superseded by the S113-fix redeployment remain listed
  upstream and must never be used.

## Status

v0.9.0 — read + guarded-execute toolchain, live-proven on Base Sepolia:
zero-value and funded transfers, ERC20 approve, and a real swap on the
Rootstock WETH/BAL pool — all policy-gated, simulated, receipt-verified.
Over-cap and kill-switch refusals live-proven. See
`docs/E2E_EVIDENCE_2026-10-27.md` for the full battery.

## License

MIT — see [LICENSE](LICENSE).

## Contact

BASED NUT — https://basednut.com — security contact in the monorepo
`.well-known/security.txt`.
