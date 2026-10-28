# Source-by-source reverse-engineering backlog

Complete **one bounded investigation at a time**. New evidence alters the ordering; this is not an immutable process.

| Order | Source and investigation | Extraction | Small reproducible acceptance gate |
| --- | --- | --- | --- |
| 01 **COMPLETE (source+CLI slice)** | Rootstock + Balancer SDK 6.2.0 + pnpm patch | Registry identity, SDK router lookup, patch delta, current vs deprecated contracts | Read-only resolver fails closed; 25+ unit/negative tests; next: verify installed patch applied |
| 02 **PARTIAL (SQLite event index + direct-pool quote; no live chain evidence)** | Balancer deployments + Balancer v3 contracts | ABI/event, Vault pool registration, immutable provenance, factory scope | Offline decoder fixtures; known/unknown factory and reorg tests |
| 03 | Uniswap `uniswap-ai` | Skill construction, layered delegation, skill-evals and negative prompts | Security scan + skill-eval examples adapted, no copied business code |
| 04 | 1inch `1inch-ai` | Domain skills, docs vs execution MCP, OAuth, least-privilege | MCP manifest trust tests; no remote execution by default |
| 05 | 0x `0x-cli` + `0x-ai` | Terminal design, machine-readable output, dry-run, errors, documentation-only MCP | Typed JSON CLI errors, stdout vs stderr, no signing |
| 06 | CoW SDK, Jupiter CLI, Morpho, Aave, Safe | Core SDK boundaries, chain differences, smart-account policies | A documented capability-to-evidence trace with no network assumptions |
| 07 | Microsoft AGT / IBM Smith / OWASP / Arx / Leash / AgentLatch / SkillSpector | Policy enforcement, approvals, transaction firewall, supply-chain scanners | Adversarial test corpus + independent runtime mediation design |
| 08 | Orchard V25 data contract (separate project, inspect only) | observation quality, graph entities, tracking, indexing | No synthetic data presented as live; no edits to existing UI |

Every study produces: source lock, inspected code paths, semantic call graph, original assumptions, contradictory evidence, security boundaries, adopt/reject matrix, minimal testable implementation, failure reports, next target. Reuse the same capabilities across core/CLI/MCP/API; adapters must not own duplicate protocol rules.
