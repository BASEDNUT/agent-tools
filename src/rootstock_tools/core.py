"""Single read-only capability implementation for Python, CLI and MCP."""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any
from .registry import CHAIN_IDS, RegistryError, load_registry
from .rpc import CHAIN_CONFIG, ChainError, JsonRpc, require_chain, FACTORIES

from .services import asset_lookup, wrapper_underlying, pool_inspect, wallet_balance, tx_status, simulate_known_transaction, explicit_graph, direct_pool_quote, wallet_balances
from .indexer import EventIndex
from .rpc import require_address
from .policy import PolicyGate, PolicyError
from .valuation import PriceBook, value_pool
from .orchard import OrchardConfig, eligibility, rooted_structure
from .abi_catalog import catalog, signature_info

class CapabilityError(ValueError): pass

# Normalized signatures for both CLI and MCP; adapters never implement blockchain rules.
CAPABILITIES={
 'registry.list_networks': {'description':'List Rootstock network identities and available local source provenance.', 'properties':{}, 'required':[]},
 'registry.resolve_deployment': {'description':'Resolve a Rootstock deployment against a pinned canonical local registry; ambiguous names require task.', 'properties':{'chain_id':'integer','name':'string','task':'string'},'required':['chain_id','name']},
 'rpc.get_health': {'description':'Read the configured Base RPC chain ID, latest block and hash.', 'properties':{'chain_id':'integer'},'required':['chain_id']},
 'pools.list': {'description':'Read Vault PoolRegistered events for an explicitly bounded inclusive block window, with block provenance.', 'properties':{'chain_id':'integer','from_block':'integer','to_block':'integer','limit':'integer'},'required':['chain_id','from_block','to_block']},
 'skills.list': {'description':'List bundled Rootstock and Orchard agent skills; no third-party skill installation.', 'properties':{},'required':[]},
 'skills.read': {'description':'Read one bundled SKILL.md by its exact, validated skill name.', 'properties':{'name':'string'},'required':['name']},
 'capabilities.list': {'description':'List the implemented read-only capabilities and their schemas.', 'properties':{},'required':[]},
}

