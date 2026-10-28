"""Conservative persistent local event index with reorg detection and no implicit network polling.

Writes are local and operator-initiated; MCP and HTTP only expose indexed reads.
"""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from .rpc import ChainError, CHAIN_CONFIG, TOPIC_POOL_REGISTERED, FACTORIES, parse_quantity, HEX32
from .evm import keccak256, decode_word, decode_dynamic_uint_array

TOPICS={
 'PoolRegistered':TOPIC_POOL_REGISTERED,
 'Swap':'0x'+keccak256(b'Swap(address,address,address,uint256,uint256,uint256,uint256)').hex(),
 'LiquidityAdded':'0x'+keccak256(b'LiquidityAdded(address,address,uint8,uint256,uint256[],uint256[])').hex(),
 'LiquidityRemoved':'0x'+keccak256(b'LiquidityRemoved(address,address,uint8,uint256,uint256[],uint256[])').hex(),
 'PoolInitialized':'0x'+keccak256(b'PoolInitialized(address)').hex(),
 'PoolPausedStateChanged':'0x'+keccak256(b'PoolPausedStateChanged(address,bool)').hex(),
 'PoolRecoveryModeStateChanged':'0x'+keccak256(b'PoolRecoveryModeStateChanged(address,bool)').hex(),
 'SwapFeePercentageChanged':'0x'+keccak256(b'SwapFeePercentageChanged(address,uint256)').hex(),
}
INV_TOPICS={v.lower():k for k,v in TOPICS.items()}

def decode_logs(logs,chain_id:int,from_block:int,to_block:int,limit:int=500):
    if not isinstance(logs,list) or len(logs)>limit:raise ChainError('Index batch exceeds event limit or malformed')
    vault=CHAIN_CONFIG[chain_id]['vault']; out=[]
    for log in logs:
        if not isinstance(log,dict) or log.get('removed') is True or str(log.get('address','')).lower()!=vault.lower():
            raise ChainError('Removed, malformed, or wrong-vault log')
        t=log.get('topics');
        if not isinstance(t,list) or not t or any(not isinstance(v,str) or not HEX32.fullmatch(v) for v in t):raise ChainError('Malformed Vault log topics')
        kind=INV_TOPICS.get(t[0].lower())
        if kind is None:raise ChainError('Unexpected event returned for requested topic set')
        n=parse_quantity(log.get('blockNumber'));i=parse_quantity(log.get('logIndex'))
        if not from_block<=n<=to_block:raise ChainError('Out-of-range log')
        bh=log.get('blockHash');tx=log.get('transactionHash')
        if not HEX32.fullmatch(str(bh)) or not HEX32.fullmatch(str(tx)):raise ChainError('Missing transaction/block evidence')
        required={'PoolRegistered':3,'Swap':4,'LiquidityAdded':4,'LiquidityRemoved':4,
                  'PoolInitialized':2,'PoolPausedStateChanged':2,
                  'PoolRecoveryModeStateChanged':2,'SwapFeePercentageChanged':2}[kind]
        if len(t)!=required:raise ChainError('Wrong indexed topic count')
        addrs=[]
        # For Liquidity events, third indexed argument is enum uint8, not address.
        for idx in (range(1,4) if kind=='Swap' else range(1,3) if kind in ('PoolRegistered','LiquidityAdded','LiquidityRemoved') else range(1,2)):
            val=int(t[idx],16)
            if val>=2**160:raise ChainError('Noncanonical indexed address')
            addrs.append('0x'+f'{val:040x}')
        ev={'chain_id':chain_id,'vault':vault,'kind':kind,'pool':addrs[0],
            'block_number':n,'block_hash':bh,'tx_hash':tx,'log_index':i,'source':'live_rpc',
            'data':log.get('data','0x')}
        if kind=='PoolRegistered':
            ev['factory']=addrs[1];ev['pool_math_type']=FACTORIES[chain_id].get(addrs[1].lower(),'UNKNOWN')
        elif kind=='Swap':
            ev['token_in']=addrs[1];ev['token_out']=addrs[2]
            for j,label in enumerate(('amount_in_raw','amount_out_raw','swap_fee_percentage_18','swap_fee_amount_raw')):
                ev[label]=str(decode_word(ev['data'],j))
        elif kind in ('PoolInitialized','PoolPausedStateChanged','PoolRecoveryModeStateChanged','SwapFeePercentageChanged'):
            if kind in ('PoolPausedStateChanged','PoolRecoveryModeStateChanged'):
                raw_flag=decode_word(ev['data'],0)
                if raw_flag not in (0,1): raise ChainError('Invalid boolean event data')
                ev['enabled']=bool(raw_flag)
            elif kind=='SwapFeePercentageChanged':
                ev['percentage_18']=str(decode_word(ev['data'],0))
            elif ev['data']!='0x':raise ChainError('Unexpected PoolInitialized data')
        else:
            ev['liquidity_provider']=addrs[1]
            kval=int(t[3],16)
            if kval>=2**8:raise ChainError('Noncanonical liquidity kind')
            ev['liquidity_kind']=kval
            ev['total_supply_raw']=str(decode_word(ev['data'],0))
            # Balancer IVaultEvents.sol: uint256 totalSupply, uint256[] amounts, uint256[] fees.
            # Dynamic pointers are relative to the beginning of the nonindexed data tuple.
            ev['token_amounts_raw']=[str(x) for x in decode_dynamic_uint_array(ev['data'],1,cap=32)]
            ev['swap_fee_amounts_raw']=[str(x) for x in decode_dynamic_uint_array(ev['data'],2,cap=32)]
            if len(ev['token_amounts_raw']) != len(ev['swap_fee_amounts_raw']):
                raise ChainError('Liquidity token and fee arrays disagree')
        out.append(ev)
    out.sort(key=lambda x:(x['block_number'],x['log_index']))
    if len({(e['chain_id'],e['tx_hash'].lower(),e['log_index']) for e in out})!=len(out):
        raise ChainError('Duplicate log identity')
    return out

