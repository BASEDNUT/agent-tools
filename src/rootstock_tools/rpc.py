"""Deliberately narrow read-only EVM JSON-RPC client and vault-event scanner.

No arbitrary method calls or transaction submission are exposed through capabilities.
"""
from __future__ import annotations
import json
import re
import urllib.request
from urllib.parse import urlsplit
from dataclasses import dataclass

TOPIC_POOL_REGISTERED = '0xbc1561eeab9f40962e2fb827a7ff9c7cdb47a9d7c84caeefa4ed90e043842dad'
CHAIN_CONFIG = {
  8453: {'name':'Base','rpc':'https://base.publicnode.com', 'vault':'0x0a3af0Da0175afa0Cc05a6ad9092dC740155a0E7','from_block':52131550},
  84532: {'name':'Base Sepolia','rpc':'https://sepolia.base.org', 'vault':'0xEf348c4222ab9c08aFE768AD722Fb02b10d640c9','from_block':46984000},
}
# These 16 mappings were transcribed from a source-locked Rootstock discovery file,
# not independently checked against chain receipts in this release.
FACTORIES = {
  8453: {
   '0x9a5bd368c8da0d7fad33fc89b6be4e39e5a33f92':'WEIGHTED',
   '0x74c9804b4659feb7d056f150a810c4b5ae926da1':'STABLE',
   '0x179bdcaebadf57d6be08db5776781f4d0b64d5ce':'STABLE',
   '0x8da17c9a51b3bbc4a4c951edce5cd9764e42a985':'GYRO',
   '0xf7024eb7d37e993c8959090c84762f6273e43682':'GYROE',
   '0x730bf6af759e9e74aa6f9f0950e233df974d1859':'RECLAMM',
   '0xf5cac7d8e637d2827c07c44ae4767093647b0867':'LIQUIDITY_BOOTSTRAPPING',
   '0x5dbd872f506ab714bf4d9c20675598d9f1495ba8':'LIQUIDITY_BOOTSTRAPPING',
  },
  84532: {
   '0x277d7dde3c6762c31cfb438c9331376fe8887a7c':'WEIGHTED',
   '0x24ab9fba48e54b05c24a02122c4c40fd2018ba10':'STABLE',
   '0x6cd1150ccc00e0d00cd3f671a8bdf00d38f5be6e':'STABLE',
   '0x458d984f6216daffc9da4577fc949bcab0e52b6d':'GYRO',
   '0x6057859cc86aa62c54860e1a342f60ab42098efe':'GYROE',
   '0x928e433f50fa579c9be5f7e1273f1db46d630ee1':'RECLAMM',
   '0xdfdddd87dc49756dd93598123879ae3d67b531a3':'LIQUIDITY_BOOTSTRAPPING',
   '0x9a30757385012495a21d64c5efac335b1a6fe48d':'LIQUIDITY_BOOTSTRAPPING',
  }
}
ADDRESS = re.compile(r'^0x[0-9a-fA-F]{40}$')
HEX32 = re.compile(r'^0x[0-9a-fA-F]{64}$')

class ChainError(ValueError): pass

def require_chain(chain_id):
    if type(chain_id) is not int or chain_id not in CHAIN_CONFIG:
        raise ChainError('Unsupported chain; only Base 8453 and Base Sepolia 84532')
    return CHAIN_CONFIG[chain_id]

def require_address(addr):
    if not isinstance(addr,str) or not ADDRESS.fullmatch(addr):
        raise ChainError('Invalid EVM address')
    return addr

def parse_quantity(n):
    if not isinstance(n,str) or not re.fullmatch(r'0x(?:0|[1-9a-fA-F][0-9a-fA-F]*)',n):
        raise ChainError('Invalid hexadecimal RPC quantity')
    return int(n,16)

USER_AGENT='rootstock-agent-tools/0.9.1'  # Public RPC endpoints 403 the default Python-urllib UA.

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        raise ChainError('RPC redirect refused')

