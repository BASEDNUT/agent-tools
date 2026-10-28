"""Behavioral wire tests for real adapters, offline fake RPC; zero fund movement."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.request
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from rootstock_tools.core import Toolchain,CapabilityError,CAPABILITIES
from rootstock_tools.mcp import Server,MODERN,LEGACY
from rootstock_tools.http_api import make_handler
from rootstock_tools.rpc import JsonRpc,CHAIN_CONFIG,ChainError,TOPIC_POOL_REGISTERED

B32='0x'+'3f'*32
T32='0x'+'af'*32
POOL='0x1234567890abcdef1234567890abcdef12345678'
FACTORY='0x9a5bd368c8da0d7fad33fc89b6be4e39e5a33f92'

def topic(addr):return '0x'+'0'*24+addr[2:].lower()

def log_event(factory=FACTORY,address=None,removed=False):
 return {'address':address or CHAIN_CONFIG[8453]['vault'],'removed':removed,
         'topics':[TOPIC_POOL_REGISTERED,topic(POOL),topic(factory)],
         'blockNumber':hex(52131552),'blockHash':B32,'transactionHash':T32,'logIndex':'0x0','data':'0x'}

class FakeRPC(BaseHTTPRequestHandler):
 chain=8453; logs=[]; invalid_id=False; requests=[]
 def log_message(self,*args): pass
 def do_POST(self):
  raw=self.rfile.read(int(self.headers['Content-Length']))
  req=json.loads(raw);type(self).requests.append(req)
  method=req['method'];params=req['params']
  result={'eth_chainId':hex(type(self).chain),'eth_blockNumber':hex(52131555),
   'eth_getBlockByNumber':{'hash':B32,'number':hex(52131555)},
   'eth_getLogs':type(self).logs,
   'eth_getCode':'0x6060'}.get(method)
  reply=json.dumps({'jsonrpc':'2.0','id':req['id']+1 if type(self).invalid_id else req['id'],'result':result}).encode()
  self.send_response(200);self.send_header('Content-Length',str(len(reply)));self.end_headers();self.wfile.write(reply)

class ServerContext:
 def __enter__(self):
  FakeRPC.chain=8453;FakeRPC.logs=[];FakeRPC.invalid_id=False;FakeRPC.requests=[]
  self.httpd=ThreadingHTTPServer(('127.0.0.1',0),FakeRPC)
  self.t=threading.Thread(target=self.httpd.serve_forever,daemon=True);self.t.start()
  return 'http://127.0.0.1:'+str(self.httpd.server_address[1])
 def __exit__(self,*args):self.httpd.shutdown();self.httpd.server_close();self.t.join()

class RPCSecurityTests(unittest.TestCase):
 def test_disallow_arbitrary_rpc_method(self):
  with ServerContext() as url:
   rpc=JsonRpc(url,8453,allow_local=True)
   with self.assertRaisesRegex(ChainError,'allowlist'):rpc.call('eth_sendRawTransaction',['0x1234'])
   self.assertEqual(FakeRPC.requests,[])
 def test_plain_http_requires_explicit_optin(self):
  with ServerContext() as url:
   with self.assertRaisesRegex(ChainError,'HTTPS'):JsonRpc(url,8453)
 def test_unsupported_chain_fails(self):
  with self.assertRaises(ChainError):JsonRpc('https://example.com',1)
 def test_live_head_hash_is_retained(self):
  with ServerContext() as url:
   r=JsonRpc(url,8453,allow_local=True).status()
   self.assertEqual(r['head_hash'],B32)
   self.assertEqual(r['chain_id'],8453)
 def test_chain_mismatch_blocks_event_query(self):
  with ServerContext() as url:
   FakeRPC.chain=1
   with self.assertRaisesRegex(ChainError,'chain mismatch'):
    JsonRpc(url,8453,allow_local=True).pool_events(52131550,52131555)
   self.assertEqual([x['method'] for x in FakeRPC.requests],['eth_chainId'])
 def test_pool_event_real_decoding_pipeline(self):
  with ServerContext() as url:
   FakeRPC.logs=[log_event()]
   result=JsonRpc(url,8453,allow_local=True).pool_events(52131550,52131555)
   ev=result['events'][0]
   self.assertEqual(ev['pool'].lower(),POOL)
   self.assertEqual(ev['factory'].lower(),FACTORY)
   self.assertEqual(ev['pool_math_type'],'WEIGHTED')
   self.assertEqual(ev['block_hash'],B32)
   self.assertFalse(result['independent_log_completeness_verified'])
   self.assertEqual(FakeRPC.requests[2]['params'][0]['address'].lower(),CHAIN_CONFIG[8453]['vault'].lower())
 def test_unknown_factory_cannot_be_guessed(self):
  with ServerContext() as url:
   FakeRPC.logs=[log_event(factory='0x'+'a'*40)]
   ev=JsonRpc(url,8453,allow_local=True).pool_events(52131550,52131555)['events'][0]
   self.assertEqual(ev['pool_math_type'],'UNKNOWN')
 def test_wrong_vault_and_removed_logs_rejected(self):
  with ServerContext() as url:
   rpc=JsonRpc(url,8453,allow_local=True)
   FakeRPC.logs=[log_event(address='0x'+'1'*40)]
   with self.assertRaisesRegex(ChainError,'Unexpected'):rpc.pool_events(52131550,52131555)
   FakeRPC.logs=[log_event(removed=True)]
   with self.assertRaisesRegex(ChainError,'reorged'):rpc.pool_events(52131550,52131555)
 def test_malformed_event_rejected(self):
  with ServerContext() as url:
   ev=log_event();ev['topics'][1]='0xbad'
   FakeRPC.logs=[ev]
   with self.assertRaisesRegex(ChainError,'Invalid event topic'):
    JsonRpc(url,8453,allow_local=True).pool_events(52131550,52131555)
 def test_oversize_window_blocks_before_logs(self):
  with ServerContext() as url:
   with self.assertRaisesRegex(ChainError,'2000 blocks'):
    JsonRpc(url,8453,allow_local=True).pool_events(1,100000)
   self.assertEqual(FakeRPC.requests,[])
 def test_unexpected_rpc_id_blocks(self):
  with ServerContext() as url:
   FakeRPC.invalid_id=True
   with self.assertRaisesRegex(ChainError,'identity mismatch'):
    JsonRpc(url,8453,allow_local=True).status()
 def test_rpc_status_does_not_leak_secret_endpoint(self):
  with ServerContext() as url:
   status=JsonRpc(url+'/tenant/private?key=SECRET',8453,allow_local=True).status()
   self.assertNotIn('SECRET',json.dumps(status))
   self.assertEqual(status['rpc_host'],'127.0.0.1')
 def test_future_window_rejected(self):
  with ServerContext() as url:
   with self.assertRaisesRegex(ChainError,'beyond current'):
    JsonRpc(url,8453,allow_local=True).pool_events(52131554,52131560)
   self.assertFalse(any(q['method']=='eth_getLogs' for q in FakeRPC.requests))
 def test_no_untrusted_redirect(self):
  with self.assertRaisesRegex(ChainError,'HTTPS'):
   JsonRpc('http://169.254.169.254/latest/meta-data',8453)

class SurfaceTests(unittest.TestCase):
 @staticmethod
 def modern(method,params=None,identifier=1):
  return {'jsonrpc':'2.0','id':identifier,'method':method,'params':{'_meta':{
   'io.modelcontextprotocol/protocolVersion':MODERN,
   'io.modelcontextprotocol/clientCapabilities':{}},**(params or {})}}
 def setUp(self):self.s=Server(Toolchain())
 def test_modern_discover(self):
  r=self.s._respond(self.modern('server/discover'))['result']
  self.assertIn('2026-07-28',r['supportedVersions'])
  self.assertEqual(r['resultType'],'complete')
 def test_modern_tools_readonly(self):
  r=self.s._respond(self.modern('tools/list'))['result']
  self.assertEqual(len(r['tools']),len(CAPABILITIES))
  self.assertTrue(all(t['annotations']['readOnlyHint'] for t in r['tools']))
  self.assertFalse(any('execute' in t['name'] or 'sign' in t['name'] for t in r['tools']))
 def test_tool_call_real_shared_sdk(self):
  r=self.s._respond(self.modern('tools/call',{'name':'registry.list_networks','arguments':{}}))['result']
  self.assertFalse(r['isError'])
  self.assertEqual(len(r['structuredContent']['data']),2)
 def test_skills_as_resources(self):
  r=self.s._respond(self.modern('resources/list'))['result']
  self.assertEqual(len(r['resources']),1+len(self.s.tools.run('skills.list')))
  res=self.s._respond(self.modern('resources/read',{'uri':'rootstock://skills/rootstock-agent-security'}))['result']
  self.assertIn('rootstock',res['contents'][0]['text'].lower())
 def test_bad_tool_name_does_not_execute(self):
  r=self.s._respond(self.modern('tools/call',{'name':'transactions.execute','arguments':{}}))
  self.assertEqual(r['error']['code'],-32602)
 def test_untrusted_param_not_accepted(self):
  r=self.s._respond(self.modern('tools/call',{'name':'registry.resolve_deployment','arguments':{'chain_id':8453,'name':'Router','execute':True}}))['result']
  self.assertTrue(r['isError'])
 def test_bad_modern_metadata_rejected(self):
  r=self.s._respond({'jsonrpc':'2.0','id':1,'method':'tools/list', 'params':{'_meta':{'io.modelcontextprotocol/protocolVersion':MODERN}}})
  self.assertEqual(r['error']['code'],-32602)
 def test_legacy_must_initialize_first(self):
  s=Server(Toolchain())
  r=s._respond({'jsonrpc':'2.0','id':9,'method':'tools/list','params':{}})
  self.assertEqual(r['error']['code'],-32600)
 def test_legacy_initialize(self):
  r=self.s._respond({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':LEGACY}})['result']
  self.assertEqual(r['protocolVersion'],LEGACY)
  legacy=self.s._respond({'jsonrpc':'2.0','id':2,'method':'tools/list','params':{}})['result']
  self.assertNotIn('resultType',legacy)
 def test_notification_has_no_response(self):
  self.assertIsNone(self.s._respond({'jsonrpc':'2.0','method':'notifications/initialized'}))
 def test_stdio_frame_output_json_only(self):
  inp=io.StringIO(json.dumps(self.modern('tools/list'))+'\nnotjson\n')
  out=io.StringIO();self.s.serve(inp,out)
  lines=[json.loads(x) for x in out.getvalue().splitlines()]
  self.assertEqual(len(lines),2)
  self.assertEqual(lines[1]['error']['code'],-32700)
 def test_mcp_subprocess(self):
  env=dict(os.environ,PYTHONPATH=str(ROOT/'src'))
  x=json.dumps(self.modern('server/discover'))+'\n'+json.dumps(self.modern('tools/list',identifier=2))+'\n'
  p=subprocess.run([sys.executable,'-m','rootstock_tools','mcp'],input=x,env=env,capture_output=True,text=True,timeout=8)
  self.assertEqual(p.returncode,0,p.stderr)
  res=[json.loads(l) for l in p.stdout.splitlines()]
  self.assertEqual(res[1]['result']['tools'][0]['name'],sorted(CAPABILITIES)[0])
 def test_cli_install_skills_requires_explicit_target(self):
  with tempfile.TemporaryDirectory() as tmp:
   target=Path(tmp)/'skills'
   env=dict(os.environ,PYTHONPATH=str(ROOT/'src'))
   cmd=[sys.executable,'-m','rootstock_tools','skills','install','--target',str(target)]
   p=subprocess.run(cmd,env=env,text=True,capture_output=True,timeout=7)
   self.assertEqual(p.returncode,0,p.stderr)
   self.assertEqual(len(list(target.glob('*/SKILL.md'))),20)
   p2=subprocess.run(cmd,env=env,text=True,capture_output=True,timeout=7)
   self.assertEqual(p2.returncode,2)
   self.assertIn('Refusing existing destination',p2.stderr)
 def test_sdk_argument_types(self):
  with self.assertRaises(CapabilityError):self.s.tools.run('pools.list',{'chain_id':True,'from_block':1,'to_block':2})
 def test_http_read_only(self):
  api=ThreadingHTTPServer(('127.0.0.1',0),make_handler(Toolchain()))
  t=threading.Thread(target=api.serve_forever,daemon=True);t.start()
  base='http://127.0.0.1:'+str(api.server_address[1])
  try:
   with urllib.request.urlopen(base+'/v1/capabilities',timeout=3) as r:
    result=json.loads(r.read());self.assertTrue(result['ok']);self.assertEqual(len(result['result']),len(CAPABILITIES))
   with self.assertRaises(urllib.error.HTTPError) as ctx:
    urllib.request.urlopen(urllib.request.Request(base+'/v1/networks',method='POST'),timeout=3)
   self.assertEqual(ctx.exception.code,405)
  finally:api.shutdown();api.server_close();t.join()

if __name__=='__main__':unittest.main()
