"""Explicit operator-configured Orchard rules and provisional graph interpretation.

Does not infer token identity or claim to implement the canonical Orchard V25 rank system.
"""
from __future__ import annotations
import json
from pathlib import Path
from decimal import Decimal, InvalidOperation
from .rpc import require_address, require_chain, ChainError
from .services import wallet_balances

class OrchardError(ChainError):pass

class OrchardConfig:
    def __init__(self,path):
        p=Path(path).expanduser()
        if not p.is_file() or p.is_symlink() or p.stat().st_size>32000:
            raise OrchardError('Operator Orchard configuration missing or unsafe')
        def unique(pairs):
            d={}
            for k,v in pairs:
                if k in d:raise OrchardError('Duplicate Orchard configuration field')
                d[k]=v
            return d
        try: data=json.loads(p.read_text(),object_pairs_hook=unique)
        except (ValueError,UnicodeError) as exc:raise OrchardError('Invalid Orchard configuration') from exc
        if not isinstance(data,dict) or set(data)!={'version','chain_id','root_asset','threshold','lp_tokens','source'} or type(data['version']) is not int or data['version']!=1:
            raise OrchardError('Invalid Orchard rule schema')
        self.chain_id=data['chain_id'];require_chain(self.chain_id)
        self.root_asset=require_address(data['root_asset']).lower()
        if not isinstance(data['source'],str) or not 1<=len(data['source'])<=180:raise OrchardError('Source citation required')
        self.source=data['source']
        if not isinstance(data['threshold'],str) or len(data['threshold'])>35:raise OrchardError('Invalid Orchard threshold')
        try: self.threshold=Decimal(data['threshold'])
        except InvalidOperation as exc:raise OrchardError('Invalid Orchard threshold') from exc
        if not self.threshold.is_finite() or not 0<self.threshold<=Decimal(10)**30 or self.threshold.as_tuple().exponent < -18:
            raise OrchardError('Threshold must be positive finite decimal with at most 18 places')
        if not isinstance(data['lp_tokens'],list) or len(data['lp_tokens'])>16:raise OrchardError('Excess LP entries')
        self.lp_tokens=[require_address(x).lower() for x in data['lp_tokens']]
        if len(set(self.lp_tokens+[self.root_asset]))!=len(self.lp_tokens)+1:raise OrchardError('Duplicate/overlapping eligibility tokens')

def eligibility(rpc,wallet:str,rule:OrchardConfig|None):
    if rule is None:return {'state':'unavailable','eligible':None,'reason':'No operator-confirmed Orchard eligibility rules configured; token address and LP set must not be guessed'}
    if rpc.chain_id!=rule.chain_id:raise OrchardError('Orchard rules do not match selected chain')
    observed=wallet_balances(rpc,wallet,[rule.root_asset,*rule.lp_tokens])
    root=observed['assets'][0];dec=root['metadata']['decimals']
    if type(dec) is not int or not 0<=dec<=255:
        return {'state':'unavailable','eligible':None,'reason':'Root token decimals unavailable','balances':observed}
    threshold_raw=rule.threshold*(Decimal(10)**dec)
    if threshold_raw!=threshold_raw.to_integral_value():return {'state':'unavailable','eligible':None,'reason':'Eligibility threshold not representable in token base units'}
    root_pass=int(root['balance_raw'])>=int(threshold_raw)
    lp_pass=[x for x in observed['assets'][1:] if int(x['balance_raw'])>0]
    return {'chain_id':rpc.chain_id,'wallet':wallet,'state':'derived_from_operator_rules',
       'eligible':root_pass or bool(lp_pass),'root_minimum_raw':str(int(threshold_raw)),
       'root_balance_raw':root['balance_raw'],'qualifying_lp_tokens':[x['token'] for x in lp_pass],
       'observed_head_block':observed['observed_head_block'],'observed_head_hash':observed['observed_head_hash'],
       'source':'on-chain ERC20 balances and operator-provided eligibility rule',
       'rule_source':rule.source,'rule_approved_by_project':False,
       'warning':'Configuration is operator supplied; this does not confer API access, rank, membership or signing rights'}

def rooted_structure(graph:dict,rule:OrchardConfig|None):
    if rule is None:return {**graph,'rooted':False,'reason':'Explicit root asset not configured'}
    if graph['chain_id']!=rule.chain_id:raise OrchardError('Rooted graph chain mismatch')
    edge_list=[]
    for edge in graph['edges']:
        distinct=set(edge['tokens']);has_root=rule.root_asset in distinct
        label=('Branch' if len(distinct)==2 else 'Graft' if len(distinct)==3 else 'rooted_other') if has_root else ('Whorl' if len(distinct)>=3 else 'unrooted_pair')
        edge_list.append({**edge,'proposed_orchard_structure':label,'rooted':has_root,'interpretation_status':'provisional_derived'})
    return {**graph,'edges':edge_list,'rooted':True,'root_asset':rule.root_asset,
            'rule_source':rule.source,'structures_are_project_canonical':False,
            'reason':'Basic structural classification only; Grove relations/ranks require approved Orchard model'}
