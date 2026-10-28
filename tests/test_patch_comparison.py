"""Test the diff parser and failure modes against curated excerpts, not a full pinned patch."""
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
sys.path.insert(0,str(ROOT/'src'))
from check_sdk_patch import extract_entries, compare
from rootstock_tools.registry import load_registry, RegistryError

PAT = '''diff --git a/dist/index.js b/dist/index.js
@@ -1,3 +1,4 @@
   Router: {
+    [8453 /* BASE */]: "0xc8dcC030C81635Da8df2D7fb35573E661B01cDCe",
+    [84532 /* BASE_SEPOLIA */]: "0xDD9793Cd4B79a8bd65D690C64A3074D023Dfa759",
diff --git a/dist/index.mjs b/dist/index.mjs
@@ -1,3 +1,4 @@
   Router: {
+    [8453 /* BASE */]: "0xc8dcC030C81635Da8df2D7fb35573E661B01cDCe",
+    [84532 /* BASE_SEPOLIA */]: "0xDD9793Cd4B79a8bd65D690C64A3074D023Dfa759",
'''

class PatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.regs = {8453:load_registry(ROOT/'tests/fixtures/base.json',allow_unpinned=True),84532:load_registry(ROOT/'tests/fixtures/base-sepolia.json',allow_unpinned=True)}
    def test_extract_both_bundles(self):
        arr=extract_entries(PAT)
        self.assertEqual(len(arr),4)
        self.assertEqual({e['file'] for e in arr},{'dist/index.js','dist/index.mjs'})
    def test_all_matches(self):
        r=compare(extract_entries(PAT),self.regs)
        self.assertTrue(r['ok'])
        self.assertEqual((r['checked_entries'],r['matches'],r['unique_chain_contracts']),(4,4,2))
    def test_wrong_address_rejected(self):
        modified=PAT.replace('0xc8dcC030C81635Da8df2D7fb35573E661B01cDCe','0x'+'1'*40)
        r=compare(extract_entries(modified),self.regs)
        self.assertFalse(r['ok'])
        self.assertEqual(len(r['mismatches']),2)
    def test_bundle_divergence_rejected(self):
        modified=PAT.replace('0xDD9793Cd4B79a8bd65D690C64A3074D023Dfa759','0x'+'1'*40,1)
        r=compare(extract_entries(modified),self.regs)
        self.assertFalse(r['ok'])
        self.assertTrue(r['bundle_divergences'])
    def test_no_address_fails_closed(self):
        with self.assertRaisesRegex(RegistryError,'No patched'):
            compare(extract_entries('diff --git a/x b/x'),self.regs)
    def test_unattributed_address_fails_closed(self):
        with self.assertRaisesRegex(RegistryError,'Unattributed'):
            extract_entries('diff --git a/a b/a\n+    [8453 /* BASE */]: "0x'+'1'*40+'",')

if __name__=='__main__':unittest.main()
