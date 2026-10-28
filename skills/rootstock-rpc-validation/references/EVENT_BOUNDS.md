# Event and RPC boundaries

Canonical inspected Rootstock sources:
- https://github.com/BASEDNUT/rootstock-monorepo/blob/main/packages/lib/modules/pool/onchain-pool-discovery.ts
- https://github.com/BASEDNUT/rootstock-monorepo/blob/main/deployments/base.json
- https://github.com/BASEDNUT/rootstock-monorepo/blob/main/deployments/base-sepolia.json

Mainnet Vault: `0x0a3af0Da0175afa0Cc05a6ad9092dC740155a0E7`; start block `52131550` (repository-reported).
Sepolia Vault: `0xEf348c4222ab9c08aFE768AD722Fb02b10d640c9`; start block `46984000` (repository-reported).

Event topic0: `0xbc1561eeab9f40962e2fb827a7ff9c7cdb47a9d7c84caeefa4ed90e043842dad`.

Exposed operations cannot sign, send transactions, create pools, grant allowances, modify registry files, or return invented historical analytics. Current scanner does not perform full-chain indexing or reorg reconciliation: block-window reads are bounded and source-dependent.
