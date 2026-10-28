"""Deterministic/offline tests: not live-chain checks and not a security certification."""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))
from rootstock_tools.registry import (CANONICAL_BLOBS, RegistryError, git_blob_sha, load_registry)

FIX = ROOT / "tests" / "fixtures"


class RegistryTests(unittest.TestCase):
    def registry(self, name="base.json"):
        return load_registry(FIX / name, allow_unpinned=True)

    def test_chain_mainnet(self):
        self.assertEqual(self.registry().chain_id, 8453)

    def test_chain_sepolia(self):
        self.assertEqual(self.registry("base-sepolia.json").chain_id, 84532)

    def test_known_mainnet_vault(self):
        self.assertEqual(self.registry().resolve("Vault")["address"].lower(), "0x0a3af0da0175afa0cc05a6ad9092dc740155a0e7")

    def test_known_sepolia_router(self):
        self.assertEqual(self.registry("base-sepolia.json").resolve("Router")["address"].lower(), "0xdd9793cd4b79a8bd65d690c64a3074d023dfa759")

    def test_same_address_repeated_tasks_is_not_ambiguous(self):
        res = self.registry("base-sepolia.json").resolve("Vault")
        self.assertEqual(len(res["tasks"]), 2)

    def test_same_name_distinct_addresses_is_ambiguous(self):
        with self.assertRaisesRegex(RegistryError, "Ambiguous"):
            self.registry().resolve("StablePoolFactory")

    def test_legacy_factory_disambiguation(self):
        old = self.registry().resolve("StablePoolFactory", "v3/deprecated/20250324-v3-stable-pool-v2")
        active = self.registry().resolve("StablePoolFactory", "v3/tasks/20260116-v3-stable-pool-v3")
        self.assertNotEqual(old["address"].lower(), active["address"].lower())

    def test_unknown_name_rejected(self):
        with self.assertRaisesRegex(RegistryError, "Not found"):
            self.registry().resolve("MadeUpContract")

    def test_blank_name_rejected(self):
        with self.assertRaisesRegex(RegistryError, "name required"):
            self.registry().resolve("  ")

    def test_nonexistent_task_rejected(self):
        with self.assertRaisesRegex(RegistryError, "Not found"):
            self.registry().resolve("Vault", "v3/not-a-real-task")

    def test_upstream_balancer_router_not_rootstock_router(self):
        # Upstream SDK v6.2.0 address was inspected at `balancerV3Contracts.ts`.
        upstream_balancer_router_on_base = "0x3f170631ed9821ca51a59d996aB095162438DC10"
        self.assertNotEqual(self.registry().resolve("Router")["address"].lower(), upstream_balancer_router_on_base.lower())

    def test_pin_rejects_excerpt(self):
        with self.assertRaisesRegex(RegistryError, "pinned canonical"):
            load_registry(FIX / "base.json")

    def test_git_blob_hash_algorithm(self):
        self.assertEqual(git_blob_sha(b"hello\n"), "ce013625030ba8dba906f756967f9e9ca394464a")

    def test_pinned_hash_is_sha1_shape(self):
        for v in CANONICAL_BLOBS.values():
            self.assertRegex(v, r"^[a-f0-9]{40}$")

    def mutation(self, change, filename="base.json"):
        data = json.loads((FIX / filename).read_text())
        change(data)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / filename
            path.write_text(json.dumps(data))
            return load_registry(path, allow_unpinned=True)

    def test_reject_chain_mismatch(self):
        with self.assertRaisesRegex(RegistryError, "Chain ID mismatch"):
            self.mutation(lambda x: x.update(chainId=1))

    def test_reject_network_mismatch(self):
        with self.assertRaisesRegex(RegistryError, "Network label mismatch"):
            self.mutation(lambda x: x.update(network="ethereum"))

    def test_reject_non_contract_address(self):
        def corruption(x):
            x["tasks"]["v3/tasks/20250307-v3-router-v2"]["Router"] = "0xdeadbeef"
        with self.assertRaisesRegex(RegistryError, "Invalid deployment"):
            self.mutation(corruption)

    def test_reject_missing_tasks(self):
        with self.assertRaisesRegex(RegistryError, "No deployment"):
            self.mutation(lambda x: x.update(tasks={}))

    def test_zero_address_not_resolvable(self):
        def zero(x):
            x["tasks"]["v3/tasks/20250307-v3-router-v2"]["Router"] = "0x" + "0"*40
        reg = self.mutation(zero)
        with self.assertRaisesRegex(RegistryError, "Not found"):
            reg.resolve("Router")

    def test_boolean_chain_rejected(self):
        with self.assertRaisesRegex(RegistryError, "Chain ID mismatch"):
            self.mutation(lambda x: x.update(chainId=True))

    def cli(self, *args):
        env = dict(os.environ, PYTHONPATH=str(SRC))
        return subprocess.run([sys.executable, "-m", "rootstock_tools", "--registry-dir", str(FIX), *args], env=env, capture_output=True, text=True)

    def test_cli_default_fails_closed(self):
        # Network identities can be read offline; deployment resolution requires pinned bytes.
        proc = self.cli("resolve", "--chain", "8453", "--name", "Router")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("pinned canonical", proc.stderr)

    def test_cli_networks_demo(self):
        proc = self.cli("--allow-unpinned", "networks")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        r = json.loads(proc.stdout)
        self.assertEqual({v["chain_id"] for v in r["result"]}, {8453, 84532})
        self.assertTrue(all(v["source_pinned"] is False and v["onchain_code_verified"] is False for v in r["result"]))

    def test_cli_ambiguous_refuses(self):
        proc = self.cli("--allow-unpinned", "resolve", "--chain", "8453", "--name", "StablePoolFactory")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("Ambiguous", proc.stderr)

    def test_cli_targeted_resolve(self):
        proc = self.cli("--allow-unpinned", "resolve", "--chain", "8453", "--name", "StablePoolFactory", "--task", "v3/tasks/20260116-v3-stable-pool-v3")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["result"]["name"], "StablePoolFactory")

    def test_cli_no_execution_surface(self):
        proc = self.cli("--allow-unpinned", "swap", "--chain", "8453")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("invalid choice", proc.stderr)


if __name__ == "__main__":
    unittest.main()
