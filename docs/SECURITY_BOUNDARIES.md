# Security boundaries, concrete attack surface and unsupported cases

**Release scope:** No signing, wallet key access, value transfer, onchain writes or mutation tools. The toolkit can construct unapproved unsigned requests and perform read-only eth_call simulations, but does not authorize or broadcast them. The security skill is procedural; enforcement here is structural removal of all write APIs, typed arguments, chain-specific Vault selection, frozen source verification and guarded RPC methods.

## Trust boundaries

- **Repo data:** Canonical JSON registries are downloaded only on explicit `rootstock setup registries`, compared byte-for-byte to observed Git blob hashes from the pinned Rootstock revision. A Git blob checksum proves source bytes matched a reviewed snapshot, **not** deployment authenticity, chain state, or external audit.
- **Superseded deployments:** 11 S113-fix addresses (upstream owners / zero sequencer feed) are hardcoded-blocked: any registry that lists one fails to load; registry-declared `superseded` entries are refused at resolve time; the guard is independent of the blob pin and active under `--allow-unpinned` too.
- **RPC:** operator-owned endpoint; network readbacks must match the requested chain ID and conform to JSON-RPC. Treat the provider's event data as evidence *from that provider*, not as independently verified block completeness. An HTTP redirect is never followed. URL paths and tokens are not exposed in status responses.
- **MCP:** arbitrary agent-provided tool name/parameters are untrusted and constrained by one allowlist. Transaction prepare/simulate/status are read-only; no signer, transaction broadcast or local file mutation tool. Descriptions/annotations are not access tokens. Stdout uses newline-delimited JSON-RPC. No arbitrary filesystem, arbitrary RPC, signer, wallet or shell methods.
- **CLI:** skill installation, registry bootstrapping and SQLite event sync write **only** local files upon an explicit operator command. `watch` is foreground-only. They cannot change Rootstock or Orchard code, GitHub branches or chain state.
- **HTTP:** 127.0.0.1 only, GET-only, no remote auth; do not port-forward or publicly expose. This is for local development.
- **Python SDK:** direct imports run with the caller's local OS privileges; this library intentionally does not sandbox arbitrary Python code.

## Unaddressed security controls (must precede write support)

Authenticated caller identity; signed/scoped capabilities; durable ledger for concurrent budgets; independent quote & calldata validation; ABI-based call graph and permit approvals; allowlisted targets/selectors/chain/asset; replay and deadline protection; block pinning/finality and reorg handling; vault-level wallet limitations; independent hardware/smart-account signer; operator approval; rate limiting, tamper-evident logs and monitoring; formal contract audits.

## Negative tests

Wrong chain, unsupported method, malicious client-supplied RPC args, opaque target, invalid event topics and emitter, reorg-removed events, unbounded scan window, false historical factory inference, unknown tool, invalid metadata, fake registry, changed source lock, and attempts to invoke transaction operations.

**Limitations:** Direct fake-RPC tests are not real mainnet tests; HTTP/MCP surface-level tests are not a substitute for formal third-party client conformance/security review.

## Additional v0.7 trusted inputs and constraints

- Operator **price sheets** and **Orchard rules** are configured by environment/constructor only, not by untrusted agent request arguments. The package validates input shape, address/chain, block/hash, duplicate keys and numeric finiteness; it does NOT cryptographically authenticate external prices or approve production eligibility.
- The new signature selector catalog is deliberately read-only and incomplete. A selector or ABI hit is not a transaction approval.
- `accounts.balances` rejects duplicate addresses and is limited to 32 assets. It never claims exhaustive wallet discovery.
- `watch.cursor` tracks block + log index, but only for indexed records. It cannot fill gaps or attest chain finality.
- `transactions.status` checks the provider's current header; Base L2 safe/finalized/L1 settlement remain unverified.
- Quote data is fixed to one block and the header is checked again at the end. RPC provider integrity and economic price fairness remain outside this guarantee.
