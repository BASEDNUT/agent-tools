"""S113-fix superseded guard: dead deployments must never resolve, whatever the registry claims.
Offline deterministic tests. The 11 superseded addresses are hardcoded defense-in-depth;
the registry-declared 'superseded' map is validated and enforced at resolution time.
"""
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
from rootstock_tools.registry import (
    CANONICAL_BLOBS,
    KNOWN_SUPERSEDED,
    RegistryError,
    git_blob_sha,
    load_registry,
)

FIX = ROOT / "tests" / "fixtures"

# The pinned canonical blobs after the S113-fix registry sync (monorepo commit
# 6206c91643e2e87c43164be90f963c91a11329ab, pushed 2026-10-28).
REPINNED_BLOBS = {
    "base.json": "3999774121968bef9f6d5abca9748a4c62b14f10",
    "base-sepolia.json": "825ecb8dedab18d5867068572bd82cd85adceed7",
}


class SupersededGuardTests(unittest.TestCase):
    def registry(self, name="base.json"):
        return load_registry(FIX / name, allow_unpinned=True)

    def mutation(self, change, filename="base.json"):
        data = json.loads((FIX / filename).read_text())
        change(data)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / filename
            path.write_text(json.dumps(data))
            return load_registry(path, allow_unpinned=True)

    def test_canonical_blobs_are_the_s113fix_synced_pins(self):
        self.assertEqual(CANONICAL_BLOBS, REPINNED_BLOBS)

    def test_known_superseded_covers_all_eleven_s113fix_addresses(self):
        expected = 7 + 4  # mainnet 7, sepolia 4
        self.assertEqual(len(KNOWN_SUPERSEDED), expected)

    def test_fixture_superseded_map_parsed_and_exposed(self):
        reg = self.registry()
        self.assertTrue(reg.superseded)
        old = "0xb3D9A369B6b7a354Ccb81c68b975830103AeBd59"
        self.assertTrue(reg.is_superseded(old))
        self.assertEqual(reg.superseded[old.lower()]["name"], "TokenPairRegistry")
        # the live replacement resolves, the dead one is not in tasks
        live = reg.resolve("TokenPairRegistry")
        self.assertEqual(live["address"].lower(), "0x0253c3996d1f21f3c064d67a6c9c496f45fa3dc5")
        self.assertNotIn(old.lower(), {a.lower() for cs in reg.tasks.values() for a in cs.values()})

    def test_registry_declared_superseded_never_resolves(self):
        # A registry that still lists a superseded address under a canonical name
        # must refuse resolution even though the map declares it dead.
        dead = "0x" + "1" * 40

        def change(x):
            # adversarial shape: dead address re-listed under a second task while
            # the map declares it superseded by the live (still deployed) replacement
            x["tasks"]["v3/tasks/test-dead-restore"] = {"TokenPairRegistry": dead}
            x["superseded"] = {
                dead: {
                    "name": "TokenPairRegistry",
                    "task": "v3/tasks/test-dead-restore",
                    "superseded_by": "0x0253c3996d1F21F3C064D67a6c9c496F45fA3Dc5",
                    "reason": "test: declared superseded yet still listed",
                    "never_use": True,
                }
            }

        reg = self.mutation(change)
        self.assertTrue(reg.is_superseded(dead))
        with self.assertRaisesRegex(RegistryError, "SUPERSEDED"):
            reg.resolve("TokenPairRegistry")

    def test_known_superseded_address_fails_load_closed(self):
        def change(x):
            x["tasks"]["v3/tasks/20250806-v3-token-pair-registry"]["TokenPairRegistry"] = (
                "0xb3D9A369B6b7a354Ccb81c68b975830103AeBd59"
            )

        with self.assertRaisesRegex(RegistryError, "known-superseded"):
            self.mutation(change)

    def test_sepolia_known_superseded_address_fails_load_closed(self):
        def change(x):
            x["tasks"]["v3/tasks/20250530-v3-cow-swap-fee-burner-v2"]["CowSwapFeeBurner"] = (
                "0xF51Efd4762d5EbdCBa49472C266A5c37dC4ddD5a"
            )

        with self.assertRaisesRegex(RegistryError, "known-superseded"):
            self.mutation(change, "base-sepolia.json")

    def test_superseded_by_must_exist_in_tasks(self):
        def change(x):
            x["superseded"]["0x" + "2" * 40] = {
                "name": "Ghost",
                "superseded_by": "0x" + "3" * 40,
                "never_use": True,
            }

        with self.assertRaisesRegex(RegistryError, "superseded_by"):
            self.mutation(change)

    def test_superseded_map_shape_validated(self):
        def change(x):
            x["superseded"]["not-an-address"] = {"never_use": True}

        with self.assertRaisesRegex(RegistryError, "superseded"):
            self.mutation(change)

    def test_live_replacement_resolves_on_both_fixture_chains(self):
        reg = self.registry("base-sepolia.json")
        live = reg.resolve("TokenPairRegistry")
        self.assertEqual(live["address"].lower(), "0x54d1e9eac2eaf5faba009dc5dc80dc24dc1957c0")
        old = "0x43DBB8F3bb9f6277e350f37Adf240518c0964f06"
        self.assertTrue(reg.is_superseded(old))

    def cli(self, *args):
        env = dict(os.environ, PYTHONPATH=str(SRC))
        return subprocess.run(
            [sys.executable, "-m", "rootstock_tools", "--allow-unpinned", "--registry-dir", str(FIX), *args],
            env=env, capture_output=True, text=True,
        )

    def test_cli_resolves_live_replacement(self):
        proc = self.cli("resolve", "--chain", "8453", "--name", "TokenPairRegistry")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)["result"]
        self.assertEqual(result["address"].lower(), "0x0253c3996d1f21f3c064d67a6c9c496f45fa3dc5")


if __name__ == "__main__":
    unittest.main()
