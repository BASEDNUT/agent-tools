# CLI minimum acceptance gates (proposed)

- Parse/validate flags with deterministic exit codes and JSON response schema.
- `--help`, `--version`, `--output json` behavior in redirected and interactive terminals.
- Timeouts, backoff, chain/RPC mismatch and no-RPC available errors.
- Missing contracts, unknown factory, duplicate token symbol and partial indexer coverage.
- Sensitive value redaction in diagnostics and telemetry.
- Read-only command audit: no `eth_sendRawTransaction`, `eth_sendTransaction`, signing, allowance or wallet import capabilities.
- `doctor` distinguishes `repo_snapshot`, `rpc_verified`, `stale`, `unavailable` rather than combining in one boolean.
- Snapshot/fixtures verify same result via library call and CLI serialization.
- Skill changes feed new failure fixtures back to `rootstock-skill-auditor`.

Reference inspirations: `0xProject/0x-cli` command/exit/error modules, `balancer/b-sdk` `query()` vs `buildCall()` separation, Uniswap composable skills and 1inch domain skill distribution. **Do not copy payment/transaction execution defaults into Rootstock's read-only CLI.**
