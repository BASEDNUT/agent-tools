"""Policy-gated transaction executor. Broadcast is impossible without policy
and a passing simulation: structural enforcement, not a convention.
"""
from __future__ import annotations
import json
import urllib.request

from .signer import Signer


class ExecuteError(ValueError):
    pass


class ExecutePolicy:
    """Fail-closed execution gates: chains, routers, value caps, kill switch."""

    def __init__(self, *, allowed_chains: set[int], router_allowlist: dict[int, set[str]],
                 max_value_wei: int, daily_budget_wei: int,
                 require_simulation: bool = True, kill_switch: bool = False):
        self.allowed_chains = set(allowed_chains)
        self.router_allowlist = {c: {r.lower() for r in rs} for c, rs in router_allowlist.items()}
        self.max_value_wei = int(max_value_wei)
        self.daily_budget_wei = int(daily_budget_wei)
        self.require_simulation = bool(require_simulation)
        self.kill_switch = bool(kill_switch)
        self._spent_today_wei = 0

    def chain_allowed(self, chain_id: int) -> bool:
        if self.kill_switch:
            return False
        return chain_id in self.allowed_chains

    def value_within_cap(self, value_wei: int) -> bool:
        return 0 <= value_wei <= self.max_value_wei and self._spent_today_wei + value_wei <= self.daily_budget_wei

    def router_allowed(self, chain_id: int, router: str) -> bool:
        return router.lower() in self.router_allowlist.get(chain_id, set())

    def record_spend(self, value_wei: int) -> None:
        self._spent_today_wei += int(value_wei)


class Executor:
    """Signs and broadcasts only after policy + simulation gates pass."""

    def __init__(self, signer: Signer, *, policy, rpc=None):
        if not isinstance(signer, Signer):
            raise ExecuteError("Executor requires a Signer")
        self.signer = signer
        self.policy = policy
        self.rpc = rpc

    def _gate_chain(self, chain_id: int):
        if self.policy is None:
            raise ExecuteError("No execution policy loaded; broadcast refused")
        if not self.policy.chain_allowed(chain_id):
            raise ExecuteError(f"Chain {chain_id} not allowed by execution policy")

    def _gate_value(self, value_wei: int):
        if self.policy is None or not self.policy.value_within_cap(value_wei):
            raise ExecuteError("Value exceeds execution policy caps or budget")

    def _gate_simulation(self, simulate_first: bool):
        if self.policy is None:
            raise ExecuteError("No execution policy loaded; simulation gate refused")
        if self.policy.require_simulation and not simulate_first:
            raise ExecuteError("Policy requires simulation before broadcast; refusing")

    def send_call(self, chain_id: int, to: str, data_hex: str, value_wei: int = 0, *,
                  simulate_first: bool = True):
        """Contract call to an allowlisted router. Sim-first, policy-gated."""
        if self.policy is None or not self.policy.router_allowed(chain_id, to):
            raise ExecuteError("Target is not an allowlisted router for this chain; refusing")
        return self._broadcast_call(chain_id, to, data_hex, value_wei,
                                    simulate_first=simulate_first, target_type="allowlisted_router")

    def _broadcast_call(self, chain_id: int, to: str, data_hex: str, value_wei: int, *,
                        simulate_first: bool, target_type: str):
        """Shared broadcast path: gates, simulation, fees, sign, send, receipt."""
        self._gate_chain(chain_id)
        self._gate_value(value_wei)
        self._gate_simulation(simulate_first)
        if self.rpc is None:
            raise ExecuteError("No RPC configured for execution")
        if simulate_first:
            try:
                self.rpc.call("eth_call", [{"from": self.signer.address, "to": to,
                                            "value": hex(value_wei) if value_wei else "0x0",
                                            "data": data_hex}, "latest"])
            except Exception as exc:
                raise ExecuteError("Simulation failed; refusing to broadcast") from exc
        nonce = int(self.rpc.call("eth_getTransactionCount", [self.signer.address, "latest"]), 16)
        head = int(self.rpc.call("eth_blockNumber", []), 16)
        block = self.rpc.call("eth_getBlockByNumber", [hex(head), False])
        base = int(block.get("baseFeePerGas", "0x1"), 16)
        priority = 10 ** 9
        max_fee = base * 2 + priority
        gas = int(self.rpc.call("eth_estimateGas", [{"from": self.signer.address, "to": to,
                                                     "value": hex(value_wei) if value_wei else "0x0",
                                                     "data": data_hex}]), 16)
        tx = {"chainId": chain_id, "nonce": nonce, "gas": gas,
              "maxFeePerGas": max_fee, "maxPriorityFeePerGas": priority,
              "to": to, "value": value_wei, "data": data_hex}
        raw = self.signer.sign_transaction(tx)
        tx_hash = self.rpc.call("eth_sendRawTransaction", [raw])
        self.policy.record_spend(value_wei)
        return {"tx_hash": tx_hash, "chain_id": chain_id, "to": to, "value_wei": str(value_wei),
                "from": self.signer.address, "simulated": simulate_first,
                "target_type": target_type}

    def approve_router(self, chain_id: int, token: str, router: str, amount_wei: int, *,
                       simulate_first: bool = True):
        """ERC20 approve where the spender MUST be an allowlisted router.

        An approval cannot move funds by itself; only the approved party can
        pull, and allowlisted routers are registry-pinned Rootstock routers.
        Arbitrary spender addresses are refused.
        """
        from .evm import encode_call, addr_word, word
        self._gate_chain(chain_id)
        self._gate_value(0)
        self._gate_simulation(simulate_first)
        if self.policy is None or not self.policy.router_allowed(chain_id, router):
            raise ExecuteError("Approve spender is not an allowlisted router; refusing")
        data = encode_call("approve(address,uint256)", addr_word(router), word(amount_wei))
        return self._broadcast_call(chain_id, token, data, 0,
                                    simulate_first=simulate_first, target_type="erc20_approve_to_allowlisted_router")

    def send_value(self, chain_id: int, to: str, value_wei: int, *,
                   simulate_first: bool = True):
        """Simple ETH transfer. Simulates first when the policy demands it."""
        self._gate_chain(chain_id)
        self._gate_value(value_wei)
        self._gate_simulation(simulate_first)
        if simulate_first and self.rpc is not None:
            try:
                self.rpc.call("eth_call", [{"from": self.signer.address, "to": to,
                                            "value": hex(value_wei) if value_wei else "0x0",
                                            "data": "0x"}, "latest"])
            except Exception as exc:
                raise ExecuteError("Simulation failed; refusing to broadcast") from exc
        # nonce + fees
        if self.rpc is None:
            raise ExecuteError("No RPC configured for execution")
        nonce = int(self.rpc.call("eth_getTransactionCount", [self.signer.address, "latest"]), 16)
        head = int(self.rpc.call("eth_blockNumber", []), 16)
        block = self.rpc.call("eth_getBlockByNumber", [hex(head), False])
        base = int(block.get("baseFeePerGas", "0x1"), 16)
        priority = 10 ** 9  # 1 gwei
        max_fee = base * 2 + priority
        tx = {"chainId": chain_id, "nonce": nonce, "gas": 21000,
              "maxFeePerGas": max_fee, "maxPriorityFeePerGas": priority,
              "to": to, "value": value_wei, "data": "0x"}
        raw = self.signer.sign_transaction(tx)
        tx_hash = self.rpc.call("eth_sendRawTransaction", [raw])
        self.policy.record_spend(value_wei)
        return {"tx_hash": tx_hash, "chain_id": chain_id, "value_wei": str(value_wei),
                "from": self.signer.address, "to": to, "simulated": simulate_first}
