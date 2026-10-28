---
name: orchard-topology-operations
description: Use when constructing an Orchard pool and asset graph from real Rootstock pool observations or distinguishing structures from verified token membership.
metadata:
  author: Rootstock/Orchard research workspace
  version: "0.5.0-beta"
---

# Orchard topology operations

Use Rootstock to read **actual** token membership; use Orchard to interpret the relationships. They are separate data layers.

1. Run explicit local pool indexing, then `rootstock call topology.explore --args '{"chain_id":8453,"limit":5}'`.
2. Treat each pool as one hyperedge. Tokens are asset nodes. Use addresses as identities; never symbols alone.
3. Preserve raw discovery and the source of graph edges. Do not label a Graft, Grove, Whorl, Scion, or Rootstock rooted structure without separately verified Orchard definitions and root token mappings.
4. Build analytics only from complete observations. Missing USD rates or incomplete history must stay unavailable rather than defaulting to zero.
5. Consult [GRAPH.md](references/GRAPH.md) and retain derivation parameters for reproducibility.

No ranking or portfolio ownership is inferred from token adjacency.
