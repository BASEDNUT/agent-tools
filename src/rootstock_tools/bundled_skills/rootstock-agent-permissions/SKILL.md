---
name: rootstock-agent-permissions
description: Configure and audit Rootstock agents with separate read capability scopes and independent-denial policies. Use for trusted launcher manifests, scoped MCP/CLI/API processes, least privilege, compromised agent risk, chain restrictions and reviewing any change to tool permissions.
metadata:
  author: Rootstock/Orchard toolchain
  version: "0.6.0-beta"
---

# Rootstock agent permission scope

## Authority hierarchy

The human operator owns authority. A trusted host launches the toolkit with a known **process identity** and a reviewed policy file. The LLM may propose operations but cannot grant itself new permissions through the toolkit.

```sh
rootstock --policy-file config/agent-policy.example.json --agent-id research-reader capabilities
```

This agent id is asserted by the launching process; it is **not cryptographic authentication**. An adversary with shell access able to launch its own unrestricted toolkit process can bypass this gate. The gate also does not secure a private key, a wallet, a kernel or external RPC credentials.

## Mandatory checks

1. Load the policy at process startup; fail if identity is missing or manifest invalid, duplicated, symlinked or larger than the limit.
2. Check every requested tool name against exact/prefix allowlists and any supplied chain against the agent chain scope.
3. Allow no wildcard `*` and no tool-level rewriting of the signed/protected scope. A human-approved policy file should be outside agent-writable areas.
4. Keep financial signing, broadcasts and executable transaction submission absent until there is a separately reviewed signer and policy enforcement surface.
5. Exercise negative cases: missing principal, forged tool name, unexpected argument, out-of-scope chain, malicious tool description, unsafe RPC method and invalid policy data.
6. Use source hashes, dependency pins, skill scanning and independent code review before installing agent skills or MCP servers.

## Critical distinction

A natural-language checklist is guidance. An authenticated signing boundary is security. This package currently offers a **read-only per-process gate**, not production financial authorization, and must describe the difference in every audit.
