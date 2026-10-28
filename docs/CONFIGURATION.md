# Standalone configuration and data contracts — v0.7

Everything is local to the operator's launcher. No live signing/execution features exist.

## Installation

```bash
python3 -m pip install .
rootstock networks
rootstock call registry.abi_catalog
rootstock skills list
rootstock-mcp
```

The local wheel includes **skills, source and partial read interfaces** but NOT the full deployment registry. For pinned contract lookup run `rootstock setup registries` once on a network-enabled workstation. This rejects mismatching Git blob IDs. After bootstrapping, `rootstock resolve --chain 8453 --name Router` resolves the correct Rootstock deployment. No automatic download occurs.

Use `ROOTSTOCK_RPC_BASE=https://...` and `ROOTSTOCK_RPC_BASE_SEPOLIA=https://...` to select RPC endpoints; prefer your own archive-capable provider for history. `ROOTSTOCK_INDEX_PATH` controls local SQLite storage.

## Optional valuation source — `ROOTSTOCK_PRICE_BOOK`

A trusted operator can supply a JSON document with **precisely** these fields:

```json
{
  "version": 1,
  "chain_id": 8453,
  "block_number": 52131557,
  "block_hash": "REPLACE_WITH_ACTUAL_0x_BLOCK_HASH",
  "source": "describe the independently collected quotation source",
  "prices": [
    {"token": "REPLACE_WITH_REAL_TOKEN_ADDRESS", "usd": "1.2345"}
  ]
}
```

This is a **schema illustration, not a valid price sheet**. Replace all placeholders with independently sourced data; include *every* pool token. Set `ROOTSTOCK_PRICE_BOOK` to its local path **in the trusted process launcher**. `analytics.tvl` requires exact chain, block number, block hash and token match to the live pool snapshot. Missing token decimals or prices produce `value:null`. The result is labeled `derived_from_operator_prices` and `price_source_verified:false`: this feature verifies arithmetic, NOT whether the supplied market price is accurate. No guarantee of real market TVL or investment valuation.

## Optional Orchard rules — `ROOTSTOCK_ORCHARD_CONFIG`

```json
{
  "version": 1,
  "chain_id": 8453,
  "root_asset": "REPLACE_WITH_APPROVED_ROOT_TOKEN_ADDRESS",
  "threshold": "0.01",
  "lp_tokens": ["REPLACE_WITH_APPROVED_LP_TOKEN_ADDRESS"],
  "source": "explicit maintainer review or approved Orchard configuration reference"
}
```

This is **not a usable configuration until the addresses and source are approved**. Root eligibility checks compare a single block's ERC20 balances against the supplied threshold and `lp_tokens` holdings. Results are labeled `derived_from_operator_rules` and `rule_approved_by_project:false`; they confer no actual access rights and cannot change the production Orchard V25. `topology.rooted` produces only tentative Branch/Graft/Whorl classification, not canonical Grove or ELO scores.

## API parity

All read capabilities are exposed by the same `Toolchain.run(name,args)` and automatically appear in `rootstock call`, `rootstock-mcp` tools, `/v1/tools/call`, and Node's CLI bridge. Input schemas are in `schemas/capability-manifest.json`; generated OpenAPI is in `schemas/openapi-readonly.json`. No separate implementation exists in transport adapters.

The HTTP API binds 127.0.0.1 without authentication: **never publish or port-forward it**. The process policy in `config/agent-policy.example.json` controls only an agent launched by a trusted operator. It does not sandbox a malicious shell user.

## Operations still requiring independent services

- Actual historical completeness requires an archival RPC or independently checked indexer; this package performs bounded local scans only.
- Canonical verified USD prices, historical time-aligned token prices, 24h TVL/volume/turnover and authoritative ELO/rank rules are not provided by a static IPFS frontend.
- Write execution requires authenticated identities, a separately protected policy enforcer, calldata/effects verification and an independently secured wallet/signer; no such write path exists here.
- Live-chain RPC integration was blocked in the packaging environment by network DNS; validate against both chains before production use.
