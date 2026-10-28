"""Execute-layer security battery.

Signing, policy gates, and broadcast safety. RED first for the new modules;
no execution path may exist that skips simulation, policy, or leaks keys.
"""
import json
import os
import unittest

# Deterministic throwaway test key (0x0000...0001 private key form), never funded.
TEST_KEY = "0x" + "00" * 31 + "01"
EXPECTED_TEST_ADDRESS = "0x7E5F4552091A69125d5DfCb7b8C2659029395Bdf"


class SignerTests(unittest.TestCase):
    def _signer(self):
        from rootstock_tools.signer import Signer
        return Signer(TEST_KEY)

    def test_address_derivation_matches_known_vector(self):
        self.assertEqual(self._signer().address, EXPECTED_TEST_ADDRESS)

    def test_key_never_in_repr_or_str(self):
        s = self._signer()
        self.assertNotIn(TEST_KEY, repr(s))
        self.assertNotIn(TEST_KEY, str(s))
        self.assertNotIn(TEST_KEY.lower().replace("0x", ""), str(s).lower().replace("0x", ""))

    def test_signs_deterministic_transaction(self):
        s = self._signer()
        tx = {
            "chainId": 84532,
            "nonce": 755,
            "gas": 21000,
            "maxFeePerGas": 10_000_000_000,
            "maxPriorityFeePerGas": 1_000_000_000,
            "to": EXPECTED_TEST_ADDRESS,
            "value": 0,
            "data": "0x",
        }
        raw1 = s.sign_transaction(tx)
        raw2 = s.sign_transaction(tx)
        self.assertEqual(raw1, raw2)  # deterministic
        self.assertTrue(raw1.startswith("0x"))
        self.assertTrue(len(raw1) > 100)  # rlp-encoded signed tx

    def test_rejects_missing_chain_id(self):
        s = self._signer()
        with self.assertRaises(Exception):
            s.sign_transaction({"nonce": 0, "gas": 21000, "to": None, "value": 0})


class ExecutePolicyTests(unittest.TestCase):
    def _policy(self, **over):
        from rootstock_tools.executor import ExecutePolicy
        defaults = dict(
            allowed_chains={84532},
            router_allowlist={84532: {"0xDD9793Cd4B79a8bd65D690C64A3074D023Dfa759".lower()}},
            max_value_wei=10**15,
            daily_budget_wei=5 * 10**15,
            require_simulation=True,
            kill_switch=False,
        )
        defaults.update(over)
        return ExecutePolicy(**defaults)

    def test_chain_gate(self):
        p = self._policy()
        self.assertTrue(p.chain_allowed(84532))
        self.assertFalse(p.chain_allowed(8453))

    def test_kill_switch_blocks_everything(self):
        p = self._policy(kill_switch=True)
        self.assertFalse(p.chain_allowed(84532))

    def test_value_cap(self):
        p = self._policy()
        self.assertTrue(p.value_within_cap(10**14))
        self.assertFalse(p.value_within_cap(10**16))

    def test_router_allowlist(self):
        p = self._policy()
        r = "0xDD9793Cd4B79a8bd65D690C64A3074D023Dfa759"
        self.assertTrue(p.router_allowed(84532, r))
        self.assertFalse(p.router_allowed(84532, "0x" + "ab" * 20))

    def test_policy_never_reads_key(self):
        from rootstock_tools.executor import ExecutePolicy
        import inspect
        src = inspect.getsource(ExecutePolicy)
        self.assertNotIn("private", src.lower())
        self.assertNotIn("PEANUTOSHI", src.upper())