# Each capability below uses the same typed boundary for Python / CLI / MCP / HTTP.
CAPABILITIES.update({
 'registry.abi_catalog':{'description':'Return reviewed partial read-only ABI signatures and verified Vault event topics; not a full exact build ABI.','properties':{},'required':[]},
 'registry.abi_selector':{'description':'Return an exact selector for a reviewed read ABI function, not a deploy/transaction authorization.','properties':{'interface':'string','signature':'string'},'required':['interface','signature']},
 'registry.list_contracts': {'description':'List Rootstock registry deployments, preserving task identity and deprecated records.', 'properties':{'chain_id':'integer'},'required':['chain_id']},
 'registry.verify_contract': {'description':'Check pinned Rootstock contract code exists on the selected chain; not a bytecode audit.', 'properties':{'chain_id':'integer','name':'string','task':'string'},'required':['chain_id','name']},
 'assets.lookup':{'description':'Read explicit ERC20 contract metadata directly from chain.', 'properties':{'chain_id':'integer','address':'string'},'required':['chain_id','address']},
 'assets.wrapper_underlying':{'description':'Probe ERC4626 asset() directly; unsupported wrappers remain unknown.', 'properties':{'chain_id':'integer','address':'string'},'required':['chain_id','address']},
 'pools.inspect':{'description':'Read actual pool token addresses via Rootstock Vault; no guessed reserve/TVL.', 'properties':{'chain_id':'integer','pool':'string'},'required':['chain_id','pool']},
 'pools.observe':{'description':'Read pool onchain data plus local indexed registration evidence.', 'properties':{'chain_id':'integer','pool':'string'},'required':['chain_id','pool']},
 'history.events':{'description':'Query locally indexed Vault swap, pool and liquidity events.', 'properties':{'chain_id':'integer','kind':'string','pool':'string','limit':'integer','since_block':'integer'},'required':['chain_id']},
 'history.status':{'description':'Describe event-index checkpoints and local data coverage.', 'properties':{'chain_id':'integer'},'required':['chain_id']},
 'observations.status':{'description':'Report which indexed observations exist and which analytics are missing.', 'properties':{'chain_id':'integer'},'required':['chain_id']},
 'topology.rooted':{'description':'Provisional rooted Branch/Graft/Whorl classification from observed pools and configured root; not canonical Orchard ranks.','properties':{'chain_id':'integer','limit':'integer'},'required':['chain_id']},
 'topology.explore':{'description':'Construct token-pool graph from indexed pools and RPC token lists, labeling missing tokens.', 'properties':{'chain_id':'integer','limit':'integer'},'required':['chain_id']},
 'accounts.eligibility':{'description':'Check on-chain balances against explicitly configured Orchard root/LP rules; not an access grant.','properties':{'chain_id':'integer','wallet':'string'},'required':['chain_id','wallet']},
 'accounts.balances':{'description':'Read up to 32 explicitly provided token balances at one pinned chain block (no automatic portfolio discovery).','properties':{'chain_id':'integer','wallet':'string','tokens':'array'},'required':['chain_id','wallet','tokens']},
 'accounts.positions':{'description':'Read wallet balance of explicitly named ERC20 or LP token, not full portfolio.', 'properties':{'chain_id':'integer','wallet':'string','token':'string'},'required':['chain_id','wallet','token']},
 'analytics.volume_fees':{'description':'Aggregate available indexed swap input and fee amounts in raw token units; never presume complete coverage.', 'properties':{'chain_id':'integer','pool':'string','since_timestamp':'integer'},'required':['chain_id']},
 'analytics.tvl':{'description':'Explain TVL availability based on verified price/reserve inputs; never fabricate USD estimates.', 'properties':{'chain_id':'integer','pool':'string'},'required':['chain_id']},
 'analytics.turnover':{'description':'Report turnover only with known, matching volume and TVL denominator.', 'properties':{'chain_id':'integer','pool':'string'},'required':['chain_id']},
 'analytics.rankings':{'description':'Rank pools by observed indexed swap count, not wallet ELO or APY.', 'properties':{'chain_id':'integer','limit':'integer'},'required':['chain_id']},
 'watch.cursor':{'description':'Query indexed Vault events after a specific block and log index, preserving intra-block updates.','properties':{'chain_id':'integer','since_block':'integer','since_log_index':'integer','limit':'integer'},'required':['chain_id','since_block','since_log_index']},
 'watch.poll':{'description':'Check locally indexed events newer than a given block; caller schedules repeated polls.', 'properties':{'chain_id':'integer','since_block':'integer','limit':'integer'},'required':['chain_id','since_block']},
 'quotes.swap':{'description':'Return explicit routing prerequisites; quote unavailable without audited Rootstock SOR.', 'properties':{'chain_id':'integer','token_in':'string','token_out':'string','amount_raw':'string','pool':'string','sender':'string'},'required':['chain_id','token_in','token_out','amount_raw']},
 'transactions.simulate':{'description':'Explicit eth_call on a pinned Rootstock target; no signing or policy approval.', 'properties':{'chain_id':'integer','transaction_json':'string'},'required':['chain_id','transaction_json']},
 'transactions.prepare':{'description':'Return an unsigned policy-unapproved transaction envelope, only for pinned Rootstock targets.', 'properties':{'chain_id':'integer','transaction_json':'string'},'required':['chain_id','transaction_json']},
 'transactions.status':{'description':'Read transaction receipt and unverified finality from RPC.', 'properties':{'chain_id':'integer','hash':'string'},'required':['chain_id','hash']},
 'policy.evaluate':{'description':'Fail-closed policy demonstration: reads allowed, writes denied; not signer authorization.', 'properties':{'action':'string','chain_id':'integer'},'required':['action','chain_id']},
})

def schema_for(cap):
    spec=CAPABILITIES[cap]
    return {'type':'object','properties':{name:({'type':'array','items':{'type':'string'},'minItems':1,'maxItems':32} if typ=='array' else {'type':typ}) for name,typ in spec['properties'].items()},'required':spec['required'],'additionalProperties':False}

def validate_arguments(name,args):
    if name not in CAPABILITIES: raise CapabilityError('Unknown or unavailable capability; no transaction tools are supported')
    if not isinstance(args,dict): raise CapabilityError('Tool arguments must be an object')
    spec=CAPABILITIES[name]
    for key in args:
        if key not in spec['properties']: raise CapabilityError('Unknown argument: '+key)
    for key in spec['required']:
        if key not in args: raise CapabilityError('Missing argument: '+key)
    for key,value in args.items():
        expected=spec['properties'][key]
        if expected=='integer' and (type(value) is not int or value<0): raise CapabilityError(f'{key} must be a nonnegative integer')
        if expected=='array' and (not isinstance(value,list) or not 1<=len(value)<=32 or any(not isinstance(v,str) or len(v)>80 for v in value)): raise CapabilityError(f'{key} requires 1..32 strings')
        if expected=='string' and (not isinstance(value,str) or not value.strip() or len(value)>300): raise CapabilityError(f'{key} must be a nonempty string of at most 300 characters')
    if 'chain_id' in args: require_chain(args['chain_id'])
    return args

