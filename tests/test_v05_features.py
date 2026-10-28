"""Local real-code tests: ABI codec, SQLite chain-index, SDK, API and MCP parity."""
import io,json,os,sys,tempfile,unittest,threading,urllib.request,urllib.error
from pathlib import Path
from http.server import ThreadingHTTPServer
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from rootstock_tools.evm import keccak256,selector,decode_addresses,decode_dynamic_uint_array,addr_word,word
from rootstock_tools.indexer import EventIndex, TOPICS,decode_logs
from rootstock_tools.rpc import CHAIN_CONFIG,ChainError
from rootstock_tools.core import Toolchain,CAPABILITIES,CapabilityError
from rootstock_tools.http_api import make_handler
from rootstock_tools.mcp import Server,MODERN

CHAIN=8453;VAULT=CHAIN_CONFIG[CHAIN]['vault'];POOL='0x'+'a'*40;FACTORY='0x9a5bd368c8da0d7fad33fc89b6be4e39e5a33f92'
T1='0x'+'1'*40;T2='0x'+'2'*40;WALLET='0x'+'3'*40
B32='0x'+'b'*64;TX='0x'+'c'*64

def swap_log(number=52131550,idx=0):
 return {'address':VAULT,'topics':[TOPICS['Swap'],'0x'+addr_word(POOL),'0x'+addr_word(T1),'0x'+addr_word(T2)],
   'data':'0x'+''.join(word(n) for n in (100000,99000,10**15,100)),
   'blockNumber':hex(number),'transactionHash':TX,'blockHash':B32,'logIndex':hex(idx),'removed':False}

def pool_log(number=52131550,idx=1):
 return {'address':VAULT,'topics':[TOPICS['PoolRegistered'],'0x'+addr_word(POOL),'0x'+addr_word(FACTORY)],
   'data':'0x','blockNumber':hex(number),'transactionHash':TX,'blockHash':B32,'logIndex':hex(idx),'removed':False}

def dynamic_addresses(addrs):
 return '0x'+word(32)+word(len(addrs))+''.join(addr_word(a) for a in addrs)

def pool_info_blob(addrs,balances):
 # Tuple outputs: address[], (uint8,address,bool)[], uint256[], uint256[]
 chunks=[];o=128
 # array of addresses
 for b in (word(len(addrs))+''.join(addr_word(a) for a in addrs),
           word(len(addrs))+''.join(word(0)+addr_word('0x'+'0'*40)+word(0) for _ in addrs),
           word(len(balances))+''.join(word(x) for x in balances),
           word(len(balances))+''.join(word(x) for x in balances)):
  chunks.append((o,b));o+=len(b)//2
 return '0x'+''.join(word(o) for o,b in chunks)+''.join(b for o,b in chunks)

class FauxRpc:
 def __init__(self,chain=CHAIN):self.chain_id=chain;self.logs=[pool_log(),swap_log()];self.hash=B32;self.calls=[];self.chain_bad=False
 def check_chain(self):
  if self.chain_bad:raise ChainError('chain mismatch')
 def call(self,method,params):
  self.calls.append((method,params))
  if method=='eth_blockNumber':return hex(52131557)
  if method=='eth_getBlockByNumber':return {'number':params[0],'hash':self.hash}
  if method=='eth_getLogs':
   a,b=(int(params[0][x],16) for x in ('fromBlock','toBlock'))
   return [e for e in self.logs if a<=int(e['blockNumber'],16)<=b]
  if method=='eth_getCode':return '0x6000'
  if method=='eth_getTransactionReceipt':return {'status':'0x1','blockNumber':hex(52131555),'blockHash':B32}
  if method=='eth_call':
   sig=params[0]['data'][:10]
   if sig==selector('getPoolTokens(address)'):return dynamic_addresses([T1,T2])
   if sig==selector('querySwapSingleTokenExactIn(address,address,address,uint256,address,bytes)'):return '0x'+word(999)
   if sig==selector('getPoolTokenInfo(address)'):return pool_info_blob([T1,T2],[10**18,20**18])
   if sig==selector('balanceOf(address)'):return '0x'+word(500)
   if sig==selector('totalSupply()'):return '0x'+word(1000)
   if sig==selector('decimals()'):return '0x'+word(18)
   if sig==selector('asset()'):return '0x'+addr_word(T2)
   if sig in (selector('name()'),selector('symbol()')):
    b=b'TKN' if sig==selector('symbol()') else b'Test'
    return '0x'+word(32)+word(len(b))+(b.hex().ljust(64,'0'))
   return '0x'
  raise AssertionError(method)

