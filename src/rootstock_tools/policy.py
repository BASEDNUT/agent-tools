"""External, process-scoped read-tool admission: cannot authorize financial writes.

Policies are read by a trusted launcher and are deliberately not editable via SDK, CLI,
MCP or HTTP. Not a wallet guard or an OS sandbox: processes with unrestricted shell
access may bypass this adapter. No private keys or externally supplied approval tokens.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

class PolicyError(ValueError): pass

def _unique_pairs(pairs):
    result={}
    for k,v in pairs:
        if k in result: raise PolicyError('Duplicate policy field: '+k)
        result[k]=v
    return result

class PolicyGate:
    def __init__(self,path:Path,agent_id:str):
        p=Path(path).expanduser()
        if not p.is_file() or p.is_symlink(): raise PolicyError('Trusted policy must be a regular non-symlink file')
        raw=p.read_bytes()
        if len(raw)>64_000:raise PolicyError('Policy exceeds size limit')
        try:policy=json.loads(raw,object_pairs_hook=_unique_pairs)
        except (ValueError,UnicodeError) as e:raise PolicyError('Invalid agent policy') from e
        if not isinstance(policy,dict) or set(policy)!={'version','agents'} or type(policy['version']) is not int or policy['version']!=1:
            raise PolicyError('Unsupported policy format')
        agents=policy['agents']
        if not isinstance(agents,dict) or not 0<len(agents)<=128:raise PolicyError('Invalid agents table')
        for identity,spec in agents.items():
            if not isinstance(identity,str) or len(identity)>80 or not isinstance(spec,dict) or set(spec)!={'allow','chains'}:
                raise PolicyError('Invalid agent scope')
            if not isinstance(spec['allow'],list) or not 0<len(spec['allow'])<=100 or any(
                not isinstance(cap,str) or cap=='*' or not cap or len(cap)>120 for cap in spec['allow']):
                raise PolicyError('Invalid allowlist; unbounded wildcard is not permitted')
            if not isinstance(spec['chains'],list) or any(type(c) is not int or c not in (8453,84532) for c in spec['chains']):
                raise PolicyError('Invalid chain scope')
        if not isinstance(agent_id,str) or agent_id not in agents:
            raise PolicyError('Agent identity absent from policy (fail closed)')
        self.principal=agent_id
        self.scope=agents[agent_id]
        self.policy_sha256=hashlib.sha256(raw).hexdigest()

    def check(self,name:str,args:dict):
        permitted=name in self.scope['allow'] or any(cap.endswith('.*') and
            name.startswith(cap[:-1]) for cap in self.scope['allow'])
        if not permitted:raise PolicyError('Capability denied by process policy')
        chain=args.get('chain_id')
        if chain is not None and chain not in self.scope['chains']:
            raise PolicyError('Chain denied by process policy')
        return {'principal':self.principal,'policy_sha256':self.policy_sha256}
