# AGENTS.md — standalone Rootstock / Orchard agent tools

- Read `README.md`, `docs/CAPABILITY_COVERAGE.md`, `docs/SECURITY_BOUNDARIES.md` before engineering new capabilities.
- Semantic Kernel: externalize assumptions/evidence, execute tests, revise false hypotheses. Do not replace proof with more files.
- Rootstock DEX != Balancer upstream deployment registry != Orchard graph and analytics. Inspect effective SDK dependency patches.
- Pin repository+file SHA for every ABI/contract interpretation. Never claim actual on-chain state from source alone.
- Use `rootstock_tools.core.Toolchain` for domain logic, not duplicated CLI/MCP/API adapters.
- Only explicitly authorized local index sync may mutate local SQLite; no deployed wallet, contract or GitHub mutations.
- Unknown pool type, token relation, price, rates, eligibility or coverage must stay unknown. Never fabricate zeros or decimals.
- Transaction signing/broadcast/approval/deployment is prohibited until independent authenticated policy, simulator, signer, transaction firewall and independent review exist.
- Do not enable NUT shorting.
- Run the complete test suite, source/skill integrity gates, and real browser mobile/desktop smoke tests before release; record failures.
- v0.7 is a beta partial feature set; do not call the 25 original goals implemented based solely on published callable names.
