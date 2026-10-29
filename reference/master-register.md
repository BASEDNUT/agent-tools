# Rootstock / Orchard — Master research register

Snapshot: 2026-10-23. Source map and proposed investigation plan; not a code or security audit certification.

**96 unique URLs · 23 security research targets · 25 candidate capabilities · 6 skills.**

## Conversation chronology

- **01  Reconstruct context:** Located Based Nut Rootstock monorepo and active Orchard Terminal V25 research candidate. Rootstock is the DeFi execution engine; Orchard is its independent data, analytics, topology and account interpretation layer. Peanutoshi was identified as an intended agent, not a deployed universal agent service.
- **02  Research agent-facing DeFi:** Compared official 1inch hosted MCP, Uniswap AI skills, 0x CLI + skills, Aave/Morpho MCP, Jupiter, LI.FI, CoW and Balancer SDK. Separated first-party tools from third-party/community wrappers.
- **03  Inventory everything needed:** Enumerated RPC, ABIs, indexers, analytics, schemas, API, SDK, CLI, MCP, skills, agent runtime, wallet/policy, documentation, event streams, audits and operations. Produced a 25-operation proposal and source-backed architecture.
- **04  Source audit and workspace:** Inspected pinned upstream GitHub READMEs, package manifests, CLI entry points, SDK modules, agent skill files and Rootstock discovery code. Retained verified source-file snapshots, source pins and a script for fuller checkouts. Full upstream checkouts were not claimed.
- **05  Define compounding development loop:** Skills help design core tools and CLI; shared CLI/service capabilities become MCP/API adapters; fixture tests and audits feed fixes into skills and specifications. Avoid duplicating financial logic across interfaces.
- **06  Build first skill foundation v0.1:** Produced five Agent Skills: rootstock-source-audit, rootstock-pool-discovery, orchard-data-integrity, rootstock-cli-engineering, rootstock-skill-auditor. Added source precedence, observation schema and offline structural tests.
- **07  Research security and release v0.2:** Studied OWASP, Microsoft, IBM Smith, OPA, Trail of Bits, Base wallet, LangGraph and Safe. Added rootstock-agent-security with checklists, read-only demonstration policy and adversarial offline fixtures. No production permission gate exists yet.
- **08  Search hackathons deeper:** Cataloged 23 hackathon/open-source security efforts covering transaction firewalls, EIP-7702 wallets, signed intent, shared budgets, nonces, receipts, sandboxed skills/MCP, cryptographic attestations and shutdown. Inspected select repository files and documented self-reported gaps.
- **09  Present phase — consolidate and reverse engineer:** Create a complete link and decision register, then investigate each target sequentially, extracting validated, licensed, tested design patterns into the Rootstock/Orchard toolchain.

## Compounding loop

Source audit → skill → core capability → CLI → MCP/API → tests + adversarial evals → improve skill and core.

## Tools and component vocabulary

- **Skill:** Portable agent guidance (SKILL.md, references, tests). Teaches behavior; cannot enforce permissions by itself.
- **ABI:** Smart-contract interface describing functions, events and errors. Must match deployment and chain.
- **RPC:** JSON-RPC interface to node data, calls, logs and broadcasts; verify chain, block and provider.
- **Indexer:** Reconstructs event history and reorg-aware state; requires checkpoints and source provenance.
- **Canonical registry:** Versioned addresses/code hashes/chain settings. Prevents confusing Rootstock with Balancer.
- **Core domain library:** Shared implementation of identities, math, validation, source state and algorithms.
- **API:** Network contract (usually REST/GraphQL) for external tools and applications.
- **SDK:** Typed client wrapping the shared contracts, errors and SDK/provider abstractions.
- **CLI:** Shell commands with stable JSON/exit codes; thin adapter to core capabilities.
- **MCP:** Tool/resource interface for compatible agent clients; thin adapter and not a security boundary.
- **Agent runtime:** Planner/tool-selection/orchestrator/task-state and memory; separate from deterministic tools.
- **Policy decision point:** Evaluates signed/verified principal, scopes, intended effect and evidence against explicit rules.
- **Policy enforcement point:** Unavoidable, independent executor boundary that blocks denied calls and cannot be bypassed by agents.
- **Signing boundary:** Independent signer/wallet/on-chain execution constraints; never store keys inside an LLM prompt.
- **Simulation:** Executes hypothetical transaction on snapshot/fork and analyzes state effects; no signing.
- **Intent / delegation:** Human-approved parameters bound to exact transactions, chain, tokens, limits, time and nonce.
- **Approval workflow:** Human review of exact payload, not a vague "I approve" message; revalidate at execution.
- **Agent evaluation:** Test expected agent reasoning/tool selection against normal and adversarial prompts.
- **Provenance:** Links data and decisions to original sources, versions, blocks, methods and timestamps.
- **Observability / audit:** Reliable logs, receipts, run traces, incident detection, revocation and replay.
- **Service metering:** Optional x402/ACP payments, quotas and economic accounting, deferred until needed.