class EventIndex:
    def __init__(self,path:Path):
        self.path=Path(path)
    def _connect(self,create=False):
        if not self.path.is_file() and not create: return None
        if create:
            self.path.parent.mkdir(parents=True,exist_ok=True)
            if self.path.is_symlink(): raise ChainError('Symlink index path refused')
        c=sqlite3.connect(self.path,timeout=10)
        if create:
            c.executescript('''CREATE TABLE IF NOT EXISTS blocks(chain_id INTEGER, number INTEGER, hash TEXT NOT NULL, PRIMARY KEY(chain_id,number));
            CREATE TABLE IF NOT EXISTS events(chain_id INTEGER NOT NULL, block_number INTEGER NOT NULL, tx_hash TEXT NOT NULL, log_index INTEGER NOT NULL, kind TEXT NOT NULL, pool TEXT NOT NULL, record TEXT NOT NULL, PRIMARY KEY(chain_id,tx_hash,log_index));
            CREATE INDEX IF NOT EXISTS events_chain_block ON events(chain_id,block_number);
            CREATE INDEX IF NOT EXISTS events_pool ON events(chain_id,pool,kind);
            CREATE TABLE IF NOT EXISTS coverage(chain_id INTEGER NOT NULL, first_block INTEGER NOT NULL, last_block INTEGER NOT NULL, PRIMARY KEY(chain_id,first_block,last_block));''')
            # Preserve databases created by older toolkits without discarding the evidence.
            if 'timestamp' not in {col[1] for col in c.execute('PRAGMA table_info(blocks)')}:
                c.execute('ALTER TABLE blocks ADD COLUMN timestamp INTEGER')
        return c
    def sync(self,rpc,from_block:int,to_block:int,*,chunk=250,limit=500):
        chain=rpc.chain_id
        if type(from_block) is not int or type(to_block) is not int or not (0<=from_block<=to_block):raise ChainError('Invalid sync interval')
        if type(chunk) is not int or not 1<=chunk<=2000:raise ChainError('Invalid chunk size')
        if type(limit) is not int or not 1<=limit<=500:raise ChainError('Invalid event limit')
        rpc.check_chain();head=parse_quantity(rpc.call('eth_blockNumber',[]))
        if to_block>head:raise ChainError('Requested index window beyond head')
        # Reconcile known checkpoint hashes and previously observed event blocks before writing.
        conn=self._connect(create=True);rewound_at=None;count=0;chunks=0
        try:
            existing=conn.execute('SELECT number,hash FROM blocks WHERE chain_id=? ORDER BY number',(chain,)).fetchall()
            existing+=conn.execute('SELECT DISTINCT block_number, json_extract(record,\'$.block_hash\') FROM events WHERE chain_id=?',(chain,)).fetchall()
            existing=sorted(set((int(n),str(h).lower()) for n,h in existing))
            for n,h in existing:
                if n>head:
                    rewound_at=n;break
                live=rpc.call('eth_getBlockByNumber',[hex(n),False]); hash_live=live.get('hash') if isinstance(live,dict) else None
                if not HEX32.fullmatch(str(hash_live)):raise ChainError('Unverifiable stored block')
                if hash_live.lower()!=h:
                    rewound_at=n;break
            # Make all changes transactional; any read failure rolls back.
            with conn:
                if rewound_at is not None:
                    conn.execute('DELETE FROM events WHERE chain_id=? AND block_number>=?',(chain,rewound_at))
                    conn.execute('DELETE FROM blocks WHERE chain_id=? AND number>=?',(chain,rewound_at))
                    crossing=conn.execute('SELECT first_block,last_block FROM coverage WHERE chain_id=? AND last_block>=?',(chain,rewound_at)).fetchall()
                    conn.execute('DELETE FROM coverage WHERE chain_id=? AND last_block>=?',(chain,rewound_at))
                    for first_seen,last_seen in crossing:
                        if first_seen<rewound_at:
                            conn.execute('INSERT OR IGNORE INTO coverage VALUES(?,?,?)',(chain,first_seen,rewound_at-1))
                for first in range(from_block,to_block+1,chunk):
                    last=min(to_block,first+chunk-1)
                    raw=rpc.call('eth_getLogs',[{'address':CHAIN_CONFIG[chain]['vault'], 'fromBlock':hex(first),'toBlock':hex(last), 'topics':[list(TOPICS.values())]}])
                    events=decode_logs(raw,chain,first,last,limit)
                    # Verify each event's block hash against an independent eth_getBlockByNumber call
                    # to the configured RPC. This checks response consistency, NOT independent provider truth.
                    block_times={}
                    for event_block in sorted(set(e['block_number'] for e in events)):
                        block=rpc.call('eth_getBlockByNumber',[hex(event_block),False])
                        block_hash=block.get('hash') if isinstance(block,dict) else None
                        if not HEX32.fullmatch(str(block_hash)) or any(
                            e['block_hash'].lower()!=block_hash.lower() for e in events if e['block_number']==event_block
                        ):raise ChainError('Vault event block hash inconsistent with provider header')
                        ts=block.get('timestamp')
                        if ts is not None: block_times[event_block]=parse_quantity(ts)
                    # Replace the requested interval to prevent stale events on incremental rescans.
                    conn.execute('DELETE FROM events WHERE chain_id=? AND block_number BETWEEN ? AND ?',(chain,first,last))
                    for ev in events:
                        conn.execute('INSERT INTO events VALUES(?,?,?,?,?,?,?)',(chain,ev['block_number'],ev['tx_hash'].lower(),ev['log_index'],ev['kind'],ev['pool'].lower(),json.dumps(ev,sort_keys=True)))
                    for bn,ts in block_times.items():
                        row=next(e['block_hash'] for e in events if e['block_number']==bn)
                        conn.execute('INSERT OR REPLACE INTO blocks(chain_id,number,hash,timestamp) VALUES(?,?,?,?)',(chain,bn,row.lower(),ts))
                    b=rpc.call('eth_getBlockByNumber',[hex(last),False]);bh=b.get('hash') if isinstance(b,dict) else None
                    if not HEX32.fullmatch(str(bh)):raise ChainError('Missing checkpoint block hash')
                    ts=parse_quantity(b['timestamp']) if b.get('timestamp') is not None else None
                    conn.execute('INSERT OR REPLACE INTO blocks(chain_id,number,hash,timestamp) VALUES(?,?,?,?)',(chain,last,bh.lower(),ts))
                    # Keep prior covered blocks on partial rescans. The intervals
                    # represent the union of successful scans, never only the last rescan.
                    conn.execute('INSERT OR IGNORE INTO coverage VALUES(?,?,?)',(chain,first,last))
                    count+=len(events);chunks+=1
            return {'chain_id':chain,'from_block':from_block,'to_block':to_block,'events_seen':count,'chunks':chunks,'rewound_from':rewound_at,'local_database_updated':True,'provider_head':head,
                    'completeness':'bounded provider logs, not independent archive proof','source':'live_rpc','index_path':str(self.path)}
        finally:conn.close()
    def events(self,chain_id:int,*,kind=None,pool=None,limit=200,since_block=None):
        if type(limit) is not int or not 1<=limit<=500:raise ChainError('Invalid query limit')
        if kind is not None and kind not in TOPICS:raise ChainError('Unknown event type')
        from .rpc import require_chain,require_address
        require_chain(chain_id)
        if pool is not None:pool=require_address(pool).lower()
        if since_block is not None and (type(since_block) is not int or since_block<0):
            raise ChainError('Invalid since_block')
        c=self._connect()
        if c is None:return {'chain_id':chain_id,'indexed':False,'events':[],'coverage':[]}
        try:
            clauses=['chain_id=?'];args=[chain_id]
            if kind:clauses+=['kind=?'];args+=[kind]
            if pool:clauses+=['pool=?'];args+=[pool]
            if since_block is not None:clauses+=['block_number>?'];args+=[since_block]
            rows=c.execute('SELECT record FROM events WHERE '+' AND '.join(clauses)+' ORDER BY block_number DESC,log_index DESC LIMIT ?',(*args,limit)).fetchall()
            coverage=c.execute('SELECT number,hash FROM blocks WHERE chain_id=? ORDER BY number',(chain_id,)).fetchall()
            ranges=c.execute('SELECT first_block,last_block FROM coverage WHERE chain_id=? ORDER BY first_block',(chain_id,)).fetchall()
            merged=[]
            for a,b in ranges:
                if merged and a<=merged[-1][1]+1: merged[-1][1]=max(merged[-1][1],b)
                else:merged.append([a,b])
            return {'chain_id':chain_id,'indexed':True,'events':[json.loads(x[0]) for x in rows],'checkpoints':[{'block':n,'hash':h} for n,h in coverage],
                    'coverage':'only explicitly requested index windows; no claim of complete history',
                    'scanned_intervals':[{'from_block':a,'to_block':b} for a,b in merged],
                    'historical_finality_verified':False}
        finally:c.close()
    def after_cursor(self,chain_id:int,since_block:int,since_log_index:int,limit:int=200):
        from .rpc import require_chain
        require_chain(chain_id)
        if any(type(x) is not int for x in (since_block,since_log_index,limit)) or since_block<0 or since_log_index<0 or not 1<=limit<=500:
            raise ChainError('Invalid event cursor or result limit')
        c=self._connect()
        if c is None:return {'chain_id':chain_id,'indexed':False,'events':[],'next_cursor':{'block':since_block,'log_index':since_log_index}}
        try:
            rows=c.execute('SELECT record FROM events WHERE chain_id=? AND (block_number>? OR (block_number=? AND log_index>?)) ORDER BY block_number ASC,log_index ASC LIMIT ?',
                           (chain_id,since_block,since_block,since_log_index,limit)).fetchall()
            events=[json.loads(record) for (record,) in rows]
            cursor={'block':events[-1]['block_number'],'log_index':events[-1]['log_index']} if events else {'block':since_block,'log_index':since_log_index}
            return {'chain_id':chain_id,'indexed':True,'events':events,'next_cursor':cursor,
                    'source':'indexed vault events','coverage':'only explicitly indexed blocks; see history.status'}
        finally:c.close()

    def rank_pools(self,chain_id:int,limit:int=10):
        from .rpc import require_chain
        require_chain(chain_id)
        if type(limit) is not int or not 1<=limit<=100:raise ChainError('Invalid ranking limit')
        c=self._connect()
        if c is None:return {'chain_id':chain_id,'ranking':'unavailable','pools':[],'reason':'No index'}
        try:
            rows=c.execute('SELECT pool,COUNT(*) AS count FROM events WHERE chain_id=? AND kind=? GROUP BY pool ORDER BY count DESC,pool LIMIT ?', (chain_id,'Swap',limit)).fetchall()
            return {'chain_id':chain_id,'ranking':'indexed_swap_counts_all_stored_events',
                'pools':[{'pool':pool,'observed_swaps':n} for pool,n in rows],
                'not_orchard_elo':True,'source':'local SQLite indexed Vault swaps',
                'coverage':'partial until every historical scan interval is complete'}
        finally:c.close()

    def aggregate_swaps(self,chain_id:int,pool=None,*,since_timestamp=None):
        from .rpc import require_chain,require_address
        require_chain(chain_id)
        if pool is not None: pool=require_address(pool).lower()
        if since_timestamp is not None and (type(since_timestamp) is not int or since_timestamp<0):
            raise ChainError('Invalid timestamp filter')
        c=self._connect()
        if c is None:return {'chain_id':chain_id,'state':'unavailable','reason':'No index'}
        try:
            cond=['e.chain_id=?',"e.kind='Swap'"];params=[chain_id]
            if pool:cond.append('e.pool=?');params.append(pool)
            # Missing timestamps must be counted, not silently removed by SQL WHERE.
            rows=c.execute('SELECT e.record,b.timestamp FROM events e LEFT JOIN blocks b ON b.chain_id=e.chain_id AND b.number=e.block_number WHERE '+' AND '.join(cond),params)
            volume={};fees={};n=0;missing_ts=0
            for record,ts in rows:
                if ts is None:
                    missing_ts+=1
                    if since_timestamp is not None:continue
                elif since_timestamp is not None and ts<since_timestamp:
                    continue
                e=json.loads(record);n+=1
                token=e['token_in'].lower();volume[token]=volume.get(token,0)+int(e['amount_in_raw'])
                fees[token]=fees.get(token,0)+int(e['swap_fee_amount_raw'])
            return {'chain_id':chain_id,'pool':pool,'state':'incomplete_timestamps' if since_timestamp is not None and missing_ts else 'partial_indexed','swap_event_count':n,
                'input_volume_raw_by_token':{k:str(v) for k,v in volume.items()},
                'swap_fee_raw_by_token':{k:str(v) for k,v in fees.items()},
                'since_timestamp':since_timestamp,'missing_event_timestamps':missing_ts,
                'usd_volume':None,'tvl_usd':None,'source':'indexed_vault_logs',
                'coverage':'recorded swap events only; scanned windows may have gaps; no independent completeness proof'}
        finally:c.close()

    def stats(self,chain_id:int,pool=None):
        return self.aggregate_swaps(chain_id,pool)
