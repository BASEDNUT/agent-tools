# Independent corrective audit — v0.7.1-beta

**Scope:** Existing `v0.7.0-beta` source and wheel, not the full Rootstock/Orchard systems; offline source review, code execution, adversarial tests, source-to-wheel parity, and independent crypto vectors. No Pi, GitHub writes, wallet keys or chain transactions.

## Reproduced defects before fixing

1. **Keccak padding defect (high):** original pure-Python `keccak256()` appended another rate block when the message length was 135, 271, 407, ... bytes. OpenSSL's `KECCAK-256` disagreed at those lengths. Fixed by ORing final 0x80 bit into the existing last byte. Three independently computed vectors embedded in tests.
2. **Historical-coverage loss (high):** `index.sync(52131550..52131557)` followed by a rescan of `52131553..52131554` made `scanned_intervals` incorrectly shrink to only the narrower range. The SQL statement removed the encompassing coverage interval. Deleted the faulty statement; coverage now accumulates successful scanned intervals while reorg handling separately truncates invalidated coverage.
3. **Snapshot instability (medium):** `pools.inspect` and `accounts.balances` used a pinned block number but did not re-check the block hash after the RPC calls. Observed reorgs could combine data from different branches. Added a second block-header verification. Same check applied to `accounts.positions` and successful ERC4626 wrapper probes.
4. **Receipt integrity (medium):** receipt results could accept an explicitly contradictory `transactionHash`, and status `0x3` was treated as a failed transaction. Both are rejected. This is a provider-relative check, not independent inclusion proof.
5. **MCP protocol errors (medium):** invoking a tool absent from the exposed inventory yielded a normal tool result with `isError: true`. Now returns JSON-RPC `-32602` (invalid tool request). Execution failures on known tools remain tool results.
6. **Build/test fidelity (medium):** tests of the Node SDK need an installed wheel or `PYTHONPATH=src`; the raw extracted source tree alone does not satisfy the module-import precondition. The independently run Node suite reported three failures without that setup, then five passing with the explicit correct setup. The release verifier now checks all shipped Python module bytes against source.

## Repeatable validation

```bash
python3 -m unittest discover -s tests -q
PYTHONPATH=src node --test sdk-ts/index.test.mjs
python3 tools/audit_skills.py .
python3 tools/test_security_policy.py .
python3 tools/test_observation_contract.py .
python3 tools/verify_distribution.py .
```

## Remaining limits / not certified

- No live Base RPC, chain finality, price-feed authenticity, complete pool/archive coverage, or deployed Orchard ELO audit.
- No third-party formal audit, security proof, signer, execution controller, or controlled wallet spending. Transactions remain unsigned and never broadcast.
- Provider-returned data may be incomplete, dishonest or manipulated; same-provider hash consistency checks do not establish finality or independent truth.
- SQLite operations over large histories and real MCP client conformance need load and cross-client testing.
- The source-pinned Balancer SDK patch alignment from earlier work was not rechecked against a full checkout in this audit.
- MCP stdio is implemented; a remotely authenticated MCP service is not.

**Result:** Corrected beta under offline tests. **Not** equivalent to "correct and without errors" in all live environments.