## Existing artifacts

- **Toolchain research:** `/projects/BASEDNUT/artifacts/rootstock-agent-toolchain-research-2026-10-23.zip`
- **Skills v0.1:** `/projects/BASEDNUT/artifacts/rootstock-orchard-skills-foundation-v0.1-2026-10-23.zip`
- **Skills v0.2:** `/projects/BASEDNUT/artifacts/rootstock-orchard-skills-foundation-v0.2-security-2026-10-23.zip`
- **Hackathon research:** `/projects/BASEDNUT/artifacts/rootstock-orchard-security-hackathon-research-2026-10-23.zip`

## Candidate capability inventory (not implemented)

- **P0 / read — `registry.list_networks`**: List supported chain IDs and registry provenance
- **P0 / read — `registry.resolve_deployment`**: Return canonical deployed addresses and ABIs for chain/block
- **P0 / read — `rpc.get_health`**: Probe provider availability and observed head with chain ID
- **P0 / read — `assets.lookup`**: Resolve addresses, symbols, decimals and factory evidence
- **P0 / read — `assets.wrapper_underlying`**: Resolve wrapper and rate relationships
- **P0 / read — `pools.list`**: Discover pools via verified Vault registrations
- **P0 / read — `pools.inspect`**: Read Vault, tokens, fees, weights, hooks at one block
- **P0 / read — `pools.observe`**: Provide block-pinned source-qualified metrics or explicit null
- **P0 / read — `history.events`**: Get registered normalized chain events with block provenance
- **P0 / read — `observations.status`**: Return coverage, staleness, synthetic/partial/unavailable
- **P1 / read — `topology.explore`**: Explore Branch/Graft/Whorl/Tree/Grove graph
- **P1 / read — `accounts.positions`**: Summarize verified wallet LP positions and event history
- **P1 / read — `accounts.eligibility`**: Calculate policy eligibility at a stated block
- **P1 / read — `analytics.tvl`**: Produce TVL with rate and price provenance
- **P1 / read — `analytics.volume_fees`**: Report index-validated volume and fee breakdown
- **P1 / read — `analytics.turnover`**: Compute Liquidity Turnover and related Orchard measures
- **P1 / read — `analytics.rankings`**: Evaluate ranking rules on indexed history with method version
- **P1 / read — `watch.subscribe`**: Establish indexed event/alert subscriptions (server-side)
- **P2 / read — `quotes.swap`**: Quote using verified routers or quote services; no sign
- **P2 / simulate — `transactions.simulate`**: Simulate proposed action with slippage/gas/hook effects
- **P2 / prepare — `transactions.prepare`**: Return typed unsigned calldata and approval inventory
- **P2 / read — `policy.evaluate`**: Check permission scopes, spending/contract limits
- **P2 / read — `transactions.status`**: Track transaction receipt and confirmation without signing
- **P3 / submit — `transactions.execute`**: Execute only via separate independently authorized signer
- **P3 / read — `payments.quote`**: Optional service billing/x402 or ACP contract

## Security threats

- **Hostile skill or MCP tool:** Pin/scan/sandbox instructions and code before installation; operator must approve trust changes.
- **Agent privilege escalation:** Trusted policy store and identity; agent cannot expand its permissions or approve itself.
- **CLI/SDK bypassing policy:** Deny in executor and signer, not just MCP wrapper; direct-call negative tests.
- **Wrong chain or Balancer Vault:** Resolve Rootstock chainId/Vault/pool/contract addresses and verify against code hash.
- **Token spoofing/decimal confusion:** Verify contract address, decimals, underlying wrapper/rate, chain; unknown means halt.
- **Value underreporting:** Inspect actual call bytes, transfers and approvals; do not trust agent-supplied USD estimate.
- **Unlimited approvals:** Treat ERC20/Permit2 allowances as delegated financial authority and cap independently.
- **Nested multicall/hook surprises:** Allowlist destinations/selectors and examine downstream simulated effects.
- **Prompt injection / poisoned tool output:** Keep retrieved text as untrusted data; do not let it alter policy.
- **Stale quotes / RPC divergence:** Block-pin observations, compare providers, reject stale or inconsistent evidence.
- **Concurrent overspend:** One shared budget per funding vault, atomic reservations and transaction reconciliation.
- **Approval payload switch:** Cryptographically bind approval to exact call bytes, policy version, nonce and expiry.
- **Retried/pending transactions:** Idempotency IDs and chain reconciliation; never resend blindly after unknown status.
- **Tampered audit trail:** Append-only or independently verifiable decision/settlement evidence.
- **Emergency incidents:** Independent pause/revoke/rotate; security agent may tighten but not unpause itself.

