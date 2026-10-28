---
name: rootstock-mcp-operations
description: Use when integrating AI assistants and agent runtimes with the Rootstock/Orchard read-only MCP server, validating MCP tool inputs, tool discovery, per-request versioning, or troubleshooting stdio compatibility and source provenance.
metadata:
  author: basednut-research
  version: "0.4.0"
---
# Rootstock MCP integration

The server is **a projection of the shared Python SDK**. Never add unique financial logic or permissions to the MCP adapter.

1. Install the packaged toolchain in a clean Python 3.11+ environment (`pip install .`).
2. Start `rootstock mcp` (or `rootstock-mcp`) through the client subprocess. Standard output is JSON-RPC **only**; never use it for diagnostics.
3. For modern clients, use `2026-07-28` and per-request `_meta` with `io.modelcontextprotocol/protocolVersion` and `io.modelcontextprotocol/clientCapabilities`. Discover via `server/discover`.
4. Legacy clients use `2025-11-25` `initialize` and `notifications/initialized` handshake. Confirm which era the client actually runs before interpreting errors.
5. Only capabilities in `rootstock capabilities` may be called. Use `resources/list` and `resources/read` to access the bundled skills. The descriptions are guidance, not permission grants.
6. Inspect **result provenance**. `rpc.get_health` contacts the configured network. `pools.list` requires an explicit block interval of at most 2000 blocks; no price/TVL/fees are inferred.
7. Never expose signing, approval, RPC send, arbitrary contract-call or generalized filesystem methods. Changing tool inventory requires threat review and negative tests.

For wire examples, see [references/TRANSPORT.md](references/TRANSPORT.md). The agent is not an authority to change contract addresses or tool allowlists.
