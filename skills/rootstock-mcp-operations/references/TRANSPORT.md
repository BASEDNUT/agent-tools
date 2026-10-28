# MCP transport and validation

Authoritative documents, reviewed 2026-10-23:
- https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio
- https://modelcontextprotocol.io/specification/2026-07-28/server/discover
- https://modelcontextprotocol.io/specification/2026-07-28/server/tools
- https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning

One newline-delimited JSON-RPC message per stdin line; stdout only JSON-RPC replies. Tool errors return `isError=true` and no transaction is attempted. Each modern result includes `resultType: complete`. Legacy replies omit it.

Example modern request (single line in actual transport):

```json
{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28","io.modelcontextprotocol/clientCapabilities":{}}}}
```

Example legacy handshake:

```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"operator","version":"1.0.0"}}}
```

MCP transport and metadata are not identity proof or an authorization mechanism. This server is intentionally read-only.