## Reverse-engineering waves

- **Wave 0: Rootstock source + Balancer SDK and deployments.** Audit canonical Rootstock Vault/factory/router identities, math, event scanning, code provenance and existing tests. **Capture:** Skill: source-audit + pool-discovery; output: pinned source map and read-only fixtures.
- **Wave 1: Uniswap AI skills and evaluations.** Examine progressive disclosure, prerequisites, modular skills, agent-agnostic packaging, regressions. **Capture:** Skill authoring rubric + activation/eval scenarios.
- **Wave 1: 1inch AI skills + hosted MCP contract.** Understand auth, tool catalog, hosted vs published code boundary, domain references and secure signing defaults. **Capture:** Skill/MCP boundary notes and expected tool contracts.
- **Wave 1: 0x AI + 0x CLI.** Study JSON envelopes, schema in help, errors, dry-run, config separation, signing and payments. **Capture:** CLI specification and local contract/JSON fixtures.
- **Wave 1: CoW SDK / Morpho / Aave / Jupiter.** Compare signer separation, adapter packages, unsigned transaction lifecycle and generated interfaces. **Capture:** Adapter standard, transaction states and typed schemas.
- **Wave 1: NVIDIA SkillSpector + IBM Smith + OPA / Microsoft AGT.** Inspect static skill scanning, policy authoring, deterministic enforcement, negative tests and host interception. **Capture:** Trusted supply-chain gate and policy test harness (no live authority).
- **Wave 2: Arx + Evzi + AgentLatch.** Deep-compare intent binding, calldata semantics, shared policy rules, signed approval and replay protection. **Capture:** Threat fixtures for Rootstock calldata, wallet scope and nonce/TTL.
- **Wave 2: Leash + intentOS + Swish + Settle.** Shared treasury budgets, EIP-7702 policies, proof objects, independent receipts and revocation. **Capture:** Wallet/treasury control design, no prototype code copied blind.
- **Wave 2: Clembot + Skill Auditor + 0G SkillGate + SkillFortify.** Preinstall skill/MCP trust gate, sandbox behavioral scans, signed manifests/lockfiles and exceptions. **Capture:** Skills/MCP provenance policy and scanning gates.
- **Wave 2: Dune + Graph + Envio + DefiLlama.** Index event provenance, freshness, completeness, TVL/fees/liquidity and multi-venue comparisons. **Capture:** Observation schema and indexer acceptance fixtures.
- **Wave 3: Remaining hackathon prototypes (23 catalog).** Triage showcase-only versus tested source, identify novel mechanisms, fill best-practice gaps. **Capture:** Individual audit cards, accepted/rejected patterns, updated tests.

## Hackathon and security target register

### Arx

Origin: ETHOnline 2026 | Depth: source-file-inspected

Mechanism: Policy engine, nonce/replay checks, calldata/value binding, signer boundary, 14 adversarial scenario claims

Caveat: self-reported tests; not rerun

Showcase/source: https://ethglobal.com/showcase/arx-z0ekp

Repository: https://github.com/YagnaRDK/Arx

### Evzi

Origin: ETHOnline 2026 | Depth: source-file-inspected

Mechanism: Human-signed immutable intent, constraint verification, calldata decoding, chain-state comparisons

Caveat: not independently executed

Showcase/source: https://ethglobal.com/showcase/evzi-g0yvy

Repository: https://github.com/EvgenyNasretdinov/evzi

### DSAP / AgentLatch

Origin: ETHGlobal Tokyo 2026 | Depth: source-file-inspected

Mechanism: ENS-stored policy, ALLOW/BLOCK/HUMAN_APPROVAL, fresh owner confirmation, MCP integration

Caveat: v4 hook prototype distinct from live v3 agent swap route

Showcase/source: https://ethglobal.com/showcase/dsap-protocol-87152

Repository: https://github.com/prathamesh-mutkure/agent-latch

### Leash

Origin: ETHOnline 2026 | Depth: repository-inspected

Mechanism: Shared budget keyed by ENS identity/token/period; chain refusal; revoke/tighten

Caveat: README discloses some policy approval/name issuance paths use MockAttester

Showcase/source: https://ethglobal.com/showcase/leash-q21er

Repository: https://github.com/ksin751119/leash

### Swish

Origin: ETHGlobal Tokyo 2026 | Depth: repository-inspected

Mechanism: Compare simulated effects to declaration; Move proof objects consumed upon spend; scoped vaults

