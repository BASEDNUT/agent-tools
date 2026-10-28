"""Shared on-chain read capabilities and exact-transaction dry-run interface."""
from __future__ import annotations
import json
import re
from .rpc import ChainError, require_address, require_chain, HEX32, parse_quantity, CHAIN_CONFIG
from .evm import encode_call, addr_word, decode_word, decode_address, decode_addresses, decode_string, decode_dynamic_uint_array

def _view(rpc,target,signature,*arg_words,block='latest'):
    require_address(target)
    result=rpc.call('eth_call',[{'to':target,'data':encode_call(signature,*arg_words)},block])
    if not isinstance(result,str):raise ChainError('Malformed contract return value')
    return result

def _verify_snapshot(rpc, block_number: int, expected_hash: str) -> None:
    """Reject a reorg observed between pinned-block read operations."""
    observed=rpc.call('eth_getBlockByNumber',[hex(block_number),False])
    hash_value=observed.get('hash') if isinstance(observed,dict) else None
    if not HEX32.fullmatch(str(hash_value)) or hash_value.lower()!=expected_hash.lower():
        raise ChainError('Snapshot block changed during reads')

def _metadata(rpc,addr,block='latest'):
    result={}
    for field,sig in [('decimals','decimals()'),('name','name()'),('symbol','symbol()'),('total_supply_raw','totalSupply()')]:
        try:
            res=_view(rpc,addr,sig,block=block)
            if field in ('name','symbol'):value=decode_string(res)
            else:value=decode_word(res)
            if field=='decimals' and value is not None and value>255:raise ChainError('Invalid ERC20 decimals')
            result[field]=str(value) if field=='total_supply_raw' else value
        except (ChainError,ValueError,IndexError):result[field]=None
    return result

