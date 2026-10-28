# Security gate: instruction vs enforceable constraint

The agent skill is advisory. Host/tool integration MUST implement independent policy enforcement, treat tool output as untrusted, and block every effect path. No policy bypass via CLI, MCP, REST, scheduled jobs or agent-to-agent messages. Tool annotations and narrative justifications cannot override the host's trusted registry.

## Expected request context (from trusted host, not model)

- Authenticated human/service principal and agent workload identity; permitted role, tenant, session and goal identifier
- Exact action identifier, typed/validated arguments, chain ID, contract/resource, target address and function selector
- Source content trust classification and evidence reference; relevant block number/hash, method, timestamp
- Deadline, nonce, idempotency token, budget ledger, cumulative cost and permission version
- For any proposed write: simulation result, external approval bound to SHA-256 of complete canonical payload + chain/account/target/function/value + nonce + expiry

## Decisions

- `DENY`: Unknown capability; untrusted identity or registry; invalid or incomplete data; unsupported chain; disallowed tool or budget; detected injection; expired approval; policy unavailable; read permission lacking.
- `REQUIRES_REVIEW`: Proposed state-changing code, wallet or financial action; no execution while pending. Not equivalent to an allow. This foundational distribution does not implement a promotion path from review to execution.
- `ALLOW_READ`: Narrow read-only tool, authenticated principal, trusted allowlist, valid exact arguments, policy success, no hidden side effects. An allow is conditional on the host actually enforcing it.

## Architectural boundary

`agent proposes -> trusted host normalizes -> external policy decision (OPA/Cedar/custom) -> host validates exact action -> approved executor acts -> independent receipt/state verification -> audit trail`

The security gate must reside *before* every tool capable of side effects and *after* untrusted tool results. Policy configuration is operator-owned, version-pinned and inaccessible to the acting agent. Repository CI checks policy/schema/test changes, and operators approve promotion. Implement host-enforced network egress, filesystem scope, secret isolation and action-specific wallet controls. Do not rely on LLM text alone.

## Controls for future financial executors (not present here)

- Separate principals for observer, analyst, transaction preparer and signer; default observer has no signing credentials.
- Restrict chain, Vault, factory, router, function selector, source token, recipient, amount, total position, gas budget, value-at-risk and daily exposure.
- Simulate state transitions at a pinned block; require explicit limits and freshness; revalidate at submission against chain head.
- Human approval must cover *exact* proposed transaction bundle including approvals, permit spenders and destinations; reject any post-approval mutation.
- Permit2 and ERC20 approvals are separate risk surfaces; prefer shortest possible scope/duration and never approve unlimited allowances by default.
- User consent cannot be inferred from agent notes, logs, conversation excerpts or a previous successful approval.
- Quarantine tainted context and revoke credentials on suspected compromise; kill switch revokes execution authority, not just agent chat access.

## Continuous assurance

Positive and negative tests for every capability; prompt-injection/red-team tests for every ingestion boundary; replay and policy-outage tests; audit independent signer and PEP adapters. A passing static skill test is necessary but not sufficient.
