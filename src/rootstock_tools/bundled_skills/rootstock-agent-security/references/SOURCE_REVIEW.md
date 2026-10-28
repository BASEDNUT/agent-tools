# Security references: inspected 2026-10-23

Original sources; conclusions below are analytical, not borrowed code or a certification.

1. **OWASP Top 10 for Agentic Applications 2026**: `https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/` — agent goal hijack, tool misuse, privilege abuse, supply chain, code execution, memory poisoning, insecure inter-agent messages, cascading failures, trust, rogue behavior.
2. **OWASP Agent Control Standard**: `https://genai.owasp.org/resource/agent-control-standard-acs/` — portable runtime interception and declarative control, not only instructions.
3. **Microsoft Agent Governance Toolkit**: `https://github.com/microsoft/agent-governance-toolkit` and `policy-engine/docs/security-model.md` — host enforces outcome of policy evaluations; incomplete interception is outside coverage. Read-only research of public preview, not runtime evaluation.
4. **IBM Smith**: `https://github.com/IBM/smith` — iterative security-guidance analysis, policy generation, tests and refinement. Experimental components; it is an analysis skill, not inherently a runtime gate.
5. **Open Policy Agent**: `https://github.com/open-policy-agent/opa` — general PDP for declarative decisions; executor is responsible for enforcing them.
6. **OpenAI Agents SDK guardrails**: `https://developers.openai.com/api/docs/guides/agents/guardrails-approvals` — tool guardrails and approval interruptions; input/output guardrails alone do not cover all tool calls.
7. **LangChain human-in-the-loop**: `https://docs.langchain.com/oss/python/langchain/human-in-the-loop` — checkpointed approval/reject/edit of tool calls; persistent checkpointer needed for production.
8. **MCP maintainer analysis of annotations**: `https://blog.modelcontextprotocol.io/posts/2026-03-16-tool-annotations/` — `readOnlyHint` and related annotations are advisory, can lie, and must not be treated as authorization.
9. **Safe spending limits**: `https://help.safe.global/articles/3961440620-set-up-and-use-spending-limits` — onchain per-token allowance, NOT a recipient restriction.
10. **Trail of Bits skills**: `https://github.com/trailofbits/skills` — scoped audit skills, anti-rationalization checks and reproducible verification.

Takeaway: adopt a compact, portable safety skill today; eventually add independently enforced host policy/PEP and wallet containment. Do NOT publish an 'agent is secure' claim based on text-only skill or offline prototype.