def asset_lookup(rpc,address:str,block='latest'):
    require_address(address);rpc.check_chain()
    # Even metadata is an on-chain observation: prevent silently mixing code and
    # ERC20 fields from different heads. This is provider-relative, not finality.
    head=parse_quantity(rpc.call('eth_blockNumber',[]))
    tag=hex(head)
    header=rpc.call('eth_getBlockByNumber',[tag,False])
    bh=header.get('hash') if isinstance(header,dict) else None
    if not HEX32.fullmatch(str(bh)): raise ChainError('Missing asset snapshot block hash')
    code=rpc.call('eth_getCode',[address,tag])
    if not isinstance(code,str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*',code):raise ChainError('Bad contract code response')
    result={'chain_id':rpc.chain_id,'address':address,'is_contract':code!='0x','block_tag':tag,
            'observed_head_block':head,'observed_head_hash':bh,
            'metadata_source':'onchain_erc20_calls','source_type':'live_rpc','code_hash_verified':False}
    result.update(_metadata(rpc,address,tag) if code!='0x' else {x:None for x in ('decimals','name','symbol','total_supply_raw')})
    _verify_snapshot(rpc,head,bh)
    return result

def wrapper_underlying(rpc,address):
    """ERC4626-compatible wrapper introspection; explicitly source-tagged, block pinned."""
    require_address(address);rpc.check_chain()
    head=parse_quantity(rpc.call('eth_blockNumber',[]));tag=hex(head)
    block=rpc.call('eth_getBlockByNumber',[tag,False]);bh=block.get('hash') if isinstance(block,dict) else None
    if not HEX32.fullmatch(str(bh)):raise ChainError('Missing wrapper snapshot block hash')
    base={'chain_id':rpc.chain_id,'wrapper':address,'observed_head_block':head,'observed_head_hash':bh,
          'classification':'ERC4626-compatible response; Rootstock wrapper identity is not inferred',
          'source':'ERC4626 eth_call at pinned block'}
    try:
        asset=decode_address(_view(rpc,address,'asset()',block=tag))
        if int(asset,16)==0:return {**base,'underlying':None,'state':'unavailable','reason':'ERC4626 asset() returned zero'}
    except (ChainError,ValueError):
        return {**base,'underlying':None,'state':'unavailable','reason':'ERC4626 asset() unsupported or failed; no guessed underlying'}
    underlying_metadata=_metadata(rpc,asset,tag)
    wrapper_metadata=_metadata(rpc,address,tag)
    share_decimals=wrapper_metadata.get('decimals')
    shares_in_raw=None;assets_out_raw=None
    if type(share_decimals) is int and 0<=share_decimals<=77:
        shares_in_raw=10**share_decimals
        try:
            assets_out_raw=decode_word(_view(rpc,address,'convertToAssets(uint256)',f'{shares_in_raw:064x}',block=tag))
        except (ChainError,ValueError):pass
    _verify_snapshot(rpc,head,bh)
    return {**base,'underlying':asset,'state':'observed',
        'underlying_metadata':underlying_metadata,
        'wrapper_metadata':wrapper_metadata,
        'one_share_in_raw':str(shares_in_raw) if shares_in_raw is not None else None,
        'one_share_assets_out_raw':str(assets_out_raw) if assets_out_raw is not None else None,
        'rate_source':'ERC4626 convertToAssets(10**shareDecimals) eth_call; null if unavailable',
        'warning':'Conversion rate is a point-in-time contract quotation, not a guaranteed redeemable value'}

def pool_inspect(rpc,pool:str):
    require_address(pool);rpc.check_chain()
    vault=CHAIN_CONFIG[rpc.chain_id]['vault']
    head=parse_quantity(rpc.call('eth_blockNumber',[]))
    block=rpc.call('eth_getBlockByNumber',[hex(head),False]);bh=block.get('hash') if isinstance(block,dict) else None
    tag=hex(head)
    tokens=decode_addresses(_view(rpc,vault,'getPoolTokens(address)',addr_word(pool),block=tag),cap=32)
    if not HEX32.fullmatch(str(bh)):raise ChainError('Head hash required for pool observation')
    # Read pool configuration through the Rootstock Vault, never a Balancer endpoint.
    static_swap_fee_raw=None
    try:
        static_swap_fee_raw=str(decode_word(_view(rpc,vault,'getStaticSwapFeePercentage(address)',addr_word(pool),block=tag)))
    except (ChainError,ValueError,IndexError):pass
    token_rates_raw=None; decimal_scaling_factors_raw=None
    try:
        raw_rates=_view(rpc,vault,'getPoolTokenRates(address)',addr_word(pool),block=tag)
        factors=decode_dynamic_uint_array(raw_rates,0,cap=32)
        rates=decode_dynamic_uint_array(raw_rates,1,cap=32)
        if len(factors)==len(tokens) and len(rates)==len(tokens):
            token_rates_raw=[str(x) for x in rates]
            decimal_scaling_factors_raw=[str(x) for x in factors]
    except (ChainError,ValueError,IndexError):pass
    balances=None; balances_reason=None
    try:
        info=_view(rpc,vault,'getPoolTokenInfo(address)',addr_word(pool),block=tag)
        toks_info=decode_addresses(info,cap=32)
        balances_raw=decode_dynamic_uint_array(info,2,cap=32)
        if [x.lower() for x in toks_info]!=[x.lower() for x in tokens] or len(balances_raw)!=len(tokens):
            raise ChainError('Vault token-info array differs from pool tokens')
        balances=[str(x) for x in balances_raw]
    except ChainError:
        balances_reason='Vault.getPoolTokenInfo unavailable or mismatched; no reserve guesses'
    _verify_snapshot(rpc,head,bh)
    return {'chain_id':rpc.chain_id,'vault':vault,'pool':pool,'tokens':[{'address':t,**_metadata(rpc,t,tag),
        'balance_raw':None if balances is None else balances[i]} for i,t in enumerate(tokens)],
        'observed_head_block':head,'observed_head_hash':bh,'source':'Vault.getPoolTokens + getPoolTokenInfo + token eth_call','balance_reason':balances_reason,
        'tvl_usd':None,'swap_fee':None,'static_swap_fee_percentage_18':static_swap_fee_raw,
        'token_rates_18':token_rates_raw,'decimal_scaling_factors_18':decimal_scaling_factors_raw,
        'hooks':None,'pool_math_type':'UNKNOWN',
        'warning':'RPC eth_call operations pinned to one block number, but not an independently proven canonical chain view'}

def wallet_balance(rpc,wallet:str,token:str):
    require_address(wallet);require_address(token);rpc.check_chain()
    head=parse_quantity(rpc.call('eth_blockNumber',[]));tag=hex(head)
    block=rpc.call('eth_getBlockByNumber',[tag,False]);bh=block.get('hash') if isinstance(block,dict) else None
    if not HEX32.fullmatch(str(bh)):raise ChainError('Missing wallet snapshot block hash')
    raw=decode_word(_view(rpc,token,'balanceOf(address)',addr_word(wallet),block=tag))
    _verify_snapshot(rpc,head,bh)
    return {'chain_id':rpc.chain_id,'wallet':wallet,'token':token,'balance_raw':str(raw),
        'token_metadata':_metadata(rpc,token,tag),'observed_head_block':head,'observed_head_hash':bh,
        'source':'ERC20.balanceOf eth_call at pinned block',
        'portfolio_coverage':'explicit token only, not exhaustive'}

def wallet_balances(rpc,wallet:str,tokens:list[str]):
    """Consistent pinned-block multi-asset balances; caller must supply all token addresses."""
    require_address(wallet)
    if not isinstance(tokens,list) or not 1<=len(tokens)<=32:raise ChainError('Must supply 1..32 explicit tokens')
    if any(not isinstance(t,str) for t in tokens):raise ChainError('Invalid token address')
    canonical=[require_address(t).lower() for t in tokens]
    if len(set(canonical))!=len(canonical):raise ChainError('Duplicate asset address')
    rpc.check_chain()
    head=parse_quantity(rpc.call('eth_blockNumber',[]));tag=hex(head)
    block=rpc.call('eth_getBlockByNumber',[tag,False]);bh=block.get('hash') if isinstance(block,dict) else None
    if not HEX32.fullmatch(str(bh)):raise ChainError('Missing account snapshot block hash')
    assets=[]
    for token in canonical:
        raw=decode_word(_view(rpc,token,'balanceOf(address)',addr_word(wallet),block=tag))
        assets.append({'token':token,'balance_raw':str(raw),'metadata':_metadata(rpc,token,tag)})
    _verify_snapshot(rpc,head,bh)
    return {'chain_id':rpc.chain_id,'wallet':wallet,'assets':assets,
       'observed_head_block':head,'observed_head_hash':bh,'state':'observed',
       'coverage':'user-enumerated assets only; not an exhaustive wallet balance',
       'source':'explicit ERC20.balanceOf and token metadata, same provider block'}

def tx_status(rpc,hash_value:str):
    if not HEX32.fullmatch(str(hash_value)):raise ChainError('Invalid tx hash')
    rpc.check_chain()
    rec=rpc.call('eth_getTransactionReceipt',[hash_value])
    if rec is None:return {'chain_id':rpc.chain_id,'transaction_hash':hash_value,'state':'not_found','source':'live_rpc','finality_verified':False}
    if not isinstance(rec,dict):raise ChainError('Malformed receipt')
    observed_tx=rec.get('transactionHash')
    if observed_tx is not None and (not HEX32.fullmatch(str(observed_tx)) or observed_tx.lower()!=hash_value.lower()):
        raise ChainError('RPC receipt transaction hash mismatch')
    status=parse_quantity(rec['status']) if rec.get('status') is not None else None
    if status is not None and status not in (0,1):
        raise ChainError('Invalid receipt status (expected 0 or 1)')
    bn=parse_quantity(rec['blockNumber']) if rec.get('blockNumber') is not None else None
    bh=rec.get('blockHash')
    if bn is not None and not HEX32.fullmatch(str(bh)):raise ChainError('Receipt missing block hash')
    if bn is None:return {'chain_id':rpc.chain_id,'transaction_hash':hash_value,'state':'pending','success':None,'block_number':None,'block_hash':None,'source':'live_rpc','finality_verified':False}
    head=parse_quantity(rpc.call('eth_blockNumber',[]))
    if head<bn:raise ChainError('Receipt block ahead of RPC head')
    block=rpc.call('eth_getBlockByNumber',[hex(bn),False]);canonical=block.get('hash') if isinstance(block,dict) else None
    if not HEX32.fullmatch(str(canonical)):raise ChainError('Cannot verify included receipt against block header')
    if canonical.lower()!=bh.lower():raise ChainError('Receipt block is no longer canonical at this RPC')
    return {'chain_id':rpc.chain_id,'transaction_hash':hash_value,'state':'included',
        'success':None if status is None else status==1,'block_number':bn,'block_hash':bh,
        'head_block':head,'confirmations':head-bn+1,'canonical_at_provider_head':True,
        'source':'RPC receipt checked against RPC block hash; independent finality not verified','finality_verified':False}

def simulate_known_transaction(rpc,tx:dict, allowed_targets:set[str]):
    """Eth_call dry-run ONLY; cannot send, sign, or grant permissions."""
    rpc.check_chain()
    if not isinstance(tx,dict) or set(tx)-{'from','to','data','value'}:raise ChainError('Invalid transaction keys')
    to=require_address(tx.get('to'));from_=require_address(tx.get('from'))
    if to.lower() not in allowed_targets:raise ChainError('Target not in pinned Rootstock registry; simulation denied')
    data=tx.get('data','0x')
    if not isinstance(data,str) or len(data)>16004 or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*',data):raise ChainError('Invalid or oversized transaction calldata')
    val=tx.get('value','0x0')
    if not isinstance(val,str) or not re.fullmatch(r'0x(?:0|[1-9a-fA-F][0-9a-fA-F]*)',val):raise ChainError('Invalid native value')
    result=rpc.call('eth_call',[{'from':from_,'to':to,'data':data,'value':val},'latest'])
    if not isinstance(result,str) or not re.fullmatch(r'0x(?:[0-9a-fA-F]{2})*',result):raise ChainError('Invalid simulation return bytes')
    return {'chain_id':rpc.chain_id,'transaction':{'from':from_,'to':to,'data':data,'value':val},
       'simulation':'eth_call_success','return_data':result,'broadcast':False,'signed':False,
       'approval_granted':False,'source':'configured chain RPC','warning':'eth_call success is NOT an execution guarantee, safety approval, transaction preview, or MEV protection'}

def explicit_graph(pools:list[dict],chain_id:int):
    require_chain(chain_id)
    if not isinstance(pools,list) or len(pools)>50:raise ChainError('Too many pools')
    nodes={};edges=[]
    for p in pools:
        if not isinstance(p,dict) or not isinstance(p.get('tokens'),list):raise ChainError('Invalid pool record')
        pool=require_address(p.get('pool')).lower()
        tok=[]
        for item in p['tokens']:
            a=require_address(item.get('address') if isinstance(item,dict) else item).lower()
            if a not in tok:tok.append(a)
            nodes[a]={'id':a,'kind':'asset','chain_id':chain_id}
        edges.append({'id':pool,'kind':'pool_hyperedge','tokens':tok,'chain_id':chain_id,'source':p.get('source','provided_pool_data')})
    return {'chain_id':chain_id,'nodes':list(nodes.values()),'edges':edges,
        'orchard_labels':'not_assigned_without_rootstock_structure_evidence',
        'source':'explicit pool-token observations; no inferred Rootstock Grove/Graft labels'}

def direct_pool_quote(rpc,router,pool,token_in,token_out,amount_raw,sender=None):
    """Query one explicitly named V3 pool via Rootstock router. No SOR, no tx execution."""
    for a in (router,pool,token_in,token_out):require_address(a)
    if token_in.lower()==token_out.lower():raise ChainError('Swap assets must differ')
    if not isinstance(amount_raw,str) or not re.fullmatch(r'(?:0|[1-9][0-9]{0,77})',amount_raw):raise ChainError('Invalid raw token amount')
    amount=int(amount_raw)
    if amount<=0 or amount>=2**256:raise ChainError('Invalid swap size')
    sender=sender or '0x'+'0'*40;require_address(sender)
    rpc.check_chain()
    head=parse_quantity(rpc.call('eth_blockNumber',[]));tag=hex(head)
    block=rpc.call('eth_getBlockByNumber',[tag,False]);bh=block.get('hash') if isinstance(block,dict) else None
    if not HEX32.fullmatch(str(bh)):raise ChainError('Missing quote source block hash')
    # Membership and quote are from the same fixed block, not two shifting latest states.
    tokens=decode_addresses(_view(rpc,CHAIN_CONFIG[rpc.chain_id]['vault'],'getPoolTokens(address)',addr_word(pool),block=tag),cap=32)
    if token_in.lower() not in [x.lower() for x in tokens] or token_out.lower() not in [x.lower() for x in tokens]:
        raise ChainError('Specified swap assets not both members of this Vault pool')
    data=encode_call('querySwapSingleTokenExactIn(address,address,address,uint256,address,bytes)',
                     addr_word(pool),addr_word(token_in),addr_word(token_out),f'{amount:064x}',addr_word(sender),f'{192:064x}',f'{0:064x}')
    raw=rpc.call('eth_call',[{'to':router,'data':data,'from':sender},tag])
    quote=decode_word(raw)
    # Re-fetch the header to detect an observed reorg during computation.
    after=rpc.call('eth_getBlockByNumber',[tag,False]);bh_after=after.get('hash') if isinstance(after,dict) else None
    if not HEX32.fullmatch(str(bh_after)) or bh_after.lower()!=bh.lower():raise ChainError('Quote block changed during request')
    return {'chain_id':rpc.chain_id,'pool':pool,'router':router,'token_in':token_in,'token_out':token_out,
            'amount_in_raw':amount_raw,'amount_out_raw':str(quote),'kind':'single_pool_exact_input',
            'observed_head_block':head,'observed_head_hash':bh,'source_block_tag':tag,
            'route_optimized':False,'quote_executable':False,'signed':False,
            'source':'eth_call Rootstock Router querySwapSingleTokenExactIn',
            'warning':'Quote can expire/change, token amount units must be decoded independently; no slippage or execution authorization included'}