class EvmAndEventTests(unittest.TestCase):
 def test_keccak_matches_known_evm(self):
  self.assertEqual(keccak256(b'').hex(),'c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470')
  self.assertEqual(selector('transfer(address,uint256)'),'0xa9059cbb')
  self.assertEqual(selector('getPoolTokens(address)'),'0xca4f2803')
 def test_abi_pool_arrays(self):
  self.assertEqual(decode_addresses(dynamic_addresses([T1,T2])),[T1,T2])
  self.assertEqual(decode_dynamic_uint_array(pool_info_blob([T1,T2],[2,3]),2),[2,3])
 def test_reject_corrupt_abi(self):
  with self.assertRaises(ChainError):decode_addresses('0x'+word(33)+word(5))
  with self.assertRaises(ChainError):decode_dynamic_uint_array('0x'+word(0xffffffff),0)
 def test_swap_event_decoded_in_raw_units(self):
  x=decode_logs([swap_log()],CHAIN,52131550,52131550)[0]
  self.assertEqual(x['amount_in_raw'],'100000')
  self.assertEqual(x['swap_fee_amount_raw'],'100')
 def test_event_reject_wrong_vault_and_log_identity(self):
  x=swap_log();x['address']=T1
  with self.assertRaises(ChainError):decode_logs([x],CHAIN,52131550,52131550)
  with self.assertRaisesRegex(ChainError,'Duplicate'):decode_logs([swap_log(),swap_log()],CHAIN,52131550,52131550)
 def test_pool_identity_from_real_registry_mapping(self):
  self.assertEqual(decode_logs([pool_log()],CHAIN,52131550,52131550)[0]['pool_math_type'],'WEIGHTED')
 def test_invalid_liquidity_event_fails_closed(self):
  ev=pool_log();ev['topics'][0]=TOPICS['LiquidityAdded'];ev['topics'].append('0x'+word(1))
  with self.assertRaises(ChainError):decode_logs([ev],CHAIN,52131550,52131550)

class IndexAndSDKTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.db=Path(self.temp.name)/'index.sqlite3';self.rpc=FauxRpc()
  self.kit=Toolchain(index_path=self.db,allow_local_rpc=True)
  self.kit._rpc=lambda chain:self.rpc
 def tearDown(self):self.temp.cleanup()
 def test_index_sync_and_raw_fee_analytics(self):
  res=self.kit.index.sync(self.rpc,52131550,52131551)
  self.assertEqual(res['events_seen'],2)
  got=self.kit.run('history.events',{'chain_id':CHAIN})
  self.assertEqual(len(got['events']),2)
  stats=self.kit.run('analytics.volume_fees',{'chain_id':CHAIN})
  self.assertEqual(stats['input_volume_raw_by_token'][T1.lower()],'100000')
  self.assertEqual(stats['swap_fee_raw_by_token'][T1.lower()],'100')
  self.assertIsNone(stats['usd_volume'])
 def test_index_rescan_clears_stale_events(self):
  self.kit.index.sync(self.rpc,52131550,52131551)
  self.rpc.logs=[]
  self.kit.index.sync(self.rpc,52131550,52131551)
  self.assertEqual(len(self.kit.run('history.events',{'chain_id':CHAIN})['events']),0)
 def test_index_reorg_detection_and_rollback(self):
  self.kit.index.sync(self.rpc,52131550,52131551)
  self.rpc.hash='0x'+'d'*64;self.rpc.logs=[]
  res=self.kit.index.sync(self.rpc,52131550,52131551)
  self.assertEqual(res['rewound_from'],52131550)
  self.assertEqual(len(self.kit.run('history.events',{'chain_id':CHAIN})['events']),0)
 def test_index_on_remote_failure_rolls_back(self):
  self.kit.index.sync(self.rpc,52131550,52131551)
  orig=self.rpc.call
  def fail(method,params):
   if method=='eth_getLogs':raise ChainError('Provider outage')
   return orig(method,params)
  self.rpc.call=fail
  with self.assertRaises(ChainError):self.kit.index.sync(self.rpc,52131550,52131551)
  self.assertEqual(len(self.kit.run('history.events',{'chain_id':CHAIN})['events']),2)
 def test_pool_inspect_and_token_metadata(self):
  r=self.kit.run('pools.inspect',{'chain_id':CHAIN,'pool':POOL})
  self.assertEqual(len(r['tokens']),2)
  self.assertEqual(r['tokens'][0]['balance_raw'],str(10**18))
  self.assertEqual(r['tokens'][0]['decimals'],18)
  self.assertIsNone(r['tvl_usd'])
 def test_direct_pool_quote_uses_pinned_router_and_never_signs(self):
  from unittest.mock import patch
  from rootstock_tools.registry import CANONICAL_BLOBS,git_blob_sha
  self.kit.registry_dir=ROOT/'tests/fixtures'
  path=self.kit.registry_dir/'base.json'
  with patch.dict(CANONICAL_BLOBS,{'base.json':git_blob_sha(path.read_bytes())}):
   r=self.kit.run('quotes.swap',{'chain_id':CHAIN,'pool':POOL,'token_in':T1,'token_out':T2,'amount_raw':'100'})
  self.assertEqual(r['amount_out_raw'],'999')
  self.assertFalse(r['quote_executable'])
  self.assertFalse(r['signed'])
  self.assertTrue(any(method=='eth_call' and params[0]['data'].startswith(selector('querySwapSingleTokenExactIn(address,address,address,uint256,address,bytes)')) for method,params in self.rpc.calls))
 def test_quote_without_pool_is_explicitly_unavailable(self):
  r=self.kit.run('quotes.swap',{'chain_id':CHAIN,'token_in':T1,'token_out':T2,'amount_raw':'100'})
  self.assertFalse(r['quote_executable'])
 def test_wallet_positions_not_full_portfolio(self):
  r=self.kit.run('accounts.positions',{'chain_id':CHAIN,'wallet':WALLET,'token':T1})
  self.assertEqual(r['balance_raw'],'500')
  self.assertIn('not exhaustive',r['portfolio_coverage'])
 def test_erc4626_wrapper_response_not_assumed_to_be_rootstock(self):
  r=self.kit.run('assets.wrapper_underlying',{'chain_id':CHAIN,'address':T1})
  self.assertEqual(r['underlying'],T2)
  self.assertIn('not inferred',r['classification'])
 def test_graph_from_actual_token_observation(self):
  self.kit.index.sync(self.rpc,52131550,52131551)
  g=self.kit.run('topology.explore',{'chain_id':CHAIN,'limit':5})
  self.assertEqual(len(g['edges']),1)
  self.assertEqual(len(g['nodes']),2)
  self.assertEqual(g['orchard_labels'],'not_assigned_without_rootstock_structure_evidence')
 def test_watch_poll_is_one_shot(self):
  self.kit.index.sync(self.rpc,52131550,52131551)
  x=self.kit.run('watch.poll',{'chain_id':CHAIN,'since_block':52131550})
  self.assertEqual(len(x['events']),0)
  self.assertFalse(x['subscriptions_running'])
 def test_unsigned_tx_rejects_missing_pinned_registry(self):
  with self.assertRaises(Exception):self.kit.run('transactions.prepare',{'chain_id':CHAIN,'transaction_json':json.dumps({'from':WALLET,'to':T1,'data':'0x'})})
 def test_policy_never_approves_execution(self):
  for action in ['swap','execute','transfer','approve','deploy','sign']:
   self.assertEqual(self.kit.run('policy.evaluate',{'action':action,'chain_id':CHAIN})['decision'],'DENY')
 def test_transaction_receipt_and_no_send(self):
  got=self.kit.run('transactions.status',{'chain_id':CHAIN,'hash':TX})
  self.assertTrue(got['success']);self.assertFalse(got['finality_verified'])
  self.assertFalse(any(m.startswith('eth_send') for m,p in self.rpc.calls))
 def test_unknown_rpc_bad_chain(self):
  with self.assertRaises(ChainError):self.kit.run('assets.lookup',{'chain_id':1,'address':T1})
 def test_analytics_no_false_tvl(self):
  v=self.kit.run('analytics.tvl',{'chain_id':CHAIN})
  self.assertIsNone(v['value']);self.assertEqual(v['state'],'unavailable')
 def test_simulation_readonly_and_pinned_target(self):
  registry_dir=ROOT/'tests/fixtures'
  self.kit.registry_dir=registry_dir
  self.kit.allow_unpinned=True # explicitly cannot override pin requirement of simulate
  with self.assertRaises(Exception):self.kit.run('transactions.simulate',{'chain_id':CHAIN,'transaction_json':json.dumps({'to':VAULT,'from':WALLET,'data':'0x'})})

