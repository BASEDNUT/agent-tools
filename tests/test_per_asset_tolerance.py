"""Regression: one provider-broken token must not abort a 32-asset read batch.

Live-caught 2026-10-27: USDC balanceOf on public Base RPCs returns an
empty 0x result (provider simulation quirk), aborting the whole batch.
Multi-asset reads must degrade per-asset: honest read_error entries,
no fabricated zeros, other assets unaffected.
"""
import unittest
from rootstock_tools.rpc import ChainError
from rootstock_tools.services import wallet_balances

WALLET = "0x135b208ac2480B0d876944416De16E7a3B9A1F65"
GOOD1 = "0xb8de15fb529d98c93c749de63c749d48d25a30df"  # NUT
BAD = "0x833589fCD5eDb6E6fa2CAb1B97BaD1B63f34E4d1"    # USDC
GOOD2 = "0xAC130701aa31c284c36609E2489f150F419AD7AD"  # SNUT


class _FakeRpc:
    """Deterministic fake: BAD token returns empty 0x for balanceOf."""
    chain_id = 8453

    def __init__(self):
        self.calls = 0

    def check_chain(self):
        return 8453

    def call(self, method, params):
        self.calls += 1
        if method == "eth_blockNumber":
            return hex(53000000)
        if method == "eth_getBlockByNumber":
            return {"hash": "0x" + "a" * 64}
        if method == "eth_call":
            target = params[0]["to"].lower()
            data = params[0]["data"]
            if target == BAD.lower() and data.startswith("0x70a08231"):
                return "0x"  # provider quirk: empty result
            if data.startswith("0x70a08231"):
                return "0x" + "f" * 64  # balance 1
            if data.startswith("0x313ce567"):  # decimals()
                return "0x" + hex(18)[2:].rjust(64, "0")
            if data.startswith("0x06fdde03") or data.startswith("0x95d89b41"):  # name()/symbol()
                return "0x" + (32).to_bytes(32, "big").hex() + (4).to_bytes(32, "big").hex() + b"TEST".hex().ljust(128, "0")
            if data.startswith("0x18160ddd"):  # totalSupply()
                return "0x" + "1" * 64
            raise ChainError("unexpected call")


class PerAssetToleranceTest(unittest.TestCase):
    def test_bad_token_degrades_per_asset_not_batch(self):
        rpc = _FakeRpc()
        result = wallet_balances(rpc, WALLET, [GOOD1, BAD, GOOD2])
        assets = {a["token"]: a for a in result["assets"]}
        self.assertEqual(assets[GOOD1.lower()]["balance_raw"], str(int("f" * 64, 16)))
        self.assertEqual(assets[GOOD2.lower()]["balance_raw"], str(int("f" * 64, 16)))
        self.assertIsNone(assets[BAD.lower()]["balance_raw"])
        self.assertIn("read_error", assets[BAD.lower()])
        self.assertTrue(assets[BAD.lower()]["read_error"])
        # batch-level state remains honest
        self.assertEqual(result["state"], "observed_partial")

    def test_all_good_unchanged(self):
        rpc = _FakeRpc()
        result = wallet_balances(rpc, WALLET, [GOOD1, GOOD2])
        self.assertEqual(result["state"], "observed")
        self.assertTrue(all(a["balance_raw"] is not None for a in result["assets"]))


if __name__ == "__main__":
    unittest.main()
