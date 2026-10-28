# Agent security systems — comparative research (2026-10-23)

## Question

How can agent instructions and per-task checklists accumulate into a reusable safety system without giving agents unrestrained access to tooling or on-chain funds?

## Findings from canonical projects

| Reference | Observed implementation/design | Our take | Limit |
| --- | --- | --- | --- |
| OWASP Agentic Top 10 / ACS | Explicit agent threat model; interception points and declarative enforcement | Tag risks, cross framework gates, record evidence | Framework/guidance alone doesn't block calls |
| Microsoft Agent Governance Toolkit | Policy kernel, framework adapters, identity, audit, trust boundaries | A shared host-side middleware instead of one safety implementation per CLI/MCP | Preview / policy engine requires correct host routing |
| IBM Smith | Skill creates policies, adversarial tests, iterative refinement | Compound skills into security **tests** and audited policy changes | Generated policies still require human review and trusted enforcement |
| Open Policy Agent | Decoupled deterministic policy decision point | Rules as code in future runtime, not natural-language consent | PDP is not PEP or signer |
| OpenAI Agents SDK | Input/output/tool guardrails, approval interruption and run persistence | Validate both tools and human approvals at consequential boundaries | Agent-level guardrails do not cover all tool calls automatically |
| LangGraph | Human-in-the-loop interrupts with persistent state | Approve/reject exact requested calls and resume safely | Checkpoints can be misused; prevent tool replay |
| MCP specification | Read-only/destructive hints and OAuth features | Metadata for discovery; never a permission grant | Annotations are advisory and may be false |
| Trail of Bits security skills | Threat-scoped audits, prechecklists, defensive review, skills curation | Strict audit skill triggers, specific artifacts, negative cases | A security-audit report isn't runtime enforcement |
| Safe Allowance Module | On-chain token spending caps and reset intervals | One potential future wallet containment layer | Token caps do NOT restrict recipients |

## Interpretation for Rootstock and Orchard

Security has TWO products, not one:

- **Safety development knowledge:** a portable skill and checklist invoked before coding, before adding tool capabilities and before evaluation. This v0.2 package is that product.
- **Runtime control plane:** trusted identity, tool registry, policy decision point, enforcement point, stable signing interface, approvals, budgets, observability, kill switch. This is architectural work **not present** in v0.2.

Enforceable constraints must use typed contracts verified at the last point of execution. Do not ask the agent to self-police after giving it an unrestricted shell, full RPC tx-submission or wallet private key. MCP and CLI adapters must call one common policy-aware capability boundary. Interposition must cover direct SDK use and scheduled jobs, not just visible chat tool calls.

## Compounding development loop

1. Security skill defines intended behavior and identifies sensitive boundaries.
2. Auditor checks the skill and generates missing negative cases.
3. Policy code eventually encodes an enforceable allowlist with operator review.
4. Tool implementations call the policy evaluator on every invocation.
5. Host tests confirm disallowed tool calls never reach a side-effecting executor.
6. Wallet/chain constraints independently limit financial authority.
7. Adversarial evaluation and monitoring reveal new counterexamples.
8. Human-reviewed fixes update policy, skills, fixtures and source references before promotion.

## First deterministic demonstration

`security/prototype_policy.py` classifies *proposed* tool operations. It has no wallet, keys, network, signer or actual tool access. A returned `ALLOW_READ` is **not** an authorization decision in the production sense. It does not authenticate a principal; it does not prove target contract identity or on-chain data provenance. The implementation is purposely designed to **never produce an executable grant**. It rejects all unrecognized or side-effecting operations.

`tools/test_security_policy.py` tests both benign reads and deliberate adversarial requests, including admin impersonation via extra arguments, prompt injection, shell commands embedded in arguments, chain confusion and disguising write commands as reads.

## Priority gaps before enabling any live agent

P0: Authenticated agent/user identity; kernel-level deny-by-default policy enforcement over all execution paths; external policy store; mandatory tool registry; isolated credentials; no signing keys for analysts; audit records; kill switch and emergency suspension; untrusted input boundary checks.

P1: Typed/pinned Rootstock deployment manifests; independent RPC attestation, read-only whitelist and reorg-aware snapshots; taint tracking; compromised-tool containment, approval fingerprinting, replay prevention, economic simulations, budgets and limits.

P2: Secure build pipeline, evaluated cross-model agent behavior, MCP authentication, per-agent resource isolation, token and rate policies, egress control, observability and incident response rehearsals.

## No production guarantees

No third-party package was installed or executed for this research. The new skill and policy demonstrator are original, independent, offline artifacts, not copies of third-party code. No claim of compliance with OWASP, certification, third-party audit, DeFi profitability or production safety is made.

See `skills/rootstock-agent-security/references/SOURCE_REVIEW.md` for original source URLs.