class VisualAndMCPTests(unittest.TestCase):
 def test_dashboard_html_and_api(self):
  with tempfile.TemporaryDirectory() as td:
   kit=Toolchain(index_path=Path(td)/'none.sqlite3')
   server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(kit));worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
   base='http://127.0.0.1:'+str(server.server_address[1])
   try:
    with self.assertRaises(urllib.error.HTTPError) as ctx:
     urllib.request.urlopen(base+'/',timeout=3)
    self.assertEqual(ctx.exception.code,404)
    with urllib.request.urlopen(base+'/v1/history/8453',timeout=3) as r:
     item=json.load(r);self.assertFalse(item['result']['index_present'])
    with urllib.request.urlopen(base+'/openapi.json',timeout=3) as r:
     spec=json.load(r)['result'];self.assertEqual(spec['openapi'],'3.1.0');self.assertIn('/v1/graph/{chain_id}',spec['paths'])
    with self.assertRaises(urllib.error.HTTPError) as e:
     urllib.request.urlopen(urllib.request.Request(base+'/v1/networks',method='POST'),timeout=3)
    self.assertEqual(e.exception.code,405)
   finally:server.shutdown();server.server_close();worker.join()
 def test_mcp_new_capability_is_same_sdk(self):
  kit=Toolchain()
  m=Server(kit)
  meta={'io.modelcontextprotocol/protocolVersion':MODERN,'io.modelcontextprotocol/clientCapabilities':{}}
  msg={'jsonrpc':'2.0','id':42,'method':'tools/call','params':{'_meta':meta,'name':'policy.evaluate','arguments':{'chain_id':8453,'action':'execute'}}}
  r=m._respond(msg)['result'];self.assertEqual(r['structuredContent']['data'],kit.run('policy.evaluate',{'chain_id':8453,'action':'execute'}))
  self.assertTrue(all(t['annotations']['readOnlyHint'] for t in m._respond({'jsonrpc':'2.0','id':43,'method':'tools/list','params':{'_meta':meta}})['result']['tools']))
 def test_no_write_rpc_methods(self):
  from rootstock_tools.rpc import JsonRpc
  rpc=JsonRpc('http://127.0.0.1:42',8453,allow_local=True)
  with self.assertRaisesRegex(ChainError,'allowlist'):rpc.call('eth_sendRawTransaction',['0x01'])

if __name__=='__main__':unittest.main()
