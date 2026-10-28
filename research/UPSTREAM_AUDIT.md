# Upstream code inspection — 2026-10-23

Directly inspected through connected GitHub file reads; `git clone` is not available in this environment (DNS/network). These notes distinguish observed source from proposed design. File identifiers are upstream **blob SHA-1** values, not pinned repo commit HEADs.

| Owner / file | Blob SHA-1 | Observed lesson |
| --- | --- | --- |
| `balancer/b-sdk/.agents/skills/changeset/SKILL.md` | `811099fb540d9db0173309a595f9a83c3b3c7cf9` | Specialized release workflow skill: trigger, step-by-step, negative paths, validation, explicit guardrails. **Official developer skill, not universal Balancer trading-agent skills.** |
| `balancer/b-sdk/src/entities/swap/index.ts` | `f7e5490be53f591fc329e2249bb956377bc39b81` | Shared dispatcher handles V2/V3 and separates simulation `query` from `buildCall`; incorrect version-specific parameters rejected. |
| `base/skills/skills/wallet-mcp/plugins/balancer.md` | `bd29bb092067833c1c2006e7bc02d04c9da4afdf` | Base-maintained Balancer agent plugin uses Balancer API, @balancer/sdk and wallet MCP; explicitly **not** Balancer's own official agent service. |
| `Uniswap/uniswap-ai/CLAUDE.md` | `590f9a0cb5ea1f2983bd925de31f0fffef7893b4` | Agent-independent Markdown, skill/plugin versioning and CI skill/eval gates; Nx/monorepo policy is specific to their repo. |
| `Uniswap/uniswap-ai/packages/plugins/uniswap-trading-tools/skills/index-bot/SKILL.md` | `417fbe35c27d7b38287e6ae927051891cacdbac3` | High-level strategy skill declares lower-level prerequisites and delegates rather than rebuilding swaps. |
| `Uniswap/uniswap-ai/packages/plugins/uniswap-driver/skills/swap-planner/SKILL.md` | `7250b173bf9b7e05784b7b118ff2861e0edf8030` | Planner verifies tokens and handles web-discovered untrusted assets explicitly. |
| `1inch/1inch-ai/skills/1inch-mcp-server/SKILL.md` | `9cc9cd6e1d0cf9dc3525a800118b8c815bf714ee` | Small routing hub delegates to narrow domain skills, references and MCP tools. Hosted 1inch MCP service is not the same as code in this repo. |
| `BASEDNUT/rootstock-monorepo/packages/lib/modules/pool/onchain-pool-discovery.ts` | `5aebbc7ce2ac15fb28eab917135287f0c6d29be4` | Vault PoolRegistered discovery, chain-aware classification, unknown factory and analytics `null` handling already exist in Rootstock frontend library. Do **not** reimplement/override before source audit. |
| `BASEDNUT/rootstock-monorepo/deployments/PROVENANCE.md` | `12ab9ae4d828edb82238edcc7558b5eb1a2394b5` | Documented upstream bytecode lineage and limitations. Source assertions were inspected; on-chain proof not independently rerun here. |

Additional source: Agent Skills specification `https://agentskills.io/specification` (required metadata, optional references/scripts, progressive disclosure, `skills-ref validate`).

## Synthesis

1. **Balancer** gives SDK mathematical/transaction separation and engineering release skill discipline, **not** a proven first-party broad agent-skill suite equivalent to Uniswap AI.
2. **Uniswap** gives skill composability, narrow triggers, CI and behavioral evaluations.
3. **1inch** gives skill-to-MCP routing and authentication documentation, but some wallet flows default to `execute: true`; Rootstock must never inherit that default into its read-only skills.
4. **Base** shows how to wrap an SDK/CLI inside an agent platform without conflating the original protocol with the adapter owner.
5. **Rootstock already contains on-chain discovery**; the next step is a source-backed capability adapter and tests, not a duplicate DEX implementation.

## Limitations

The Balancer SDK repository also contains `.claude/skills` but its directory contents were not exhaustively enumerated through the GitHub file endpoint. Claims about the entire set of first-party Balancer skills are therefore intentionally narrow. External skill instructions may be unsafe as operational policy; these examples were only used as design inputs. License review required before incorporating source code.