Caveat: Sui testnet only; EVM translation requires new design

Showcase/source: https://ethglobal.com/showcase/swish-0vft8

Repository: https://github.com/Khalid-000-ME/swish

### intentOS

Origin: ETHGlobal New York 2026 | Depth: repository-inspected

Mechanism: Signed typed ExecutionRequest, hard contract limits, Watcher may freeze/tighten, no LLM custody

Caveat: MVP single-pair Base mainnet, self-reported

Showcase/source: https://ethglobal.com/showcase/intentos-3m9gp

Repository: https://github.com/rtree/2026NYC-ethglobal

### Mandate Agents

Origin: ETHOnline 2026 | Depth: showcase-only

Mechanism: Deterministic adapters, smart-account cap/allowlist/replay, Ledger approval

Caveat: author claims not source audited

Showcase/source: https://ethglobal.com/showcase/mandate-agents-wxnex

### StableCoinManager

Origin: ETHGlobal Tokyo 2026 | Depth: showcase+repo-link

Mechanism: Code-enforced allowance, payee/network pin, no duplicate signatures upon retries, settlement receipt

Caveat: company system plus hackathon extension

Showcase/source: https://ethglobal.com/showcase/stablecoinmanager-8z1et

Repository: https://github.com/elsoul/stablecoinmanager

### Settle

Origin: Solana Frontier Hackathon 2026 | Depth: repository-inspected

Mechanism: Atomic policy checks, capability pin, receipts with hash verifier, 3 SDK runtimes

Caveat: devnet; mainnet planned after audit

Showcase/source: https://github.com/Pratiikpy/Settle

Repository: https://github.com/Pratiikpy/Settle

### Guardrail Alpha

Origin: BNB CMC/Trust Wallet hackathon | Depth: repository-inspected

Mechanism: Rust risk engine between strategy and TWAK signer; offline paper mode, event log

Caveat: description self-reported; not independently tested

Showcase/source: https://github.com/caelum0x/guardrail

Repository: https://github.com/caelum0x/guardrail

### Verified Execution Agent

Origin: OKX.AI Genesis hackathon | Depth: repository-inspected

Mechanism: Decodes calldata/approvals; signed PASS/BLOCK receipts and post-trade attestation

Caveat: verification service alone is not a mandatory signer gate

Showcase/source: https://github.com/alicesparkai/verified-execution-agent

Repository: https://github.com/alicesparkai/verified-execution-agent

### Skill Auditor

Origin: ETHGlobal Cannes 2026 | Depth: showcase+repo-link

Mechanism: Semantic analysis, sandbox execution, skill audit report hash

Caveat: model judge fallible; sandbox fidelity unverified

Showcase/source: https://ethglobal.com/showcase/skill-auditor-44oie

Repository: https://github.com/Arttribute/skillauditor

### Clembot Doorman

Origin: ETHOnline 2026 | Depth: repository-inspected

Mechanism: Local MCP tool gate, two-stage vetting, pinned recipe, harness A/B test

Caveat: hooks must be mandatory in each chosen runtime; model attacks still possible

Showcase/source: https://ethglobal.com/showcase/clembot-doorman-mw4pd

Repository: https://github.com/clemenswan/clembot-doorman

### 0G SkillGate

Origin: Open Agents 2026 | Depth: showcase-only

Mechanism: Deterministic static scan, optional model reviewer, hash registry

Caveat: scan does not prove runtime safety

Showcase/source: https://ethglobal.com/showcase/0g-skillgate-xja63

### NVIDIA SkillSpector

Origin: Open source (not hackathon) | Depth: repository+docs-inspected

Mechanism: Skill, MCP config and archive scanning; CLI and optional MCP integration

Caveat: scanner verdict advisory and not complete proof of safety

Showcase/source: https://github.com/NVIDIA/SkillSpector

Repository: https://github.com/NVIDIA/SkillSpector

### SkillFortify

Origin: Open source research (not hackathon) | Depth: documentation-inspected

Mechanism: Dependency graphs, skill lockfiles, SBOM, static capability checks

Caveat: formal-model guarantees limited to model assumptions

Showcase/source: https://github.com/qualixar/skillfortify

Repository: https://github.com/qualixar/skillfortify

### Harness

Origin: ETHOnline 2026 | Depth: repository-inspected

Mechanism: Container isolation, hardware signer, ENS identity, revocation

Caveat: self-reported demos and guarantees

Showcase/source: https://ethglobal.com/showcase/harness-vvvaq

Repository: https://github.com/LeoFranklin015/Harness

### StableSettle

Origin: ETHGlobal New York 2026 | Depth: showcase-only

Mechanism: single Solidity spend gate, multi-limit policy, 6-tool MCP