class JsonRpc:
    def __init__(self, url, chain_id, *, allow_local=False, timeout=9, execute=False):
        require_chain(chain_id)
        parts=urlsplit(url)
        local=(parts.hostname or '').lower() in ('127.0.0.1','localhost','::1')
        if parts.username or parts.password or parts.fragment or not parts.hostname or (parts.scheme!='https' and not (allow_local and local and parts.scheme=='http')):
            raise ChainError('External RPC must use HTTPS; local HTTP requires explicit test opt-in')
        self.url=url
        self.endpoint_host=parts.hostname  # Never disclose path/query API keys in structured outputs.
        self.chain_id=chain_id
        self.timeout=timeout
        self.opener=urllib.request.build_opener(NoRedirect())
        self.sequence=0
        self.execute=execute  # execute-mode transport: adds broadcast-only methods

    def call(self, method, params):
        allowed=('eth_chainId','eth_blockNumber','eth_getBlockByNumber','eth_getLogs','eth_getCode','eth_call','eth_getTransactionReceipt')
        if self.execute:
            # execute mode adds ONLY signed-broadcast submission; no eth_sign, no arbitrary methods
            allowed=allowed+('eth_sendRawTransaction','eth_getTransactionCount','eth_estimateGas','eth_gasPrice')
        if method not in allowed:
            raise ChainError('RPC method not on allowlist')
        self.sequence+=1
        request_id=self.sequence
        raw=json.dumps({'jsonrpc':'2.0','id':request_id,'method':method,'params':params},separators=(',',':')).encode()
        req=urllib.request.Request(self.url, data=raw, headers={'Content-Type':'application/json','Accept':'application/json','User-Agent':USER_AGENT},method='POST')
        try:
            with self.opener.open(req,timeout=self.timeout) as response:
                if response.status!=200: raise ChainError(f'RPC HTTP status {response.status}')
                content=response.read(2_000_001)
        except (OSError, ValueError) as exc:
            raise ChainError('RPC transport failed (endpoint details withheld)') from exc
        if len(content)>2_000_000: raise ChainError('RPC response exceeds size limit')
        try: reply=json.loads(content)
        except (ValueError,UnicodeError) as exc: raise ChainError('RPC returned malformed JSON') from exc
        if not isinstance(reply,dict) or reply.get('jsonrpc')!='2.0' or reply.get('id')!=request_id:
            raise ChainError('RPC response identity mismatch')
        if 'error' in reply: raise ChainError('RPC rejected read-only request: '+str(reply['error'])[:250])
        if 'result' not in reply: raise ChainError('Missing RPC result')
        return reply['result']

    def check_chain(self):
        seen=parse_quantity(self.call('eth_chainId', []))
        if seen!=self.chain_id: raise ChainError(f'RPC chain mismatch: expected {self.chain_id}, observed {seen}')
        return seen

    def status(self):
        self.check_chain()
        head=parse_quantity(self.call('eth_blockNumber', []))
        b=self.call('eth_getBlockByNumber',[hex(head),False])
        if not isinstance(b,dict) or not HEX32.fullmatch(str(b.get('hash',''))):
            raise ChainError('Missing canonical head hash')
        return {'chain_id':self.chain_id,'head_block':head,'head_hash':b['hash'], 'source_type':'live_rpc','rpc_host':self.endpoint_host,'read_only':True}

    def pool_events(self, from_block, to_block, *, limit=250):
        if type(from_block) is not int or type(to_block) is not int or from_block<0 or to_block<from_block:
            raise ChainError('Invalid block interval')
        if to_block-from_block>1999: raise ChainError('Window exceeds 2000 blocks; request smaller windows')
        if type(limit) is not int or not 1<=limit<=500: raise ChainError('Limit must be 1..500')
        self.check_chain()
        head=parse_quantity(self.call('eth_blockNumber', []))
        if to_block>head: raise ChainError('Requested range extends beyond current provider head')
        config=CHAIN_CONFIG[self.chain_id]
        # A past block is an explicit caller-selected window; no fabricated zero-coverage claim.
        logs=self.call('eth_getLogs',[{'address':config['vault'],'fromBlock':hex(from_block),'toBlock':hex(to_block),'topics':[TOPIC_POOL_REGISTERED]}])
        if not isinstance(logs,list): raise ChainError('RPC logs not an array')
        # Never silently cut a window's results; if over limit, fail for full coverage.
        if len(logs)>limit: raise ChainError('Result exceeds limit; split the block window')
        events=[]
        for log in logs:
            if not isinstance(log,dict) or str(log.get('address','')).lower()!=config['vault'].lower() or log.get('removed',False):
                raise ChainError('Unexpected or reorged log')
            topics=log.get('topics')
            if not isinstance(topics,list) or len(topics)<3 or str(topics[0]).lower()!=TOPIC_POOL_REGISTERED:
                raise ChainError('Unrecognized PoolRegistered event layout')
            if not all(isinstance(t,str) and HEX32.fullmatch(t) for t in topics[:3]):
                raise ChainError('Invalid event topic')
            if int(topics[1][2:26],16)!=0 or int(topics[2][2:26],16)!=0:
                raise ChainError('Non-canonical address topic padding')
            pool='0x'+topics[1][-40:]
            factory='0x'+topics[2][-40:]
            number=parse_quantity(log.get('blockNumber'))
            if number<from_block or number>to_block: raise ChainError('Log outside requested block window')
            if not HEX32.fullmatch(str(log.get('blockHash',''))): raise ChainError('Log missing block hash')
            if not HEX32.fullmatch(str(log.get('transactionHash',''))): raise ChainError('Log missing transaction hash')
            idx=parse_quantity(log.get('logIndex'))
            events.append({'chain_id':self.chain_id,'vault':config['vault'],'pool':pool,'factory':factory,
              'pool_math_type':FACTORIES[self.chain_id].get(factory.lower(),'UNKNOWN'),'block_number':number,
              'block_hash':log['blockHash'],'tx_hash':log['transactionHash'],'log_index':idx,
              'source_type':'live_rpc','event':'PoolRegistered','topic0':TOPIC_POOL_REGISTERED,
              'provenance':'Rootstock Vault event from configured RPC; chain validated; no third-party API'})
        events.sort(key=lambda x:(x['block_number'],x['log_index']))
        return {'chain_id':self.chain_id,'vault':config['vault'],'from_block':from_block,'to_block':to_block,
                'request_window_scanned':True,'provider_head_block':head,'independent_log_completeness_verified':False,'rpc_response_received':True,'events':events,'event_count':len(events),
                'type_classification_source':'Rootstock pinned source mapping; UNKNOWN for unrecognized factories',
                'metrics_available':False}