class ExecutorGateTests(unittest.TestCase):
    """Broadcast must be impossible without: policy pass + simulated receipt."""

    def test_no_execute_without_policy(self):
        from rootstock_tools.executor import Executor
        from rootstock_tools.signer import Signer
        ex = Executor(Signer(TEST_KEY), policy=None)
        with self.assertRaises(Exception) as cm:
            ex.send_value(84532, EXPECTED_TEST_ADDRESS, 0)
        self.assertIn("policy", str(cm.exception).lower())

    def test_sim_required_before_broadcast(self):
        from rootstock_tools.executor import Executor
        from rootstock_tools.signer import Signer
        policy = None
        class FakePolicy:
            def chain_allowed(self, c): return True
            def value_within_cap(self, v): return True
            def router_allowed(self, c, r): return True
            def record_spend(self, v): pass
            def require_simulation(self): return True
        class FailRpc:
            chain_id = 84532
            def call(self, method, params): raise AssertionError("broadcast attempted without sim")
        ex = Executor(Signer(TEST_KEY), policy=FakePolicy(), rpc=FailRpc())
        with self.assertRaises(Exception) as cm:
            ex.send_value(84532, EXPECTED_TEST_ADDRESS, 10**14, simulate_first=False)
        self.assertIn("simulat", str(cm.exception).lower())




class ExecuteRpcModeTests(unittest.TestCase):
    def test_readonly_rpc_cannot_broadcast(self):
        from rootstock_tools.rpc import JsonRpc, ChainError
        rpc = JsonRpc("https://example.invalid", 84532)
        with self.assertRaises(ChainError) as cm:
            rpc.call("eth_sendRawTransaction", ["0xdead"])
        self.assertIn("not on", str(cm.exception))

    def test_execute_rpc_allows_send_and_nonce(self):
        from rootstock_tools.rpc import JsonRpc
        import unittest.mock as mock
        rpc = JsonRpc("https://example.invalid", 84532, execute=True)
        fake_body = b'{"jsonrpc":"2.0","id":1,"result":"0xabc"}'
        with mock.patch.object(rpc, "opener") as m:
            resp = m.open.return_value.__enter__.return_value
            resp.status = 200
            resp.read.return_value = fake_body
            r = rpc.call("eth_sendRawTransaction", ["0xdead"])
            self.assertEqual(r, "0xabc")

    def test_execute_rpc_still_refuses_arbitrary_methods(self):
        from rootstock_tools.rpc import JsonRpc, ChainError
        rpc = JsonRpc("https://example.invalid", 84532, execute=True)
        with self.assertRaises(ChainError):
            rpc.call("eth_sign", ["0xabc", "data"])



class RouterCallGateTests(unittest.TestCase):
    """Contract calls must be router-allowlisted; arbitrary targets refused."""

    def _exec(self, rpc=None):
        from rootstock_tools.executor import Executor
        from rootstock_tools.signer import Signer
        class P:
            def chain_allowed(self, c): return c == 84532
            def value_within_cap(self, v): return 0 <= v <= 10**15
            def router_allowed(self, c, r): return r.lower() == "0xdd9793cd4b79a8bd65d690c64a3074d023dfa759"
            def record_spend(self, v): pass
            require_simulation = True
            kill_switch = False
        return Executor(Signer(TEST_KEY), policy=P(), rpc=rpc)

    def test_router_call_to_allowlisted_router_passes_gate(self):
        ex = self._exec()
        r = "0xDD9793Cd4B79a8bd65D690C64A3074D023Dfa759"
        # gate-level check only (no broadcast in unit test)
        self.assertTrue(ex.policy.router_allowed(84532, r))

    def test_router_call_to_arbitrary_target_refused(self):
        ex = self._exec()
        with self.assertRaises(Exception) as cm:
            ex.send_call(84532, "0x" + "ab" * 20, "0x1234", 0)
        self.assertIn("router", str(cm.exception).lower())

    def test_send_call_requires_simulation_path(self):
        from rootstock_tools.executor import Executor
        from rootstock_tools.signer import Signer
        class P:
            def chain_allowed(self, c): return True
            def value_within_cap(self, v): return True
            def router_allowed(self, c, r): return True
            def record_spend(self, v): pass
            require_simulation = True
            kill_switch = False
        class FailRpc:
            chain_id = 84532
            def call(self, method, params): raise AssertionError("broadcast without sim")
        ex = Executor(Signer(TEST_KEY), policy=P(), rpc=FailRpc())
        with self.assertRaises(Exception) as cm:
            ex.send_call(84532, "0xDD9793Cd4B79a8bd65D690C64A3074D023Dfa759", "0x", 0, simulate_first=False)
        self.assertIn("simulat", str(cm.exception).lower())

if __name__ == "__main__":
    unittest.main()