Caveat: self-reported Foundry coverage

Showcase/source: https://ethglobal.com/showcase/stablesettle-iw6kh

### Aegis402

Origin: Open Agents 2026 | Depth: showcase+repo-link

Mechanism: Pre-audit hook scrutiny, post-audit realized effects/MEV signals

Caveat: LLM judgement not a hard authorizer

Showcase/source: https://ethglobal.com/showcase/aegis402-o8x6z

Repository: https://github.com/AEGIS402/post-audit

### HumanSign

Origin: ETHGlobal New York 2026 | Depth: showcase-only

Mechanism: owner approval recorded onchain, per-payment/daily caps, MCP tool

Caveat: not independently run

Showcase/source: https://ethglobal.com/showcase/humansign-ad6j1

### xPayables

Origin: ETHGlobal New York 2026 | Depth: showcase-only

Mechanism: Ledger-signed vendor and budget rules, idempotent settlement state

Caveat: self-reported tests

Showcase/source: https://ethglobal.com/showcase/xpayables-h9950

### Solana Guard

Origin: Colosseum Frontier Hackathon 2026 | Depth: repository-inspected

Mechanism: Anchor register_agent/set_policy/validate_and_execute/toggle_agent structure

Caveat: repository roadmap still lists SDK/dashboard/demo as coming soon

Showcase/source: https://github.com/abhigyan1102/solana-guard

Repository: https://github.com/abhigyan1102/solana-guard

### Skill Constellations

Origin: Research 2026-10-08 | Depth: research-paper

Mechanism: Measured skill copying and low propagation of upstream security fixes

Caveat: empirical results, not a product

Showcase/source: https://arxiv.org/abs/2610.11169

## Full URL index

### Protocol, project and code sources (30)

- **L001 — 0x AI skill repository** (P0): https://github.com/0xProject/0x-ai — Agent API and x402 payment skills [commit 0167bbb411cc972b966127d23c23de801061fa99]
- **L002 — 0x CLI docs** (P0): https://docs.0x.org/docs/introduction/develop-with-ai/0x-cli — CLI behavior, install and execution guidance
- **L003 — 0x CLI repository** (P0): https://github.com/0xProject/0x-cli — JSON output, errors, simulation, wallet separation [commit fc86b4db986bfede5684e7810eae0ff11cbca05d]
- **L004 — 1inch AI distribution** (P0): https://github.com/1inch/1inch-ai — Hosted MCP config, skills, auth docs [commit 11126423d43d5d67c378ac80450850f5536e2b34]
- **L005 — 1inch MCP documentation** (P0): https://business.1inch.com/portal/documentation/ai-integration/mcp-server — Official tool descriptions and authentication
- **L006 — Balancer deployments** (P0): https://github.com/balancer/balancer-deployments — Official deployment artifacts for provenance comparisons
- **L007 — Balancer SDK developer documentation** (P0): https://docs-v3.balancer.fi/developer-reference/sdk/ — SDK integration patterns
- **L008 — Balancer SDK repository** (P0): https://github.com/balancer/b-sdk — Balancer protocol math and swap/LP SDK; includes changeset skill
- **L009 — Balancer v3 monorepo** (P0): https://github.com/balancer/balancer-v3-monorepo — Upstream contract architecture; verify provenance
- **L010 — Base wallet agent skills** (P0): https://github.com/base/skills — Official Base Wallet MCP skills and protocol integrations
- **L011 — Base Wallet MCP plugin Balancer** (P0): https://github.com/base/skills/blob/main/skills/wallet-mcp/plugins/balancer.md — Balancer community integration maintained by Base, not Balancer
- **L012 — BASED NUT — primitives** (P0): https://github.com/BASEDNUT/sol-contracts — TokenFactory and WrapperFactory source
- **L013 — BASED NUT — Rootstock monorepo** (P0): https://github.com/BASEDNUT/rootstock-monorepo — Canonical project code; inspect deployments, ABIs, event scanning [commit 6206c91643e2e87c43164be90f963c91a11329ab — S113-fix registry sync: superseded never-use map live]
- **L014 — Orchard application** (P0): https://orchard.basednut.com — Orchard user-facing interpretation layer; V25 under development
- **L015 — Rootstock documentation** (P0): https://docs.basednut.com/rootstock — Canonical product documentation
- **L016 — Uniswap AI developer overview** (P0): https://developers.uniswap.org/docs/uniswap-ai/overview — Official AI integration guidance
- **L017 — Uniswap AI skill repository** (P0): https://github.com/Uniswap/uniswap-ai — Domain-specific skills, evaluation suites and plugin architecture [commit 1a43e968a39537d5a73aeca20dd1ed9d96f502fa]
- **L018 — 0x documentation MCP** (P1): https://docs.0x.org/_mcp/server — Documentation MCP endpoint, not transactional service
- **L019 — 1inch AI integration index** (P1): https://business.1inch.com/portal/documentation/ai-integration — General 1inch agent tool setup
- **L020 — 1inch AI Skills** (P1): https://business.1inch.com/portal/documentation/ai-integration/ai-skills — Domain skill definitions
- **L021 — 1inch hosted MCP endpoint** (P1): https://api.1inch.com/mcp/protocol — Remote MCP server endpoint, not a cloned codebase
- **L022 — 1inch machine-readable docs** (P1): https://business.1inch.com/portal/llms.txt — Machine-readable API/docs discovery
- **L023 — Aave official MCP docs** (P1): https://www.aave.com/docs/mcp — Discover, inspect, simulate, build, sign transaction pattern
- **L024 — Balancer frontend monorepo** (P1): https://github.com/balancer/frontend-monorepo — Reference to upstream frontend conventions
- **L025 — Base Wallet MCP setup** (P1): https://docs.cdp.coinbase.com/ai-agents/coinbase-for-agents/wallet-mcp#quickstart — Wallet MCP security and per-protocol plugins
- **L026 — CoW SDK monorepo** (P1): https://github.com/cowprotocol/cow-sdk — SDK module boundaries, orders, signing and provider adapters [commit 2aa89cebb1088928b9aebb0e9b563a034d859c4e]
- **L027 — Jupiter CLI repository** (P1): https://github.com/jup-ag/cli — Agent CLI and JSON output; Solana/GPL code, use as design reference [commit d8d7386691535469f7d17705ebfc5f432b96feba]
- **L028 — Morpho official MCP docs** (P1): https://docs.morpho.org/developers/agents/mcp/ — OpenAPI-derived typed tools and unsigned transactions
- **L029 — Rootstock application** (P1): https://root.basednut.com — Current DeFi interface, not agent server
- **L030 — BASED NUT project site** (P2): https://basednut.com — Ecosystem orientation

