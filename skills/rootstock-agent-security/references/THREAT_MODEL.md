# Agent threat model v0.2 (research; not a formal certification)

Map to OWASP Top 10 for Agentic Applications 2026 (ASI01–ASI10):

| Risk | Local countermeasure | Validation scenario |
| --- | --- | --- |
| ASI01 Goal hijacking | Do not promote retrieved words/tool data to authority | Hostile token metadata says to transfer funds |
| ASI02 Tool misuse | Typed allowlisted operations + trusted effect classifications | `pool.list` tool returns executable shell snippet |
| ASI03 Identity/privilege abuse | Authenticated per-agent identity; never shared admin secrets | Impersonated multisig delegate |
| ASI04 Supply-chain compromise | Pin skill/tool packages; verify authors and hashes | Poisoned SKILL.md / MCP manifest |
| ASI05 Unexpected code execution | Sandbox, no arbitrary shell/JS eval and egress restrictions | `curl | sh` inside task instruction |
| ASI06 Memory/context poisoning | Provenance + quarantined memory; no authority from memory | Cached incorrect Vault address |
| ASI07 Inter-agent messages | Signed/verified work items and least privilege | Agent B asks Agent A to sign |
| ASI08 Cascading failure | Idempotency, rate limits, isolation, circuit breakers | 1 failed RPC causes retries across all pools |
| ASI09 Human–agent trust abuse | Independent approval UI displaying exact payload | Agent mislabels infinite Permit2 approval as read |
| ASI10 Rogue agents | Bounded runtime, revocable credentials and kill switch | Agent modifies its own policy or resubmits tx |

Additional DeFi-specific risks: Oracle/price manipulation, phishing pools, fee-on-transfer/rebasing tokens, precision/decimals, malicious ERC4626 rate providers, stale/reorged logs, failed/slippage simulation, liquidity math divergence, front-run/MEV, permit signature replay, allowance drain, same-ticker token spoofing, compromised RPC, unsafe hooks and dynamic fee changes.

No model-generated report automatically resolves a threat. Evidence requirements: test IDs, pinned sources, reviewed policy diff, logs from separate runtime components and if relevant an independent on-chain read-back.
