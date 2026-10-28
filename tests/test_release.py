"""Integrity, bundling and source-download policy checks. All tests offline."""
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
import sys
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from rootstock_tools import Toolchain,CAPABILITIES
from rootstock_tools.registry import git_blob_sha,RegistryError
from rootstock_tools import bootstrap
from rootstock_tools.http_api import OPENAPI

class MockResponse:
 def __init__(self,data):self.data=data
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def read(self,limit):return self.data

class MockOpener:
 def __init__(self,documents):self.documents=documents
 def open(self,request,timeout):return MockResponse(self.documents[request.full_url.split('/')[-1]])

class ReleaseTests(unittest.TestCase):
 def test_skills_bundled_byte_identical_to_authored(self):
  for src in sorted((ROOT/'skills').glob('*/SKILL.md')):
   dest=ROOT/'src/rootstock_tools/bundled_skills'/src.parent.name/'SKILL.md'
   self.assertEqual(src.read_bytes(),dest.read_bytes(),str(src))
  self.assertEqual(len(Toolchain().run('skills.list')),20)
 def test_capabilities_manifest_matches_code(self):
  manifest=json.loads((ROOT/'schemas/capability-manifest.json').read_text())
  self.assertEqual(manifest['capabilities'],Toolchain().run('capabilities.list'))
  self.assertEqual(len(manifest['capabilities']),len(CAPABILITIES))
 def test_openapi_manifest_matches_code(self):
  spec=json.loads((ROOT/'schemas/openapi-readonly.json').read_text())
  self.assertEqual(spec,OPENAPI)
 def test_bootstrap_validates_bytes_before_writes(self):
  docs={'base.json':b'{"demo":"base"}\n','base-sepolia.json':b'{"demo":"sep"}\n'}
  pins={k:git_blob_sha(v) for k,v in docs.items()}
  with tempfile.TemporaryDirectory() as td,patch.object(bootstrap,'CANONICAL_BLOBS',pins),patch.object(bootstrap,'build_opener',return_value=MockOpener(docs)):
   res=bootstrap.fetch_registries(Path(td))
   self.assertTrue(res['verified_against_pinned_blobs'])
   self.assertEqual((Path(td)/'base.json').read_bytes(),docs['base.json'])
 def test_bootstrap_bad_blob_rolls_back_all(self):
  docs={'base.json':b'good','base-sepolia.json':b'bad'}
  pins={'base.json':git_blob_sha(docs['base.json']),'base-sepolia.json':git_blob_sha(b'expected')}
  with tempfile.TemporaryDirectory() as td,patch.object(bootstrap,'CANONICAL_BLOBS',pins),patch.object(bootstrap,'build_opener',return_value=MockOpener(docs)):
   with self.assertRaisesRegex(RegistryError,'does not match'):
    bootstrap.fetch_registries(Path(td))
   self.assertEqual(list(Path(td).iterdir()),[])
 def test_bootstrap_conflict_does_not_write_other_file(self):
  docs={'base.json':b'ok','base-sepolia.json':b'ok2'}
  pins={k:git_blob_sha(v) for k,v in docs.items()}
  with tempfile.TemporaryDirectory() as td,patch.object(bootstrap,'CANONICAL_BLOBS',pins),patch.object(bootstrap,'build_opener',return_value=MockOpener(docs)):
   (Path(td)/'base-sepolia.json').write_bytes(b'conflict')
   with self.assertRaisesRegex(RegistryError,'Refusing to overwrite'):
    bootstrap.fetch_registries(Path(td))
   self.assertFalse((Path(td)/'base.json').exists())
 def test_no_transaction_capabilities(self):
  self.assertFalse(any(x in CAPABILITIES for x in ('transactions.execute','transactions.broadcast','wallet.sign','wallet.approve')))
  with self.assertRaises(Exception):Toolchain().run('transactions.execute',{})

if __name__=='__main__':unittest.main()
