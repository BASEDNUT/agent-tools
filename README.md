# ROOTSTOCK / ORCHARD Agent Tools

**BASED NUT's official read-only agent toolchain** for the ROOTSTOCK DEX and the
Orchard ecosystem on Base (chain 8453) and Base Sepolia (84532).

One tested domain core, five surfaces:

- **CLI**: `rootstock` (JSON in, JSON out)
- **MCP stdio server**: `rootstock-mcp` (34 read-only tools)
- **Python SDK**: `rootstock_tools.Toolchain`
- **Node/TypeScript bridge**: `sdk-ts/`
- **Loopback HTTP API + OpenAPI**: `rootstock-api` (127.0.0.1 only)

Plus **20 installable Agent Skills** (`rootstock skills install`).

This is a **read-only toolkit**: no signer, no wallet keys, no broadcast, no
transaction execution path exists anywhere in the package. That is structural,
not a policy setting.

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

## Boundaries (unchanged and deliberate)

- No transaction signing, broadcast, or approval. `eth_call` and unsigned
  envelopes are not authorization to move funds.
- Payments/x402 features are **excluded by user direction**; do not add them
  back without a new request.
- The optional policy file restricts tools inside a trusted process; it is not
  a sandbox for arbitrary local code.
- The HTTP API binds 127.0.0.1 only and must not be exposed publicly.
- The pinned registry is provenance data. Resolution is not approval.
  Four contracts superseded by the S113-fix redeployment remain listed
  upstream and must never be used.

## Status

v0.8.0 — live-chain end-to-end verified on Base mainnet and Base Sepolia
against BASED NUT production deployments (see evidence doc). Still a
read-only toolkit by design: live-data pricing, Orchard ELO, and any signing
service remain out of scope here.

## License

MIT — see [LICENSE](LICENSE).

## Contact

BASED NUT — https://basednut.com — security contact in the monorepo
`.well-known/security.txt`.
