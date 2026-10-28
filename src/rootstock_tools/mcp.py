"""MCP stdio server, dual era: 2026-07-28 stateless and 2025-11-25 legacy.

JSON-RPC framing and business logic are separate; stdout is wire messages only.
No wallet, transaction, or signing tools exist in this server.
"""
from __future__ import annotations
import json
import sys
from . import __version__
from .core import Toolchain, CAPABILITIES, CapabilityError, schema_for
from .registry import RegistryError
from .rpc import ChainError
from .policy import PolicyError

MODERN='2026-07-28'
LEGACY='2025-11-25'
SERVER_INFO={'name':'rootstock-orchard-readonly','version':__version__}
SUPPORTED=[MODERN,LEGACY]

def error(request_id,code,message,data=None):
    e={'jsonrpc':'2.0','id':request_id,'error':{'code':code,'message':message}}
    if data is not None: e['error']['data']=data
    return e

def ok(request_id,result): return {'jsonrpc':'2.0','id':request_id,'result':result}

def tool_definitions():
    return [{'name':n,'title':n.replace('.',' / '),'description':s['description'],
             'inputSchema':schema_for(n),
             'annotations':{'readOnlyHint':True,'destructiveHint':False,'idempotentHint':True,'openWorldHint': n.startswith(('pools.','rpc.'))}}
            for n,s in sorted(CAPABILITIES.items())]

class Server:
    def __init__(self,toolchain=None):
        self.tools=toolchain or Toolchain()
        self._legacy_initialized=False

    def _respond(self,msg):
        if not isinstance(msg,dict) or msg.get('jsonrpc')!='2.0': return error(None,-32600,'Invalid JSON-RPC request')
        method=msg.get('method')
        rid=msg.get('id')
        # Notifications never require or permit a response.
        if 'id' not in msg:
            return None if isinstance(method,str) else error(None,-32600,'Invalid notification')
        if type(rid) not in (int,str) or not isinstance(method,str): return error(None,-32600,'Invalid id or method')
        params=msg.get('params',{})
        if not isinstance(params,dict): return error(rid,-32602,'Params must be object')
        if method=='initialize':
            requested=params.get('protocolVersion')
            if requested!=LEGACY:
                return error(rid,-32602,'Unsupported legacy revision; supported: '+LEGACY)
            self._legacy_initialized=True
            return ok(rid,{'protocolVersion':LEGACY,'capabilities':{'tools':{},'resources':{}},
                           'serverInfo':SERVER_INFO,'instructions':'Read-only Rootstock chain and skill discovery; no financial transactions.'})
        meta=params.get('_meta',{})
        modern=isinstance(meta,dict) and meta.get('io.modelcontextprotocol/protocolVersion')==MODERN
        if meta and not modern:
            requested=meta.get('io.modelcontextprotocol/protocolVersion')
            if requested is not None and requested not in SUPPORTED:
                return error(rid,-32022,'Unsupported protocol version',{'supported':SUPPORTED,'requested':requested})
        if modern:
            if not isinstance(meta.get('io.modelcontextprotocol/clientCapabilities'),dict):
                return error(rid,-32602,'Modern MCP requires clientCapabilities metadata')
        elif method=='server/discover':
            return error(rid,-32602,'Modern discovery requires versioned request metadata')
        elif not self._legacy_initialized:
            return error(rid,-32600,'Legacy MCP initialize handshake required')
        result={'resultType':'complete'} if modern else {}
        if method=='server/discover':
            result.update({'supportedVersions':SUPPORTED,'capabilities':{'tools':{},'resources':{}},
                           'instructions':'Read-only local MCP; financial actions unavailable.'})
        elif method=='tools/list':
            if params.get('cursor') is not None: return error(rid,-32602,'No pagination cursor is supported')
            result['tools']=tool_definitions()
        elif method=='tools/call':
            name=params.get('name')
            args=params.get('arguments',{})
            if not isinstance(name,str) or name not in CAPABILITIES:
                return error(rid,-32602,'Unknown tool')
            if not isinstance(args,dict):
                return error(rid,-32602,'Tool arguments must be an object')
            try:
                data=self.tools.run(name,args)
                result.update({'content':[{'type':'text','text':json.dumps(data,sort_keys=True,default=str)}],
                               'structuredContent':{'data':data},'isError':False})
            except (RegistryError,ChainError,CapabilityError,PolicyError,OSError,ValueError) as exc:
                result.update({'content':[{'type':'text','text':str(exc)}],'isError':True})
        elif method=='resources/list':
            result['resources']=[{'uri':'rootstock://capabilities','name':'Implemented read-only capabilities','mimeType':'application/json'}]+[
                {'uri':'rootstock://skills/'+s['name'],'name':s['name'],'mimeType':'text/markdown'}
                for s in self.tools.run('skills.list')]
        elif method=='resources/read':
            uri=params.get('uri')
            if uri=='rootstock://capabilities':
                text=json.dumps(self.tools.run('capabilities.list'),sort_keys=True)
                mime='application/json'
            elif isinstance(uri,str) and uri.startswith('rootstock://skills/'):
                try: text=self.tools.run('skills.read',{'name':uri[len('rootstock://skills/'):]})['content']
                except (CapabilityError, OSError) as e: return error(rid,-32602,str(e))
                mime='text/markdown'
            else: return error(rid,-32602,'Unknown resource')
            result['contents']=[{'uri':uri,'mimeType':mime,'text':text}]
        elif method=='ping' and not modern:
            result={}
        else: return error(rid,-32601,'Method not found')
        if modern: result['_meta']={'io.modelcontextprotocol/serverInfo':SERVER_INFO}
        return ok(rid,result)

    def serve(self,input_stream=None, output_stream=None):
        instream=input_stream or sys.stdin
        outstream=output_stream or sys.stdout
        for line in instream:
            if not line.strip(): continue
            if len(line)>1_000_000:
                reply=error(None,-32600,'Request too large')
            else:
                try:
                    obj=json.loads(line)
                    reply=self._respond(obj)
                except (ValueError,UnicodeError):
                    reply=error(None,-32700,'Parse error')
                except Exception: # server faults must not disclose private paths or crash stdio.
                    reply=error(None,-32603,'Internal error')
            if reply is not None:
                outstream.write(json.dumps(reply,ensure_ascii=True,separators=(',',':'))+'\n')
                outstream.flush()


def main(): Server().serve()
if __name__=='__main__': main()
