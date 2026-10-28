"""Independent v0.7 audit regressions, added after reproducing omissions."""
import sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src')); sys.path.insert(0,str(ROOT/'tests'))
from rootstock_tools.indexer import EventIndex
from rootstock_tools.rpc import ChainError
from rootstock_tools.services import pool_inspect, wallet_balances, tx_status
from test_v05_features import FauxRpc, CHAIN, POOL, WALLET, T1, T2, TX, B32

class AuditRegressions(unittest.TestCase):
    def test_rescan_subrange_must_not_erase_other_covered_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            i=EventIndex(Path(td)/'events.sqlite3'); rpc=FauxRpc()
            i.sync(rpc,52131550,52131557)
            i.sync(rpc,52131553,52131554)
            self.assertEqual(i.events(CHAIN)['scanned_intervals'], [{'from_block':52131550,'to_block':52131557}])

    def test_pool_inspection_rejects_snapshot_block_reorg(self):
        class ReorgRpc(FauxRpc):
            def __init__(self): super().__init__(); self.header_reads=0
            def call(self,method,params):
                if method=='eth_getBlockByNumber':
                    self.header_reads+=1
                    if self.header_reads>1:return {'hash':'0x'+'f'*64}
                return super().call(method,params)
        with self.assertRaisesRegex(ChainError,'block changed'):
            pool_inspect(ReorgRpc(),POOL)

    def test_multi_wallet_inspection_rejects_snapshot_block_reorg(self):
        class ReorgRpc(FauxRpc):
            def __init__(self): super().__init__(); self.header_reads=0
            def call(self,method,params):
                if method=='eth_getBlockByNumber':
                    self.header_reads+=1
                    if self.header_reads>1:return {'hash':'0x'+'f'*64}
                return super().call(method,params)
        with self.assertRaisesRegex(ChainError,'block changed'):
            wallet_balances(ReorgRpc(),WALLET,[T1,T2])

    def test_receipt_must_match_requested_transaction_hash(self):
        class WrongReceiptRpc(FauxRpc):
            def call(self,method,params):
                r=super().call(method,params)
                if method=='eth_getTransactionReceipt':r['transactionHash']='0x'+'e'*64
                return r
        with self.assertRaisesRegex(ChainError,'transaction hash mismatch'):
            tx_status(WrongReceiptRpc(),TX)

    def test_receipt_invalid_status_cannot_be_reported_as_failure(self):
        class WrongStatusRpc(FauxRpc):
            def call(self,method,params):
                r=super().call(method,params)
                if method=='eth_getTransactionReceipt':r['status']='0x3'
                return r
        with self.assertRaisesRegex(ChainError,'receipt status'):
            tx_status(WrongStatusRpc(),TX)

if __name__=='__main__': unittest.main()

class CryptoAndProtocolAudit(unittest.TestCase):
    def test_keccak_rate_last_byte_against_openssl_vectors(self):
        from rootstock_tools.evm import keccak256
        # Generated independently by OpenSSL 3's KECCAK-256 digest.
        vectors={
          135:'03c527855334eb2e62b3b9b4d02ab76721707d3dde5fb218369640ee2edc7f3a',
          271:'6913adec7e366aaa82b47e65fa86e20416f3ca3bee8d3651b4b1e61a8e533ed1',
          407:'3bf0caa53fb9cf4ca498009eceaecc75c83a5bec7c740fac0b0d6c4854bde204',
        }
        for n,expected in vectors.items():
            with self.subTest(length=n): self.assertEqual(keccak256(b'Z'*n).hex(),expected)

    def test_mcp_unknown_tool_is_protocol_error_not_execution_error(self):
        from rootstock_tools.mcp import Server, MODERN
        from rootstock_tools.core import Toolchain
        metadata={'io.modelcontextprotocol/protocolVersion':MODERN,'io.modelcontextprotocol/clientCapabilities':{}}
        req={'jsonrpc':'2.0','id':7,'method':'tools/call','params':{
             '_meta':metadata,'name':'transactions.execute','arguments':{}}}
        reply=Server(Toolchain())._respond(req)
        self.assertEqual(reply['error']['code'],-32602)
        self.assertNotIn('result',reply)

class AssetConsistencyAudit(unittest.TestCase):
    def test_token_code_and_metadata_snapshot_cannot_cross_reorg(self):
        from rootstock_tools.services import asset_lookup
        class ReorgRpc(FauxRpc):
            def __init__(self): super().__init__(); self.headers=0
            def call(self,method,params):
                if method=='eth_getBlockByNumber':
                    self.headers+=1
                    if self.headers>1:return {'hash':'0x'+'f'*64}
                return super().call(method,params)
        with self.assertRaisesRegex(ChainError,'block changed'):
            asset_lookup(ReorgRpc(),T1)