### Indexing, analytics, interoperability and economics (11)

- **L031 — Agent Skills specification** (P0): https://agentskills.io/specification — Skill packaging and progressive disclosure
- **L032 — JSON Schema 2020-12** (P0): https://json-schema.org/draft/2020-12/schema — Formal data contracts for tool operations
- **L033 — MCP official website** (P0): https://modelcontextprotocol.io/ — Agent tool/resource protocol
- **L034 — Dune MCP overview** (P1): https://dune.com/blog/dune-mcp — Blockchain SQL analytics accessible to agents
- **L035 — Envio documentation** (P1): https://docs.envio.dev/ — EVM indexing and event normalization
- **L036 — MCP server metadata schema** (P1): https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json — Schema used in the inspected 1inch MCP registry manifest
- **L037 — MCP tool annotations article** (P1): https://blog.modelcontextprotocol.io/posts/2026-03-16-tool-annotations/ — Security metadata is descriptive, not enforcement
- **L038 — The Graph — Subgraph MCP** (P1): https://thegraph.com/docs/en/subgraphs/tooling/subgraph-mcp/introduction/ — Indexed chain data and query schema discovery
- **L039 — Uniswap universal-router / SDK overview** (P1): https://developers.uniswap.org/ — Protocol developer source; see Uniswap AI for exact skills
- **L040 — DefiLlama MCP** (P2): https://investors.defillama.com/mcp — TVL, protocol and financial comparative analytics
- **L041 — x402 reference** (P2): https://www.x402.org/ — Potential machine-to-machine paid API pattern; optional later

### Policy engines, security research and controls (12)

- **L042 — IBM Smith** (P0): https://github.com/IBM/smith — Skills producing OPA policies, tests, feedback/refinement loop
- **L043 — Microsoft Agent Governance Toolkit** (P0): https://github.com/microsoft/agent-governance-toolkit — Policy enforcement, audit and agent identity
- **L044 — NVIDIA SkillSpector** (P0): https://github.com/NVIDIA/SkillSpector — Skill scanner CLI/MCP for injection, exfiltration and permissions [commit d7338f58200a9ae2a24810cee08911ab68b107a7]
- **L045 — Open Policy Agent** (P0): https://github.com/open-policy-agent/opa — Deterministic policy decision point
- **L046 — OWASP Agent Control Standard** (P0): https://genai.owasp.org/resource/agent-control-standard-acs/ — Explicit interception and agent authority rules
- **L047 — OWASP Agentic AI Top 10 (2026)** (P0): https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/ — Agent threat taxonomy
- **L048 — LangChain human in the loop** (P1): https://docs.langchain.com/oss/python/langchain/human-in-the-loop — Pause, review and resume of agent actions
- **L049 — OpenAI Agents SDK guardrails/approvals** (P1): https://developers.openai.com/api/docs/guides/agents/guardrails-approvals — Approval interrupts and guardrails
- **L050 — Safe spending limits** (P1): https://help.safe.global/articles/3961440620-set-up-and-use-spending-limits — Token amount caps; not recipient policy
- **L051 — SkillFortify** (P1): https://github.com/qualixar/skillfortify — Skill dependency/lockfile/SBOM security
- **L052 — Trail of Bits security skills** (P1): https://github.com/trailofbits/skills — Structured auditing and security workflows
- **L053 — Agent Skill Constellations paper** (P2): https://arxiv.org/abs/2610.11169 — Research on agent configuration/skill ecosystem safety

