# Agent capability completion audit — v0.7

The exposed **34** operations are not a completed 25-domain production infrastructure. Source code + regression tests justify *offline feature existence*, not live correctness, completeness or independent security. Agent payments are excluded.

| Capability family | Implemented now | Missing for production |
|---|---|---|
| Registry / source audit | Local Git-blob-pinned deployment resolution; historical task disambiguation; reviewed partial ABI selectors | Full exact contract artifact ABI; independently verified bytecode provenance and historical versions; online verification |
| RPC / asset metadata | Chain ID/head/code check; ERC20 metadata; ERC4626 `asset()`/`convertToAssets()` probe | Independent provider quorum, authoritative wrapper factory identity and rate provider safety |
| Pools | Bounded Vault registrations, explicit token/balance/fee/rates; registered factory classification from index | Complete live and historical pool metadata, special math/hooks, third-party chain cross-checks |
| Data index | Local SQLite Vault swaps, liquidity, pause/fee/registration events; rescan, coverage intervals and cursor | Fully automated archival service, independent block completeness, operational SLO and reorg guarantees |
| Accounts / Orchard | Single and multi-token balance reads; explicitly configured root threshold/LP qualification | Canonical full-wallet portfolio, deployed membership gate, V25 profile/rank/ELO rules |
| Analytics | Raw-token swap volume/fees, pool activity counts; optional block-matched operator-price TVL arithmetic | Verified historical prices, daily USD volume/TVL, APR, turnover, rankings, ELO |
| Topology | Indexed token hypergraph; operator-configured *provisional* Branch/Graft/Whorl classification | Canonical Grove definitions, nested LP and wrapper recursion, historical topology |
| Monitoring | Foreground read watches, index follow, one-shot poll and log-index cursors | Hosted scheduled high-availability service, notifications and incident response |
| Quotes/simulation | Single specified-pool exact-in `eth_call` read quote, pinned-block evidence; allowlisted target simulations | Audited multi-pool SOR, calldata effect-level analysis, MEV/slippage and gas guarantees |
| Transactions | Unsigned envelope, receipt status, provider-relative canonical header + confirmations | Independent hardware/smart-account signer, approved writes, replay/budgets and full execution recovery |
| Security | Process-bound read allowlist; method schemas; no `eth_send*`, no keys; offline adversarial tests | Authenticated remote principals, independent policy enforcement, signer separation, formal security review |

`accounts.eligibility`, `analytics.tvl` and `topology.rooted` have real implementations but require separately configured inputs. Unknown input returns unavailable or fails closed. A callable tool returning `unavailable` does not satisfy the underlying production requirement.

**Safety:** `transactions.execute` is intentionally absent. No user funds may be moved by the toolkit. This is necessary until genuine independent authorization and signing controls exist. No agent payment/x402 feature is in scope.
