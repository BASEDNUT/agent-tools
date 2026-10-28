"""Adversarial/integration tests for read-only v0.7 interfaces and state correctness."""
import json, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
from test_v05_features import FauxRpc,CHAIN,POOL,T1,T2,WALLET,B32,swap_log,pool_log,VAULT
from rootstock_tools.core import Toolchain,CapabilityError
from rootstock_tools.rpc import ChainError
from rootstock_tools.evm import selector
from rootstock_tools.valuation import PriceBook,PriceError, value_pool
from rootstock_tools.orchard import OrchardConfig,OrchardError
from rootstock_tools.mcp import Server,MODERN

class TestV07(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.dir=Path(self.tmp.name)
  self.rpc=FauxRpc();self.kit=Toolchain(index_path=self.dir/'index.sqlite3');self.kit._rpc=lambda c:self.rpc
 def price_file(self,prices=None,**kw):
  path=self.dir/'prices.json'; data={'version':1,'chain_id':CHAIN,'block_number':52131557,
          'block_hash':B32,'source':'operator test fixture, not oracle verified',
          'prices':prices or [{'token':T1,'usd':'1.25'},{'token':T2,'usd':'2.00'}]}
  data.update(kw);path.write_text(json.dumps(data));return path
 def orchard_file(self,**kw):
  path=self.dir/'orchard.json';data={'version':1,'chain_id':CHAIN,'root_asset':T1,'threshold':'0.01','lp_tokens':[T2],'source':'operator test fixture - NOT APPROVED'}
  data.update(kw);path.write_text(json.dumps(data));return path
 def test_vault_and_quote_read_same_block(self):
  from rootstock_tools.services import direct_pool_quote
  r=direct_pool_quote(self.rpc,VAULT,POOL,T1,T2,'500')
  self.assertEqual(r['source_block_tag'],hex(52131557))
  read_tags=[p[-1] for m,p in self.rpc.calls if m=='eth_call']
  self.assertEqual(set(read_tags),{hex(52131557)})
  self.assertFalse(r['quote_executable'])
 def test_quote_reorg_during_request_rejected(self):
  from rootstock_tools.services import direct_pool_quote
  orig=self.rpc.call; count=[0]
  def flip(method,params):
   if method=='eth_getBlockByNumber':
    count[0]+=1
    if count[0]==2:return {'hash':'0x'+'d'*64}
   return orig(method,params)
  self.rpc.call=flip
  with self.assertRaisesRegex(ChainError,'changed'):direct_pool_quote(self.rpc,VAULT,POOL,T1,T2,'1')
 def test_wallet_balances_share_head_and_detect_duplicate(self):
  r=self.kit.run('accounts.balances',{'chain_id':CHAIN,'wallet':WALLET,'tokens':[T1,T2]})
  self.assertEqual(len(r['assets']),2)
  self.assertEqual(r['assets'][0]['balance_raw'],'500')
  self.assertEqual({p[-1] for m,p in self.rpc.calls if m=='eth_call'}, {hex(52131557)})
  with self.assertRaises(ChainError):self.kit.run('accounts.balances',{'chain_id':CHAIN,'wallet':WALLET,'tokens':[T1,T1.lower()]})
  with self.assertRaises(CapabilityError):self.kit.run('accounts.balances',{'chain_id':CHAIN,'wallet':WALLET,'tokens':'not-array'})
 def test_receipt_canonicality_and_confirmation_count(self):
  receipt=self.kit.run('transactions.status',{'chain_id':CHAIN,'hash':'0x'+'c'*64})
  self.assertEqual(receipt['confirmations'],3)
  self.assertTrue(receipt['canonical_at_provider_head'])
  self.assertFalse(receipt['finality_verified'])
  self.rpc.hash='0x'+'d'*64
  with self.assertRaisesRegex(ChainError,'no longer canonical'):self.kit.run('transactions.status',{'chain_id':CHAIN,'hash':'0x'+'c'*64})
 def test_operator_priced_tvl_arithmetic(self):
  book=PriceBook(self.price_file());self.kit.price_book=book
  result=self.kit.run('analytics.tvl',{'chain_id':CHAIN,'pool':POOL})
  self.assertEqual(result['value'],'524289.25')
  self.assertEqual(result['state'],'derived_from_operator_prices')
  self.assertFalse(result['price_source_verified'])
  self.assertEqual(len(result['tokens']),2)
 def test_invalid_prices_fail_closed(self):
  for bad in ('NaN','Infinity','-1','0','1e100','a'):
   with self.subTest(bad=bad):
    with self.assertRaises(PriceError):PriceBook(self.price_file([{'token':T1,'usd':bad}]))
  book=PriceBook(self.price_file(block_hash='0x'+'e'*64));self.kit.price_book=book
  with self.assertRaisesRegex(PriceError,'does not match'):self.kit.run('analytics.tvl',{'chain_id':CHAIN,'pool':POOL})
 def test_price_missing_asset_no_zero_fabrication(self):
  self.kit.price_book=PriceBook(self.price_file([{'token':T1,'usd':'1'}]))
  r=self.kit.run('analytics.tvl',{'chain_id':CHAIN,'pool':POOL})
  self.assertIsNone(r['value']);self.assertEqual(r['state'],'unavailable')
 def test_operator_config_eligibility(self):
  rule=OrchardConfig(self.orchard_file());self.kit.orchard_config=rule
  r=self.kit.run('accounts.eligibility',{'chain_id':CHAIN,'wallet':WALLET})
  self.assertTrue(r['eligible']);self.assertEqual(r['root_minimum_raw'],'10000000000000000')
  self.assertFalse(r['rule_approved_by_project'])
 def test_eligibility_absent_config_is_unknown(self):
  r=self.kit.run('accounts.eligibility',{'chain_id':CHAIN,'wallet':WALLET})
  self.assertIsNone(r['eligible'])
 def test_config_duplicate_and_chain_mismatch(self):
  with self.assertRaises(OrchardError):OrchardConfig(self.orchard_file(lp_tokens=[T1]))
  self.kit.orchard_config=OrchardConfig(self.orchard_file(chain_id=84532))
  with self.assertRaisesRegex(OrchardError,'chain'):self.kit.run('accounts.eligibility',{'chain_id':CHAIN,'wallet':WALLET})
 def test_rooted_graph_explicit_classification(self):
  self.kit.orchard_config=OrchardConfig(self.orchard_file())
  self.kit.index.sync(self.rpc,52131550,52131550)
  g=self.kit.run('topology.rooted',{'chain_id':CHAIN})
  self.assertEqual(g['edges'][0]['proposed_orchard_structure'],'Branch')
  self.assertFalse(g['structures_are_project_canonical'])
 def test_cursor_retains_late_events_same_block(self):
  self.rpc.logs=[pool_log(idx=1),swap_log(idx=2),swap_log(idx=3)]
  self.kit.index.sync(self.rpc,52131550,52131550)
  r=self.kit.run('watch.cursor',{'chain_id':CHAIN,'since_block':52131550,'since_log_index':1,'limit':1})
  self.assertEqual(r['next_cursor'],{'block':52131550,'log_index':2})
  later=self.kit.run('watch.cursor',{'chain_id':CHAIN,'since_block':52131550,'since_log_index':2})
  self.assertEqual(later['events'][0]['log_index'],3)
 def test_registration_not_hidden_by_swaps(self):
  self.rpc.logs=[pool_log(idx=1)]+[{**swap_log(52131550,i+2),'transactionHash':'0x'+f'{i+30:064x}'} for i in range(100)]
  self.kit.index.sync(self.rpc,52131550,52131550)
  r=self.kit.run('pools.observe',{'chain_id':CHAIN,'pool':POOL})
  self.assertEqual(r['pool_math_type'],'WEIGHTED')
  self.assertEqual(len(r['indexed_registration']),1)
 def test_abi_catalog_never_invents_signature(self):
  result=self.kit.run('registry.abi_selector',{'interface':'ERC20','signature':'balanceOf(address)'})
  self.assertEqual(result['selector'],'0x70a08231')
  with self.assertRaises(ChainError):self.kit.run('registry.abi_selector',{'interface':'RootstockVault','signature':'execute(address)'})
  self.assertFalse(self.kit.run('registry.abi_catalog')['signing_approved'])
 def test_mcp_uses_same_new_capability(self):
  m=Server(self.kit);meta={'io.modelcontextprotocol/protocolVersion':MODERN,'io.modelcontextprotocol/clientCapabilities':{}}
  req={'jsonrpc':'2.0','id':15,'method':'tools/call','params':{'_meta':meta,'name':'accounts.eligibility','arguments':{'chain_id':CHAIN,'wallet':WALLET}}}
  response=m._respond(req)
  self.assertIsNone(response['result']['structuredContent']['data']['eligible'])

if __name__=='__main__': unittest.main()