### Hackathon showcases and competition entries (16)

- **L054 — Arx — showcase / submission** (P1): https://ethglobal.com/showcase/arx-z0ekp — Policy engine, nonce/replay checks, calldata/value binding, signer boundary, 14 adversarial scenario claims
- **L055 — Clembot Doorman — showcase / submission** (P1): https://ethglobal.com/showcase/clembot-doorman-mw4pd — Local MCP tool gate, two-stage vetting, pinned recipe, harness A/B test
- **L056 — DSAP / AgentLatch — showcase / submission** (P1): https://ethglobal.com/showcase/dsap-protocol-87152 — ENS-stored policy, ALLOW/BLOCK/HUMAN_APPROVAL, fresh owner confirmation, MCP integration
- **L057 — Evzi — showcase / submission** (P1): https://ethglobal.com/showcase/evzi-g0yvy — Human-signed immutable intent, constraint verification, calldata decoding, chain-state comparisons
- **L058 — Harness — showcase / submission** (P1): https://ethglobal.com/showcase/harness-vvvaq — Container isolation, hardware signer, ENS identity, revocation
- **L059 — intentOS — showcase / submission** (P1): https://ethglobal.com/showcase/intentos-3m9gp — Signed typed ExecutionRequest, hard contract limits, Watcher may freeze/tighten, no LLM custody
- **L060 — Leash — showcase / submission** (P1): https://ethglobal.com/showcase/leash-q21er — Shared budget keyed by ENS identity/token/period; chain refusal; revoke/tighten
- **L061 — Swish — showcase / submission** (P1): https://ethglobal.com/showcase/swish-0vft8 — Compare simulated effects to declaration; Move proof objects consumed upon spend; scoped vaults
- **L062 — 0G SkillGate — showcase / submission** (P2): https://ethglobal.com/showcase/0g-skillgate-xja63 — Deterministic static scan, optional model reviewer, hash registry
- **L063 — Aegis402 — showcase / submission** (P2): https://ethglobal.com/showcase/aegis402-o8x6z — Pre-audit hook scrutiny, post-audit realized effects/MEV signals
- **L064 — HumanSign — showcase / submission** (P2): https://ethglobal.com/showcase/humansign-ad6j1 — owner approval recorded onchain, per-payment/daily caps, MCP tool
- **L065 — Mandate Agents — showcase / submission** (P2): https://ethglobal.com/showcase/mandate-agents-wxnex — Deterministic adapters, smart-account cap/allowlist/replay, Ledger approval
- **L066 — Skill Auditor — showcase / submission** (P2): https://ethglobal.com/showcase/skill-auditor-44oie — Semantic analysis, sandbox execution, skill audit report hash
- **L067 — StableCoinManager — showcase / submission** (P2): https://ethglobal.com/showcase/stablecoinmanager-8z1et — Code-enforced allowance, payee/network pin, no duplicate signatures upon retries, settlement receipt
- **L068 — StableSettle — showcase / submission** (P2): https://ethglobal.com/showcase/stablesettle-iw6kh — single Solidity spend gate, multi-limit policy, 6-tool MCP
- **L069 — xPayables — showcase / submission** (P2): https://ethglobal.com/showcase/xpayables-h9950 — Ledger-signed vendor and budget rules, idempotent settlement state

### Hackathon source repositories (15)