class Toolchain:
    def __init__(self,registry_dir: Path | None=None, *, allow_unpinned=False, allow_local_rpc=False, rpc_overrides=None, index_path: Path | None=None, price_book: Path | None=None, orchard_config: Path | None=None, policy_file: Path | None=None, agent_id: str | None=None):
        self.registry_dir=Path(registry_dir or os.getenv('ROOTSTOCK_REGISTRY_DIR',Path.home()/'.config/rootstock-agent-tools/deployments'))
        self.allow_unpinned=allow_unpinned
        self.allow_local_rpc=allow_local_rpc
        self.rpc_overrides=rpc_overrides or {}
        source=price_book or os.getenv("ROOTSTOCK_PRICE_BOOK")
        self.price_book=PriceBook(source) if source else None
        orchard_path=orchard_config or os.getenv("ROOTSTOCK_ORCHARD_CONFIG")
        self.orchard_config=OrchardConfig(orchard_path) if orchard_path else None
        self.index=EventIndex(Path(index_path or os.getenv("ROOTSTOCK_INDEX_PATH",Path.home()/".local/share/rootstock-agent-tools/events.sqlite3")))
        policy_file=policy_file or os.getenv('ROOTSTOCK_POLICY_FILE')
        agent_id=agent_id or os.getenv('ROOTSTOCK_AGENT_ID')
        if bool(policy_file)!=bool(agent_id):
            raise PolicyError('Process policy requires both a policy file and trusted launcher agent identity')
        self.policy=PolicyGate(Path(policy_file),agent_id) if policy_file else None

    def _rpc(self,chain):
        config=require_chain(chain)
        env='ROOTSTOCK_RPC_BASE' if chain==8453 else 'ROOTSTOCK_RPC_BASE_SEPOLIA'
        return JsonRpc(self.rpc_overrides.get(chain) or os.getenv(env) or config['rpc'],chain,allow_local=self.allow_local_rpc)

    @staticmethod
    def _skillroot(): return Path(__file__).parent / 'bundled_skills'

    def run(self,name:str,args:dict|None=None)->Any:
        args=validate_arguments(name,{} if args is None else args)
        if self.policy: self.policy.check(name,args)
        if name=='capabilities.list':
            return [{'name':key,'effect':'read','description':data['description'],'input_schema':schema_for(key)} for key,data in sorted(CAPABILITIES.items())]
        if name=='registry.list_networks':
            records=[]
            for chain,fn in sorted(CHAIN_IDS.items()):
                path=self.registry_dir/fn
                record={'chain_id':chain,'name':CHAIN_CONFIG[chain]['name'],'vault':CHAIN_CONFIG[chain]['vault'],
                        'network_source':'Rootstock source-locked onchain-pool-discovery.ts',
                        'registry_file':fn,'local_registry_present':path.is_file(), 'onchain_code_verified':False}
                if path.is_file():
                    try:
                        r=load_registry(path,allow_unpinned=self.allow_unpinned)
                        record.update(source_blob_sha=r.blob_sha,source_pinned=r.verified_against_pinned_blob)
                    except (OSError,RegistryError) as e:
                        record['registry_error']=str(e)
                records.append(record)
            return records
        if name=='registry.resolve_deployment':
            chain=args['chain_id'];require_chain(chain)
            reg=load_registry(self.registry_dir/CHAIN_IDS[chain], allow_unpinned=self.allow_unpinned)
            return reg.resolve(args['name'],args.get('task'))
        if name=='rpc.get_health': return self._rpc(args['chain_id']).status()
        if name=='pools.list': return self._rpc(args['chain_id']).pool_events(args['from_block'],args['to_block'],limit=args.get('limit',250))
        if name=='registry.abi_catalog':return catalog()
        if name=='registry.abi_selector':return signature_info(args['interface'],args['signature'])
        if name=='registry.list_contracts':
            chain=args['chain_id']; require_chain(chain)
            reg=load_registry(self.registry_dir/CHAIN_IDS[chain],allow_unpinned=self.allow_unpinned)
            return {'chain_id':chain,'source_pinned':reg.verified_against_pinned_blob,'source_blob_sha':reg.blob_sha,
             'entries':[{'task':t,'name':n,'address':a} for t,cs in reg.tasks.items() for n,a in cs.items()]}
        if name=='registry.verify_contract':
            chain=args['chain_id'];require_chain(chain)
            dep=self.run('registry.resolve_deployment',args)
            rpc=self._rpc(chain);rpc.check_chain()
            code=rpc.call('eth_getCode',[dep['address'],'latest'])
            import re
            if not isinstance(code,str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*',code) or len(code)>2_000_002:
                raise ChainError('Malformed or oversized contract code')
            return {'deployment':dep,'has_code':code!='0x','bytecode_provenance_verified':False,'source':'eth_getCode live RPC; full provenance sweep required'}
        if name=='assets.lookup':return asset_lookup(self._rpc(args['chain_id']),args['address'])
        if name=='assets.wrapper_underlying':return wrapper_underlying(self._rpc(args['chain_id']),args['address'])
        if name=='pools.inspect':return pool_inspect(self._rpc(args['chain_id']),args['pool'])
        if name=='pools.observe':
            state=self.run('pools.inspect',args)
            events=self.index.events(args['chain_id'],kind='PoolRegistered',pool=args['pool'],limit=500)['events']
            state['indexed_registration']=events
            state['registration_factory']=events[0]['factory'] if events else None
            state['pool_math_type']=(events[0].get('pool_math_type','UNKNOWN') if events else 'UNKNOWN')
            state['classification_source']='indexed_rootstock_vault_registration' if events else 'unavailable'
            return state
        if name=='history.events':return self.index.events(args['chain_id'],kind=args.get('kind'),pool=args.get('pool'),limit=args.get('limit',200),since_block=args.get('since_block'))
        if name in ('history.status','observations.status'):
            events=self.index.events(args['chain_id'],limit=1)
            return {'chain_id':args['chain_id'],'index_present':events['indexed'],'checkpoints':events.get('checkpoints',[]),
                    'source':'local SQLite + Vault logs','coverage':events.get('coverage','no local indexing'),
                    'live_analytics_available':False,'missing_metrics':['tvl_usd','apr','reliable_24h_usd_volume','Orchard ELO']}
        if name=='topology.rooted':
            graph=self.run('topology.explore',args)
            if graph.get('state')=='unavailable':return {**graph,'rooted':False}
            return rooted_structure(graph,self.orchard_config)
        if name=='topology.explore':
            chain=args['chain_id'];require_chain(chain)
            entries=self.index.events(chain,kind='PoolRegistered',limit=args.get('limit',8))['events'];observed=[];errors=[]
            if not entries:return {'chain_id':chain,'nodes':[],'edges':[],'source':'local index empty','state':'unavailable'}
            rpc=self._rpc(chain)
            for item in entries:
                try: observed.append(pool_inspect(rpc,item['pool']))
                except (ChainError,ValueError) as exc:errors.append({'pool':item['pool'],'reason':'contract read unavailable'})
            graph=explicit_graph(observed,chain)
            graph['unresolved_pools']=errors;graph['indexed_pool_count']=len(entries)
            return graph
        if name=='accounts.eligibility':return eligibility(self._rpc(args['chain_id']),args['wallet'],self.orchard_config)
        if name=='accounts.balances':return wallet_balances(self._rpc(args['chain_id']),args['wallet'],args['tokens'])
        if name=='accounts.positions':return wallet_balance(self._rpc(args['chain_id']),args['wallet'],args['token'])
        if name=='analytics.volume_fees':return self.index.aggregate_swaps(args['chain_id'],pool=args.get('pool'),since_timestamp=args.get('since_timestamp'))
        if name=='analytics.tvl':
            require_chain(args['chain_id'])
            if 'pool' not in args:
                return {'chain_id':args['chain_id'],'value':None,'state':'unavailable','reason':'Explicit pool address required'}
            state=pool_inspect(self._rpc(args['chain_id']),args['pool'])
            return value_pool(state,self.price_book)
        if name=='analytics.turnover':
            require_chain(args['chain_id'])
            if 'pool' not in args or self.price_book is None:
                return {'chain_id':args['chain_id'],'value':None,'state':'unavailable',
                        'reason':'Requires explicit pool and operator price book, plus a proven time-window history'}
            return {'chain_id':args['chain_id'],'pool':args['pool'],'value':None,'state':'unavailable',
                    'reason':'Point-in-time pool TVL and historical swap volume require a time-matched price series and complete block-window coverage; single-block prices cannot produce defensible turnover.'}
        if name=='analytics.rankings':return self.index.rank_pools(args['chain_id'],args.get('limit',10))
        if name=='watch.cursor':
            return self.index.after_cursor(args['chain_id'],args['since_block'],args['since_log_index'],args.get('limit',200))
        if name=='watch.poll':
            ev=self.index.events(args['chain_id'],limit=args.get('limit',200),since_block=args['since_block'])
            ev['poll_only']=True;ev['subscriptions_running']=False
            return ev
        if name=='quotes.swap':
            require_chain(args['chain_id']);require_address(args['token_in']);require_address(args['token_out'])
            if 'pool' not in args:
                return {'chain_id':args['chain_id'],'quote':None,'state':'unavailable','reason':'Explicit Rootstock pool required; no SOR route optimization or automatic pool guessing','quote_executable':False}
            reg=load_registry(self.registry_dir/CHAIN_IDS[args['chain_id']],allow_unpinned=False)
            router=reg.resolve('Router')['address']
            return direct_pool_quote(self._rpc(args['chain_id']),router,args['pool'],args['token_in'],args['token_out'],args['amount_raw'],args.get('sender'))
        if name in ('transactions.prepare','transactions.simulate'):
            chain=args['chain_id'];require_chain(chain)
            try: tx=json.loads(args['transaction_json'])
            except ValueError as e:raise CapabilityError('Invalid transaction JSON') from e
            if not isinstance(tx,dict) or not all(k in tx for k in ('from','to','data')):raise CapabilityError('Transaction requires from/to/data')
            target=require_address(tx['to']).lower()
            reg=load_registry(self.registry_dir/CHAIN_IDS[chain],allow_unpinned=False)
            allowed={address.lower() for contracts in reg.tasks.values() for address in contracts.values() if int(address,16)!=0}
            if target not in allowed:raise CapabilityError('Target absent from source-pinned Rootstock deployment registry')
            if name=='transactions.simulate':return simulate_known_transaction(self._rpc(chain),tx,allowed)
            import re
            require_address(tx['from'])
            if set(tx)-{'from','to','data','value'}:raise CapabilityError('Unexpected transaction keys')
            data=tx['data'];value=tx.get('value','0x0')
            if not isinstance(data,str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*',data) or len(data)>16004:raise CapabilityError('Invalid calldata')
            if not isinstance(value,str) or not re.fullmatch(r'0x(?:0|[1-9a-fA-F][0-9a-fA-F]*)',value):raise CapabilityError('Invalid value')
            return {'chain_id':chain,'unsigned_transaction':{'from':tx['from'],'to':tx['to'],'data':data,'value':value},
               'status':'UNSIGNED_UNAPPROVED','execution_authorized':False,'signing_available':False,
               'warning':'Prepared bytes are untrusted; an independent signer must validate exact effects and policy.'}
        if name=='transactions.status':return tx_status(self._rpc(args['chain_id']),args['hash'])
        if name=='policy.evaluate':
            require_chain(args['chain_id']);action=args['action']
            if action in ('read','inspect','observe'):
                return {'action':action,'decision':'ALLOW_READ','enforced_by':'read-only tool capability registry','signing_authority':False}
            return {'action':action,'decision':'DENY','reason':'No independent authenticated policy executor or signer is configured','signing_authority':False}
        if name=='skills.list':
            return [{'name':p.parent.name,'path':'bundled_skills/'+p.parent.name+'/SKILL.md', 'installed_with_toolkit':True} for p in sorted(self._skillroot().glob('*/SKILL.md'))]
        if name=='skills.read':
            skill=args['name']
            if not all(c.isascii() and (c.islower() or c.isdigit() or c=='-') for c in skill) or skill.startswith('-') or skill.endswith('-') or '--' in skill:
                raise CapabilityError('Invalid skill identifier')
            file=self._skillroot()/skill/'SKILL.md'
            if not file.is_file(): raise CapabilityError('Unknown bundled skill')
            if file.is_symlink(): raise CapabilityError('Symlink skill refused')
            return {'name':skill,'content':file.read_text(encoding='utf8'),'source':'built-in verified package content'}
        raise CapabilityError('Not implemented')
