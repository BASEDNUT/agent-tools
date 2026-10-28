# Validation — v0.7.1-beta — 2026-10-23

## Repeatable commands

```sh
python -m unittest discover -s tests -q
python tools/audit_skills.py .
python tools/test_security_policy.py .
python tools/test_observation_contract.py .
python tools/evaluate_evidence.py
python tools/check_sdk_patch.py --patch /path/to/verified/sdk.patch --registry-dir /path/to/pinned/rootstock/deployments
PYTHONPATH=src node --test sdk-ts/index.test.mjs
python tools/verify_distribution.py  # after wheel build
```

The independent v0.7.1 audit added eight regression tests in `tests/test_v071_audit.py`. Original 130 -> 138 total Python tests. Five Node bridge tests require either `PYTHONPATH=src` or a properly installed Python wheel. Keccak test vectors were obtained independently with OpenSSL KECCAK-256. Source-to-wheel Python module parity is now checked.

New tests include same-block quote/portfolio, actual receipt canonicality validation, malicious price values and block mismatch, absent/incomplete price input, operator-configured eligibility, untrusted Orchard chain, indexed registration after swaps, event log cursor pagination and MCP parity.

**Tested in isolated local environment:** Python/SQLite fake RPC and subprocess APIs, CLI/MCP/HTTP adapters, bundled skill parity and installable wheel.

**NOT tested:** live Base RPC, full archives, independent provider confirmations, price oracles, on-chain TVL/24h turnover/ELO, production access policy, hardware wallet signing, external MCP clients, production deployment or Rootstock V25 integration. Live RPC DNS/network access unavailable from this sandbox.

Existing deterministic 66-case security and 15-case observation fixture tests do not certify deployed security or data quality. Exact counts and wheel status are recorded in the release manifest and logs.

The SDK patch comparison requires the actual reviewed Rootstock SDK patch and both exact pinned registry files, neither of which is in this source ZIP; it is not an automatically runnable standalone check. Reference evidence snapshots and Git blob pins are retained separately.
