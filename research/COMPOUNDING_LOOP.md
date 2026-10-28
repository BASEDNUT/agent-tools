# Compounding skills → CLI → MCP loop

**A single feature, end to end:** rootstock pool discovery.

| Pass | Input | Deliverable | Gate | New learning fed backward |
| --- | --- | --- | --- | --- |
| 0 Source | Rootstock deployment registry, ABI and current code | `rootstock-source-audit` | exact source commit and truth classification | update source precedence for contradictions |
| 1 Domain skill | Rootstock Vault `PoolRegistered` semantics, reorg rules | `rootstock-pool-discovery` | positive, wrong-Vault, unknown-factory and reorg scenario definitions | add edge cases to source skill |
| 2 Core | verified Vault and event reader | deterministic library `discoverPools` | frozen-block replay, no duplicate logs, code identity | update skill and fixtures for discovered provider failures |
| 3 CLI | same library and schemas | `rootstock pools list --chain 8453 --output json` | correct JSON, no wallet, errors, timeouts | update skill and core diagnostics |
| 4 MCP | same library capabilities, not shell string parsing | `list_rootstock_pools` tool (proposed) | same results as library/CLI fixtures, scoped auth | update CLI/skill docs on adapter inconsistencies |
| 5 Evals | user intents and failure prompts | cross-model scenario/evidence report | chain proof, null handling, no writes, no hallucinated addresses | versioned revisions and regression tests |

**Never** proceed merely because metadata validates. A new layer requires contract and behavioral tests appropriate to that layer. This package completes only the source/skill *documentation stage* and offline observation contract fixtures; it does not claim pass 2–5 implementations.

## Change acceptance

Each compounding iteration must include: source pin, exact new capability, owner/authority boundary, negative case, regression suite, rollback pointer and an explanation of why the new functionality belongs in the core rather than another adapter.
