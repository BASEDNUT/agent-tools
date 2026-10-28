# Evidence hierarchy and conflict handling

1. **Verified chain observation at a pinned block:** exact chain ID, RPC, block number/hash, contract address, `eth_getCode`, event receipts and decoded state.
2. **Canonical Rootstock deployment data** at pinned commit, including provenance and ABIs. This is evidence of deployed *intent* until independently compared with chain.
3. **Canonical Based Nut project configuration** (`config.py`) where token/economic identity is applicable. Report conflicts; never overwrite either source to force agreement.
4. **Rootstock SDK/frontend implementation**, including `onchain-pool-discovery.ts` and factory event-scanning code; implementation may be stale or incomplete.
5. **Static baked pool registries and Orchard demo aliases:** only historical repo snapshots; not current balances, APY, fees or on-chain verification.
6. **Balancer upstream docs/SDK:** math and integration patterns only. Balancer's separate Vault, factory and API data are NOT Rootstock identities.

When evidence conflicts, emit both with provenance and an unresolved verdict. Do not blend snapshots of different blocks into one current reading. Do not infer that an internal audit of two primitive factories is an independent third-party audit of those contracts.

Canonical references: https://github.com/BASEDNUT/rootstock-monorepo ; https://github.com/balancer/b-sdk ; https://github.com/balancer/balancer-deployments.
