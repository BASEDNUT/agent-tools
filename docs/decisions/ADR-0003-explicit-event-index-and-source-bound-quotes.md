# ADR-0003 — Local Vault index, explicit direct-pool quote, no broadcast

**Decision:** Extend a source-locked Rootstock read client, not upstream Balancer routing. The event index is SQLite, local and operator-synchronized, with 250-block default chunks, 2,000 maximum block windows and strict `PoolRegistered`/`Swap`/liquidity event decoding. Query time-series lack independent price sources; USD remains null.

**Reasoning:** This gives a usable, auditable base for Orchard without guessing state, creating a hosted service, bypassing wallet controls, or rewriting Rootstock V25 interfaces.

**Security:** Basic MCP/HTTP methods remain read-only. `index sync` is a separate CLI-only local write. `quotes.swap` calls `querySwapSingleTokenExactIn` only for an explicit pool with both tokens verified in Vault, source-pinned Router and amount in raw units. It is not an executable recommendation. Signers and broadcasters do not exist.

**Non-goals:** priced TVL, global complete history, asynchronous subscriptions, multi-route SOR, ELO/Grove composition assignment, auto-trading and x402 payments (user excluded).

**Evidence:** `reference/protocol-abi-provenance.json`; source locks. Tests use local RPC doubles and are not independent live chain tests. Any change to ABI assumptions requires fresh upstream source inspection, test revisions and live read-only verification.
