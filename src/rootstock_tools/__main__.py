"""rootstock: read-only CLI and MCP server using the same core SDK."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
from .core import Toolchain, CAPABILITIES, CapabilityError
from .policy import PolicyError
from .registry import RegistryError
from .rpc import ChainError, parse_quantity
from .bootstrap import fetch_registries

def main(argv=None):
    parser=argparse.ArgumentParser(prog='rootstock',description='Standalone read-only Rootstock/Orchard CLI, SDK and MCP server')
    parser.add_argument('--policy-file',type=Path,default=None,help='Trusted launcher-supplied read-only agent permission manifest')
    parser.add_argument('--agent-id',default=None,help='Agent identity asserted by the trusted launcher (not cryptographic authentication)')
    parser.add_argument('--registry-dir',type=Path,default=None,help='Canonical deployment JSON folder (or ROOTSTOCK_REGISTRY_DIR)')
    parser.add_argument('--allow-unpinned',action='store_true',help='Research fixtures only; untrusted source will be labeled')
    parser.add_argument('--allow-local-rpc',action='store_true',help='Allow localhost HTTP RPC for development tests')
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('networks',help='Known chains and deployment-file provenance')
    call=sub.add_parser('call',help='Invoke a shared SDK capability from CLI (JSON args)')
    call.add_argument('name',choices=sorted(CAPABILITIES))
    call.add_argument('--args',default='{}',help='JSON object; quote safely in shell')
    index=sub.add_parser('index',help='Explicit local SQLite event index')
    ix=index.add_subparsers(dest='index_command',required=True)
    ins=ix.add_parser('sync',help='Operator-initiated local event sync, no chain writes')
    ins.add_argument('--chain',required=True,type=int);ins.add_argument('--from-block',required=True,type=int)
    ins.add_argument('--to-block',required=True,type=int);ins.add_argument('--chunk',type=int,default=250)
    ins.add_argument('--index-path',type=Path)
    ist=ix.add_parser('status',help='List stored checkpoints');ist.add_argument('--chain',required=True,type=int)
    follow=ix.add_parser('follow',help='Foreground bounded index daemon; local database writes, no chain writes')
    follow.add_argument('--chain',required=True,type=int);follow.add_argument('--from-block',type=int)
    follow.add_argument('--interval',type=float,default=15.0)
    follow.add_argument('--max-polls',type=int,default=0)
    follow.add_argument('--max-blocks-per-poll',type=int,default=1000)
    follow.add_argument('--rewind',type=int,default=12)
    follow.add_argument('--index-path',type=Path)
    ist.add_argument('--index-path',type=Path)

    sub.add_parser('capabilities',help='List implemented read-only SDK/MCP operations')
    res=sub.add_parser('resolve',help='Resolve pinned deployment contract by exact name')
    res.add_argument('--chain',required=True,type=int)
    res.add_argument('--name',required=True)
    res.add_argument('--task')
    rpc=sub.add_parser('rpc'); rr=rpc.add_subparsers(dest='rpc_command',required=True)
    rpcstat=rr.add_parser('status');rpcstat.add_argument('--chain',required=True,type=int)
    pools=sub.add_parser('pools');pp=pools.add_subparsers(dest='pools_command',required=True)
    li=pp.add_parser('list');li.add_argument('--chain',required=True,type=int)
    li.add_argument('--from-block',type=int,required=True);li.add_argument('--to-block',type=int,required=True)
    li.add_argument('--limit',type=int,default=250)
    skills=sub.add_parser('skills');ss=skills.add_subparsers(dest='skill_command',required=True)
    ss.add_parser('list');sread=ss.add_parser('read');sread.add_argument('name')
    si=ss.add_parser('install');si.add_argument('--target',type=Path,required=True,help='Explicit destination parent directory')
    setup=sub.add_parser('setup');su=setup.add_subparsers(dest='setup_command',required=True)
    sd=su.add_parser('registries');sd.add_argument('--dest',type=Path,default=None)
    watch=sub.add_parser('watch',help='Foreground polling of Rootstock PoolRegistered events; read-only')
    watch.add_argument('--chain',required=True,type=int)
    watch.add_argument('--from-block',required=True,type=int)
    watch.add_argument('--interval',type=float,default=15.0)
    watch.add_argument('--max-polls',type=int,default=0,help='0 = continue until interrupted')
    sub.add_parser('mcp',help='Run MCP stdio server; do not print logging to stdout')
    api=sub.add_parser('api',help='Run loopback-only read-only JSON/HTTP API')
    api.add_argument('--port',type=int,default=8765)
    ns=parser.parse_args(argv)
    try:
        kit=Toolchain(ns.registry_dir,allow_unpinned=ns.allow_unpinned,allow_local_rpc=ns.allow_local_rpc,policy_file=ns.policy_file,agent_id=ns.agent_id)
        if ns.command=='watch':
            from time import sleep
            if not 0.5<=ns.interval<=3600:raise CapabilityError('Interval must be 0.5–3600 seconds')
            if ns.from_block<0 or ns.max_polls<0:raise CapabilityError('Invalid watch range')
            rpc=kit._rpc(ns.chain);cursor=ns.from_block;count=0
            try:
                while ns.max_polls==0 or count<ns.max_polls:
                    rpc.check_chain();head=parse_quantity(rpc.call('eth_blockNumber',[]))
                    while cursor<=head:
                        end=min(head,cursor+1999)
                        event=rpc.pool_events(cursor,end)
                        print(json.dumps({'ok':True,'effect':'read','result':event},sort_keys=True),flush=True)
                        cursor=end+1
                    count+=1
                    if ns.max_polls==0 or count<ns.max_polls:sleep(ns.interval)
            except KeyboardInterrupt:pass
            return 0
        if ns.command=='mcp':
            from .mcp import Server
            Server(kit).serve();return 0
        if ns.command=='api':
            from .http_api import serve
            serve(kit,ns.port);return 0
        if ns.command=='setup':
            result=fetch_registries(ns.dest or kit.registry_dir)
        elif ns.command=='skills' and ns.skill_command=='install':
            # Explicit local copy, never auto-install from an untrusted source.
            target=ns.target.expanduser()
            if any(part.is_symlink() for part in (target,*target.parents)):
                raise CapabilityError('Symlink target path refused')
            if not target.is_dir() and target.exists(): raise CapabilityError('Target must be a directory')
            entries=kit.run('skills.list')
            for entry in entries:
                dst=target/entry['name']
                if dst.exists() or dst.is_symlink(): raise CapabilityError('Refusing existing destination '+str(dst))
            target.mkdir(parents=True,exist_ok=True)
            installed=[]
            for entry in entries:
                source=kit._skillroot()/entry['name']
                dst=target/entry['name']
                shutil.copytree(source,dst,symlinks=False)
                installed.append(str(dst))
            result={'installed_paths':installed,'source':'local bundled skill package'}
        elif ns.command=='index':
            if ns.index_path is not None:
                from .indexer import EventIndex
                kit.index=EventIndex(ns.index_path)
            if ns.index_command=='sync':
                result=kit.index.sync(kit._rpc(ns.chain),ns.from_block,ns.to_block,chunk=ns.chunk)
            elif ns.index_command=='follow':
                from time import sleep
                from .rpc import CHAIN_CONFIG
                if not 0.5<=ns.interval<=3600: raise CapabilityError('Invalid follow interval')
                if type(ns.max_polls) is not int or ns.max_polls<0 or not 1<=ns.max_blocks_per_poll<=2000 or not 0<=ns.rewind<=500:
                    raise CapabilityError('Invalid follow limit')
                if ns.from_block is not None and ns.from_block<0:raise CapabilityError('Invalid starting block')
                if ns.from_block is not None:
                    cursor=ns.from_block
                else:
                    current=kit.index.events(ns.chain,limit=1)
                    windows=current.get('scanned_intervals',[])
                    if not windows:raise CapabilityError('First run needs an explicit --from-block (deployment height is not assumed)')
                    cursor=max(CHAIN_CONFIG[ns.chain]['from_block'],max(w['to_block'] for w in windows)-ns.rewind)
                rpc=kit._rpc(ns.chain);rounds=0
                try:
                    while ns.max_polls==0 or rounds<ns.max_polls:
                        rpc.check_chain();head=parse_quantity(rpc.call('eth_blockNumber',[]))
                        if cursor<=head:
                            end=min(head,cursor+ns.max_blocks_per_poll-1)
                            output=kit.index.sync(rpc,cursor,end,chunk=min(250,ns.max_blocks_per_poll))
                            print(json.dumps({'ok':True,'effect':'local_write','result':output},sort_keys=True),flush=True)
                            cursor=end+1
                        else:
                            print(json.dumps({'ok':True,'effect':'read','idle_at':head,'next_block':cursor},sort_keys=True),flush=True)
                        rounds+=1
                        if ns.max_polls==0 or rounds<ns.max_polls:sleep(ns.interval)
                except KeyboardInterrupt:pass
                return 0
            else:result=kit.run('history.status',{'chain_id':ns.chain})
        elif ns.command=='call':
            try: args=json.loads(ns.args)
            except ValueError as exc: raise CapabilityError('Invalid JSON arguments') from exc
            if not isinstance(args,dict):raise CapabilityError('Capability arguments must be a JSON object')
            result=kit.run(ns.name,args)
        else:
            if ns.command=='networks': name,args='registry.list_networks',{}
            elif ns.command=='resolve':
                name,args='registry.resolve_deployment',{'chain_id':ns.chain,'name':ns.name}
                if ns.task: args['task']=ns.task
            elif ns.command=='capabilities': name,args='capabilities.list',{}
            elif ns.command=='rpc': name,args='rpc.get_health',{'chain_id':ns.chain}
            elif ns.command=='pools': name,args='pools.list',{'chain_id':ns.chain,'from_block':ns.from_block,'to_block':ns.to_block,'limit':ns.limit}
            elif ns.command=='skills':
                name,args=('skills.list',{}) if ns.skill_command=='list' else ('skills.read',{'name':ns.name})
            result=kit.run(name,args)
        print(json.dumps({'ok':True,'effect':('local_write' if ns.command=='index' and ns.index_command=='sync' else 'read' if ns.command!='setup' and not (ns.command=='skills' and ns.skill_command=='install') else 'local_setup'),'result':result},sort_keys=True,indent=2))
        return 0
    except (RegistryError, ChainError, CapabilityError, PolicyError, OSError, ValueError) as exc:
        print(json.dumps({'ok':False,'error':str(exc)},sort_keys=True),file=sys.stderr)
        return 2

if __name__=='__main__': raise SystemExit(main())
