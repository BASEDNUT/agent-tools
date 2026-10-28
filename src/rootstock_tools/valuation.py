"""Source-qualified optional USD arithmetic. Operator data is never called oracle verified.

Price sheets are installed through the trusted launcher, not through agent tool args.
Matched chain+block snapshots are necessary, but NOT sufficient for price authenticity.
"""
from __future__ import annotations
import json
from pathlib import Path
from decimal import Decimal, InvalidOperation, localcontext
from .rpc import ChainError, require_address, require_chain, HEX32

class PriceError(ChainError):pass

def decimal_price(text):
    if not isinstance(text,str) or not 1<=len(text)<=70: raise PriceError('USD price must be a decimal string')
    try: d=Decimal(text)
    except InvalidOperation as e:raise PriceError('Invalid USD decimal price') from e
    if not d.is_finite() or d<=0 or d.as_tuple().exponent < -30 or d > Decimal('1e30'):
        raise PriceError('Unsafe or nonpositive USD price')
    return d

class PriceBook:
    def __init__(self,path):
        p=Path(path).expanduser()
        if not p.is_file() or p.is_symlink() or p.stat().st_size>60_000:raise PriceError('Operator price file missing or unsafe')
        def reject_dupes(pairs):
            d={}
            for k,v in pairs:
                if k in d:raise PriceError('Duplicate JSON field in price book')
                d[k]=v
            return d
        try: data=json.loads(p.read_text(encoding='utf8'),object_pairs_hook=reject_dupes)
        except (UnicodeError,ValueError) as e:raise PriceError('Invalid price book') from e
        if not isinstance(data,dict) or set(data)!={'version','chain_id','block_number','block_hash','source','prices'} or type(data['version']) is not int or data['version']!=1:
            raise PriceError('Unsupported price book schema')
        self.chain_id=data['chain_id'];require_chain(self.chain_id)
        self.block_number=data['block_number'];self.block_hash=data['block_hash']
        if type(self.block_number) is not int or self.block_number<0 or not HEX32.fullmatch(str(self.block_hash)):
            raise PriceError('Price snapshot block identity missing')
        self.source=data['source']
        if not isinstance(self.source,str) or not 1<=len(self.source)<=180:
            raise PriceError('Explicit operator pricing provenance is required')
        raw=data['prices']
        if not isinstance(raw,list) or not 1<=len(raw)<=256:raise PriceError('Invalid price rows')
        self.prices={}
        for row in raw:
            if not isinstance(row,dict) or set(row)!={'token','usd'}:raise PriceError('Invalid price row')
            token=require_address(row['token']).lower()
            if token in self.prices:raise PriceError('Duplicate asset in operator price book')
            self.prices[token]=decimal_price(row['usd'])

    def assert_snapshot(self,obs):
        if obs['chain_id']!=self.chain_id or obs['observed_head_block']!=self.block_number or obs['observed_head_hash'].lower()!=self.block_hash.lower():
            raise PriceError('Price sheet chain or block hash does not match observed reserves')

def value_pool(observation,book:PriceBook|None):
    base={'chain_id':observation['chain_id'],'pool':observation['pool'],
          'block_number':observation['observed_head_block'],'block_hash':observation['observed_head_hash'],
          'balance_source':'Rootstock Vault getPoolTokenInfo at pinned block',
          'currency':'USD','value':None,'state':'unavailable','price_source_verified':False}
    if book is None:
        return {**base,'reason':'No operator-supplied, block-matched USD price sheet; prices not inferred','tokens':observation['tokens']}
    book.assert_snapshot(observation)
    rows=[]
    with localcontext() as ctx:
        ctx.prec=78
        total=Decimal(0)
        for token in observation['tokens']:
            addr=token['address'].lower();raw=token.get('balance_raw');dec=token.get('decimals')
            price=book.prices.get(addr)
            if price is None or raw is None or type(dec) is not int or not 0<=dec<=255:
                return {**base,'reason':'Incomplete reserve, token decimals or operator price for '+addr,
                        'operator_price_source':book.source,'missing_token':addr}
            if not isinstance(raw,str) or not raw.isdecimal() or len(raw)>79:raise PriceError('Invalid raw token balance')
            amount=Decimal(raw)/(Decimal(10)**dec)
            value=amount*price;total+=value
            rows.append({'token':addr,'amount':str(amount),'decimals':dec,'price_usd':str(price),'contribution_usd':str(value)})
        return {**base,'value':str(total),'state':'derived_from_operator_prices',
                'operator_price_source':book.source,'price_source_verified':False,
                'price_quote_block':book.block_number,'tokens':rows,
                'warning':'Arithmetic is reproducible; authenticity of operator-supplied USD prices is not established. Never treat as audited TVL or executable valuation.'}

def value_volume(volume,book:PriceBook|None,asset_decimals:dict[str,int]):
    if book is None:return {'value':None,'state':'unavailable','reason':'No operator pricing snapshot'}
    if volume.get('state')=='incomplete_timestamps':return {'value':None,'state':'unavailable','reason':'Some indexed swap blocks lack timestamps'}
    rows=volume.get('input_volume_raw_by_token',{})
    total=Decimal(0);out=[]
    with localcontext() as ctx:
        ctx.prec=78
        for token,amount in rows.items():
            dec=asset_decimals.get(token.lower());price=book.prices.get(token.lower())
            if price is None or type(dec) is not int or not 0<=dec<=255:
                return {'value':None,'state':'unavailable','reason':'Missing price/decimals for indexed swap token '+token}
            v=Decimal(amount)*price/(Decimal(10)**dec)
            total+=v;out.append({'token':token,'volume_usd':str(v)})
    return {'value':str(total),'state':'derived_from_operator_prices','components':out,'price_source_verified':False}
