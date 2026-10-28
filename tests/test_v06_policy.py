import json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from rootstock_tools.policy import PolicyGate,PolicyError
from rootstock_tools.core import Toolchain
class PolicyTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'policy.json'
  self.path.write_text(json.dumps({'version':1,'agents':{'reader':{'allow':['registry.*','capabilities.list'], 'chains':[8453]}}}))
 def tearDown(self):self.tmp.cleanup()
 def test_http_shared_read_calls_respect_policy(self):
  import threading,urllib.request,urllib.error
  from http.server import ThreadingHTTPServer
  from rootstock_tools.http_api import make_handler
  kit=Toolchain(policy_file=self.path,agent_id='reader')
  api=ThreadingHTTPServer(('127.0.0.1',0),make_handler(kit));worker=threading.Thread(target=api.serve_forever,daemon=True);worker.start()
  base='http://127.0.0.1:'+str(api.server_address[1])+'/v1/tools/call'
  def req(name,args):
   return urllib.request.Request(base,data=json.dumps({'name':name,'arguments':args}).encode(),headers={'Content-Type':'application/json'})
  try:
   with urllib.request.urlopen(req('registry.list_networks',{}),timeout=3) as r:
    self.assertEqual(len(json.load(r)['result']),2)
   with self.assertRaises(urllib.error.HTTPError) as e:
    urllib.request.urlopen(req('policy.evaluate',{'chain_id':8453,'action':'execute'}),timeout=3)
   self.assertEqual(e.exception.code,400)
  finally:api.shutdown();api.server_close();worker.join()
 def test_known_agent_allowed_exact_and_prefix(self):
  kit=Toolchain(policy_file=self.path,agent_id='reader')
  self.assertIsInstance(kit.run('capabilities.list'),list)
  self.assertEqual(len(kit.run('registry.list_networks')),2)
 def test_absent_agent_rejected(self):
  with self.assertRaises(PolicyError):Toolchain(policy_file=self.path,agent_id='admin')
 def test_denies_unlisted_analytics_and_other_chains(self):
  kit=Toolchain(policy_file=self.path,agent_id='reader')
  with self.assertRaises(PolicyError):kit.run('analytics.tvl',{'chain_id':8453})
  with self.assertRaises(PolicyError):kit.run('registry.resolve_deployment',{'chain_id':84532,'name':'Vault'})
 def test_duplicate_json_keys_rejected(self):
  self.path.write_text('{"version":1,"version":1,"agents":{}}')
  with self.assertRaises(PolicyError):PolicyGate(self.path,'reader')
 def test_unbounded_wildcard_denied(self):
  self.path.write_text(json.dumps({'version':1,'agents':{'reader':{'allow':['*'],'chains':[8453]}}}))
  with self.assertRaises(PolicyError):PolicyGate(self.path,'reader')
 def test_symlink_policy_denied(self):
  link=Path(self.tmp.name)/'link.json';link.symlink_to(self.path)
  with self.assertRaises(PolicyError):PolicyGate(link,'reader')
 def test_no_exec_even_permitted_name_in_manifest(self):
  self.path.write_text(json.dumps({'version':1,'agents':{'reader':{'allow':['transactions.execute'],'chains':[8453]}}}))
  with self.assertRaises(Exception):Toolchain(policy_file=self.path,agent_id='reader').run('transactions.execute',{})
if __name__=='__main__':unittest.main()
