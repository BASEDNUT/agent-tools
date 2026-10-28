# Rootstock / Orchard Agent Tools v0.7.1-beta

Standalone Python 3.11+ **read-only toolchain**: CLI, MCP stdio, Python SDK, Node/TypeScript bridge, loopback HTTP API/OpenAPI and **20 bundled Agent Skills**. One tested domain core is shared by all interfaces. Agent payments/x402 are **not included**.

**Independent audit correction (v0.7.1):** Eight additional regressions now cover Keccak rate padding, partial index-rescan coverage, provider-observed reorgs during pool/wallet reads, malformed receipts, and MCP unknown tools. See `docs/INDEPENDENT_AUDIT_V071.md` for evidence and remaining risks. The tests do not establish live-chain correctness.

**Status:** installable and tested offline. Not a fully deployed or production-safe DeFi agent. Critical live-data, pricing, Orchard ELO and independent signing services remain unresolved; no real funds can be spent by this package.

## Quick start

```sh
python3 -m pip install .
rootstock --help
rootstock networks
rootstock capabilities
rootstock skills list
rootstock call registry.abi_catalog
rootstock-mcp                    # MCP stdio, JSON-RPC
rootstock api --port 8765       # GET/API loopback 127.0.0.1 ONLY
```

Rootstock contract resolution uses canonical deployment JSON. On a workstation with internet access:

```sh
rootstock setup registries
rootstock resolve --chain 8453 --name Vault
rootstock resolve --chain 84532 --name Router
```

It verifies exact pinned Git blob content; a fresh install does not automatically download anything. For custom RPC, set `ROOTSTOCK_RPC_BASE` and `ROOTSTOCK_RPC_BASE_SEPOLIA` in a trusted launcher.

## Functional examples

```sh
rootstock rpc status --chain 8453
rootstock pools list --chain 8453 --from-block 52131550 --to-block 52131560
rootstock call pools.inspect --args '{"chain_id":8453,"pool":"YOUR_ACTUAL_POOL_ADDRESS"}'
rootstock call accounts.balances --args '{"chain_id":8453,"wallet":"YOUR_WALLET_ADDRESS","tokens":["YOUR_TOKEN_ADDRESS"]}'
rootstock call registry.abi_selector --args '{"interface":"ERC20","signature":"balanceOf(address)"}'
rootstock call transactions.status --args '{"chain_id":8453,"hash":"YOUR_TRANSACTION_HASH"}'
rootstock index sync --chain 8453 --from-block 52131550 --to-block 52131800
rootstock index follow --chain 8453 --from-block 52131550 --max-polls 1
rootstock call history.events --args '{"chain_id":8453,"limit":20}'
rootstock call watch.cursor --args '{"chain_id":8453,"since_block":52131550,"since_log_index":0}'
```

Inputs marked `YOUR_*` are placeholders, not executable addresses. The index sync/follow writes **only an operator-selected local SQLite file**. It never sends blockchain transactions. Pool quotes require a specific Rootstock pool and pinned Router registry; no smart order routing or signing is supplied.

### Agent configuration

- `config/mcp-servers.example.json`: MCP client launch example
- `config/agent-policy.example.json`: trusted launcher **read-tool allowlist**
- `rootstock skills install --target /path/to/your/agent/skills`: explicitly install the 20 bundled skills
- `schemas/capability-manifest.json`: all CLI/MCP/SDK tool input contracts
- `docs/CONFIGURATION.md`: optional operator-supplied USD price sheets and Orchard eligibility rules
- `docs/CAPABILITY_COVERAGE.md`: verified vs partial vs missing scope
- `docs/SECURITY_BOUNDARIES.md`: permission and custody boundaries
- `docs/VALIDATION.md`: reproducible tests and environment limitations

### Python SDK

```python
from rootstock_tools import Toolchain
kit = Toolchain()  # read-only, no wallets/signing
print(kit.run('capabilities.list'))
print(kit.run('registry.abi_selector', {'interface':'ERC20', 'signature':'balanceOf(address)'}))
```

The TypeScript bridge is in `sdk-ts/`, spawning the **installed** Python CLI without shell interpolation. Example `node --test sdk-ts/index.test.mjs`.

## What changed in v0.7

- Quote membership and router reads pin to a single block; a changing block hash aborts the quote.
- Transaction receipt check verifies its block is still canonical **at that RPC**, reports confirmations, and never claims independent Base finality.
- New `accounts.balances` performs bounded multi-token reads and metadata from one block. Enhanced ERC4626 underlying/rate probe.
- New `analytics.tvl` performs strict decimal arithmetic **only** with an explicit operator price sheet matching the live pool block hash; output cannot masquerade as oracle-verified TVL. No authenticated price feed exists yet.
- New `accounts.eligibility` and `topology.rooted` operate only with **explicit operator configuration**. No fabricated NUT address, canonical Orchard ranking or access grant.
- New `registry.abi_catalog` and `registry.abi_selector` expose a documented partial read-only ABI catalog.
- New `watch.cursor` preserves log-index position within a block; `pools.observe` now finds indexed registration events even when hundreds of swaps follow.
- Four new skills and regression tests, preserving the existing 16.

## Security statement

There is **no signer, broadcast method, wallet private-key handling or permission-escalating operation** in any exposed interface. `eth_call` simulation and unsigned transaction envelopes are NOT approval. MCP tool annotations are not a security boundary. The optional policy file restricts tools in a trusted process, not arbitrary local shell access.

**Excluded by user request:** agent payments, x402 and payment quotes. Do not add these back without a new request.

For limitations, source audits and reverse-engineering queue see `docs/` and `reference/`. Do not modify live Rootstock, Orchard V25, GitHub or hardware based on this development beta.
