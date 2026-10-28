# Decision log — v0.1

- D1: Maintain Rootstock and Orchard as distinct protocol/execution vs data/interpretation surfaces. ACCEPTED historical product constraint.
- D2: Skills precede CLI and MCP in the development plan. USER-DIRECTED.
- D3: First skill pack is read-only, vendor-agnostic, small and testable. PROVISIONAL IMPLEMENTATION SCOPE.
- D4: Canonical capability library should serve both CLI and MCP; adapters do not call shell text from each other. PROPOSED.
- D5: No hardcoded contract addresses in skills; read canonical deployment sources at pinned revision. PROPOSED.
- D6: Observation JSON schema is a fixture spec, not the existing Orchard API contract. PROPOSED; migration mapping required.
- D7: Actual CLI implementation, MCP server, agents, wallet automation, git publication remain NOT STARTED.

## Phase gates

0. Source skill + negative tests PASS → 1. Read-only capability API and CLI design review → 2. CLI implementation with frozen chain fixture verification → 3. MCP adapter backed by exactly same core → 4. Agent-level behavioral evals and independent chain integration.

## Open

- Agree exact system boundary for rootstock agent repo vs existing rootstock-monorepo vs Orchard and Peanutoshi.
- Choose runtime/toolchain based on measured needs and existing Rootstock shared library dependencies.
- Map provisional observation schema to V25's approved `meta/data/links` resource envelopes.
- Check licensing of upstream materials; use original implementation for proprietary distribution if needed.
