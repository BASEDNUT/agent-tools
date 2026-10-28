"""Adversarial regression tests for Vault event and index correctness."""
import json, tempfile, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tests'))
from test_v05_features import FauxRpc,swap_log,pool_log,CHAIN,POOL,VAULT,T1,T2,B32,word,addr_word
from rootstock_tools.evm import decode_dynamic_uint_array
from rootstock_tools.indexer import EventIndex,TOPICS,decode_logs
from rootstock_tools.rpc import ChainError
from rootstock_tools.core import Toolchain

def liquidity_log(amounts=(100,200),fees=(1,2)):
    arr1=word(len(amounts))+''.join(word(x) for x in amounts)
    arr2=word(len(fees))+''.join(word(x) for x in fees)
    data='0x'+word(777)+word(96)+word(96+len(arr1)//2)+arr1+arr2
    return {**pool_log(idx=2),'topics':[TOPICS['LiquidityAdded'],'0x'+addr_word(POOL),'0x'+addr_word(T1),'0x'+word(2)],'data':data}

class V06Integrity(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.index=EventIndex(Path(self.tmp.name)/'audit.sqlite3')
        self.rpc=FauxRpc()
    def tearDown(self):self.tmp.cleanup()
    def test_pool_pause_and_fee_events(self):
        event={**pool_log(idx=4),'topics':[TOPICS['PoolPausedStateChanged'],'0x'+addr_word(POOL)],'data':'0x'+word(1)}
        parsed=decode_logs([event],CHAIN,52131550,52131550)[0]
        self.assertTrue(parsed['enabled'])
        event['topics'][0]=TOPICS['SwapFeePercentageChanged']
        parsed=decode_logs([event],CHAIN,52131550,52131550)[0]
        self.assertEqual(parsed['percentage_18'],'1')
        event['data']='0x'+word(2);event['topics'][0]=TOPICS['PoolPausedStateChanged']
        with self.assertRaisesRegex(ChainError,'boolean'):decode_logs([event],CHAIN,52131550,52131550)
    def test_ranking_over_last_500(self):
        self.rpc.logs=[{**swap_log(52131550,i),'transactionHash':'0x'+f'{i+1:064x}'} for i in range(500)]
        self.rpc.logs += [{**swap_log(52131551,i),'transactionHash':'0x'+f'{i+501:064x}'} for i in range(10)]
        self.index.sync(self.rpc,52131550,52131550)
        self.index.sync(self.rpc,52131551,52131551)
        ranked=self.index.rank_pools(CHAIN)
        self.assertEqual(ranked['pools'][0]['observed_swaps'],510)
    def test_pool_initialized_requires_empty_data(self):
        x={**pool_log(idx=8),'topics':[TOPICS['PoolInitialized'],'0x'+addr_word(POOL)],'data':'0x'}
        self.assertEqual(decode_logs([x],CHAIN,52131550,52131550)[0]['kind'],'PoolInitialized')
        x['data']='0x'+word(0)
        with self.assertRaisesRegex(ChainError,'Unexpected'):decode_logs([x],CHAIN,52131550,52131550)
    def test_liquidity_full_arrays(self):
        got=decode_logs([liquidity_log()],CHAIN,52131550,52131550)[0]
        self.assertEqual(got['token_amounts_raw'],['100','200'])
        self.assertEqual(got['swap_fee_amounts_raw'],['1','2'])
    def test_liquidity_mismatched_lengths_rejected(self):
        with self.assertRaisesRegex(ChainError,'disagree'):
            decode_logs([liquidity_log((100,200),(1,))],CHAIN,52131550,52131550)
    def test_coverage_separate_windows_not_falsely_contiguous(self):
        self.index.sync(self.rpc,52131550,52131551)
        self.index.sync(self.rpc,52131554,52131555)
        intervals=self.index.events(CHAIN)['scanned_intervals']
        self.assertEqual(intervals,[{'from_block':52131550,'to_block':52131551},{'from_block':52131554,'to_block':52131555}])
    def test_adjacent_windows_merge(self):
        self.index.sync(self.rpc,52131550,52131551)
        self.index.sync(self.rpc,52131552,52131553)
        self.assertEqual(self.index.events(CHAIN)['scanned_intervals'],[{'from_block':52131550,'to_block':52131553}])
    def test_reorg_discards_invalidated_coverage(self):
        self.index.sync(self.rpc,52131550,52131551)
        self.rpc.hash='0x'+'d'*64;self.rpc.logs=[]
        self.index.sync(self.rpc,52131554,52131555)
        self.assertEqual(self.index.events(CHAIN)['scanned_intervals'],[{'from_block':52131554,'to_block':52131555}])
    def test_filter_occurs_before_limit(self):
        # Include many historical logs; request only new ones.
        self.rpc.logs=[{**swap_log(52131550, i),'transactionHash':'0x'+f'{i+1:064x}'} for i in range(40)]
        self.rpc.logs+=[{**swap_log(52131551, 40),'transactionHash':'0x'+f'{41:064x}'}]
        self.index.sync(self.rpc,52131550,52131551)
        result=self.index.events(CHAIN,since_block=52131550,limit=1)
        self.assertEqual(len(result['events']),1)
        self.assertEqual(result['events'][0]['block_number'],52131551)
    def test_timestamp_filtered_aggregation_never_silently_drops_missing(self):
        self.index.sync(self.rpc,52131550,52131551)
        got=self.index.aggregate_swaps(CHAIN,since_timestamp=1000)
        self.assertEqual(got['state'],'incomplete_timestamps')
        self.assertEqual(got['missing_event_timestamps'],1)
        self.assertEqual(got['swap_event_count'],0)
    def test_stats_count_all_over_500(self):
        self.rpc.logs=[{**swap_log(52131550,i),'transactionHash':'0x'+f'{i+1:064x}'} for i in range(500)]
        self.rpc.logs += [{**swap_log(52131551,i),'transactionHash':'0x'+f'{i+501:064x}'} for i in range(10)]
        self.index.sync(self.rpc,52131550,52131550)
        self.index.sync(self.rpc,52131551,52131551)
        got=self.index.stats(CHAIN)
        self.assertEqual(got['swap_event_count'],510)
        self.assertEqual(got['input_volume_raw_by_token'][T1.lower()],str(100000*510))
    def test_pool_calls_share_block_tag(self):
        kit=Toolchain(index_path=Path(self.tmp.name)/'i.sqlite3');kit._rpc=lambda c:self.rpc
        kit.run('pools.inspect',{'chain_id':CHAIN,'pool':POOL})
        reads=[p for m,p in self.rpc.calls if m=='eth_call']
        self.assertTrue(reads)
        self.assertEqual({p[-1] for p in reads},{hex(52131557)})
    def test_invalid_event_data_is_blocked(self):
        x=liquidity_log();x['data']='0x'+word(5)
        with self.assertRaises(ChainError):decode_logs([x],CHAIN,52131550,52131550)

if __name__=='__main__':unittest.main()