- **L070 — Arx — repository** (P1): https://github.com/YagnaRDK/Arx — Policy engine, nonce/replay checks, calldata/value binding, signer boundary, 14 adversarial scenario claims [commit 3e8176a833d855ac229b7422079c4baeeab16abe]
- **L071 — Clembot Doorman — repository** (P1): https://github.com/clemenswan/clembot-doorman — Local MCP tool gate, two-stage vetting, pinned recipe, harness A/B test [commit ba7c08e0345a52106107edbdc23c8426d9fdba2e]
- **L072 — DSAP / AgentLatch — repository** (P1): https://github.com/prathamesh-mutkure/agent-latch — ENS-stored policy, ALLOW/BLOCK/HUMAN_APPROVAL, fresh owner confirmation, MCP integration [commit 80a5fd5ae8d818aa0edf69f2f136b5c2bc1f5988]
- **L073 — Evzi — repository** (P1): https://github.com/EvgenyNasretdinov/evzi — Human-signed immutable intent, constraint verification, calldata decoding, chain-state comparisons [commit 8a20d2dc05afc6325da65c4e82046bab29a698b4]
- **L074 — Guardrail Alpha — repository** (P1): https://github.com/caelum0x/guardrail — Rust risk engine between strategy and TWAK signer; offline paper mode, event log [commit 8fcd7f1e6628d9f1a2bb6d04811a5bb0f37d0e80]
- **L075 — Harness — repository** (P1): https://github.com/LeoFranklin015/Harness — Container isolation, hardware signer, ENS identity, revocation
- **L076 — intentOS — repository** (P1): https://github.com/rtree/2026NYC-ethglobal — Signed typed ExecutionRequest, hard contract limits, Watcher may freeze/tighten, no LLM custody
- **L077 — Leash — repository** (P1): https://github.com/ksin751119/leash — Shared budget keyed by ENS identity/token/period; chain refusal; revoke/tighten [commit f08ee0496562c3d6d2aec029bd8ea0469fe161e6]
- **L078 — Settle — repository** (P1): https://github.com/Pratiikpy/Settle — Atomic policy checks, capability pin, receipts with hash verifier, 3 SDK runtimes [commit 05889590058208932751df2e473ae7741b670d7d]
- **L079 — Solana Guard — repository** (P1): https://github.com/abhigyan1102/solana-guard — Anchor register_agent/set_policy/validate_and_execute/toggle_agent structure
- **L080 — Swish — repository** (P1): https://github.com/Khalid-000-ME/swish — Compare simulated effects to declaration; Move proof objects consumed upon spend; scoped vaults [commit b47f40e853dd502ffbb5a1cfb13ad7593d8052b0]
- **L081 — Verified Execution Agent — repository** (P1): https://github.com/alicesparkai/verified-execution-agent — Decodes calldata/approvals; signed PASS/BLOCK receipts and post-trade attestation
- **L082 — Aegis402 — repository** (P2): https://github.com/AEGIS402/post-audit — Pre-audit hook scrutiny, post-audit realized effects/MEV signals
- **L083 — Skill Auditor — repository** (P2): https://github.com/Arttribute/skillauditor — Semantic analysis, sandbox execution, skill audit report hash [commit f28376a6e7836cb1f41372aec13dfcb11486fc81]
- **L084 — StableCoinManager — repository** (P2): https://github.com/elsoul/stablecoinmanager — Code-enforced allowance, payee/network pin, no duplicate signatures upon retries, settlement receipt

### Operational and supplementary links (8)

- **L085 — Git clone alias — 0x-ai.git** (P2): https://github.com/0xProject/0x-ai.git — Clone URL used by previous pinned-checkout script
- **L086 — Git clone alias — 0x-cli.git** (P2): https://github.com/0xProject/0x-cli.git — Clone URL used by previous pinned-checkout script
- **L087 — Git clone alias — 1inch-ai.git** (P2): https://github.com/1inch/1inch-ai.git — Clone URL used by previous pinned-checkout script
- **L088 — Git clone alias — cli.git** (P2): https://github.com/jup-ag/cli.git — Clone URL used by previous pinned-checkout script
- **L089 — Git clone alias — cow-sdk.git** (P2): https://github.com/cowprotocol/cow-sdk.git — Clone URL used by previous pinned-checkout script
- **L090 — Git clone alias — rootstock-monorepo.git** (P2): https://github.com/BASEDNUT/rootstock-monorepo.git — Clone URL used by previous pinned-checkout script
- **L091 — Git clone alias — uniswap-ai.git** (P2): https://github.com/Uniswap/uniswap-ai.git — Clone URL used by previous pinned-checkout script
- **L092 — Non-substantive fixture or asset URL** (P3): https://example.org/manifest — A link inside a retained fixture/manifest, not a research source

### Additional relevant official entry points (4)

- **L093 — 0x docs** (P2): https://docs.0x.org/home/home — 0x API and agent developer reference
- **L094 — Balancer v3 docs** (P2): https://docs-v3.balancer.fi/ — Upstream pool math and SDK reference
- **L095 — BASED NUT docs** (P2): https://docs.basednut.com/ — Project documentation
- **L096 — ETHGlobal showcase index** (P2): https://ethglobal.com/showcase/ — Competition project discovery; broad contextual link

