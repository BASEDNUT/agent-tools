---
name: rootstock-abi-catalog
description: Use when decoding Rootstock calls, determining ABI selectors, inspecting contract interfaces or comparing upstream Balancer deployments.
metadata:
  author: rootstock-orchard-agent-tools
---

# Source-bound ABI inspection

1. Run `rootstock call registry.abi_catalog` for the reviewed **partial read** selector inventory.
2. Run `rootstock call registry.abi_selector --args '{"interface":"ERC20","signature":"balanceOf(address)"}'` for a specific reviewed selector.
3. Resolve Rootstock chain IDs and targets from the pinned registry, not Balancer's upstream address table. Historical/deprecated task names require explicit task selection.
4. A selector being listed **does not prove** bytecode, on-chain code equivalence, contract behavior, or signing safety. Always separate ABI provenance from live runtime evidence.
5. For financial authorization, require exact deployment artifact ABI + bytecode provenance + decoded arguments and state effects; no such authority exists in this toolkit.

References: [reviewed source](https://github.com/balancer/balancer-v3-monorepo/blob/main/pkg/interfaces/contracts/vault/IVaultExtension.sol) and [Rootstock deployments](https://github.com/BASEDNUT/rootstock-monorepo/tree/main/deployments).
