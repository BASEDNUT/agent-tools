"""Loopback-only, unauthenticated, read-only HTTP API.

Never bind a public interface: this is a local developer/agent bridge, not a web service.
"""
from __future__ import annotations
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs,urlsplit,unquote
from .core import Toolchain, CapabilityError
from .registry import RegistryError
from .rpc import ChainError
from .policy import PolicyError

READ_PATHS={
 '/v1/networks':'Rootstock networks',
 '/v1/capabilities':'Read-only capabilities',
 '/v1/skills':'Bundled skills',
 '/v1/skills/{name}':'Read bundled skill',
 '/v1/deployments/{chain_id}/{name}':'Resolve pinned deployment',
 '/v1/rpc/{chain_id}/health':'Provider chain/head check',
 '/v1/pools/{chain_id}':'Bounded pool events',
 '/v1/contracts/{chain_id}':'Source-pinned contract inventory',
 '/v1/history/{chain_id}':'Local history checkpoint status',
 '/v1/analytics/{chain_id}':'Indexed raw-token swap volume and fees',
 '/v1/graph/{chain_id}':'Observed Orchard token-pool hypergraph',
 '/v1/assets/{chain_id}/{address}':'Explicit token metadata',
 '/v1/portfolio/{chain_id}/{wallet}/{token}':'Explicit wallet token balance',
}
OPENAPI={
    'openapi':'3.1.0',
    'info':{'title':'Rootstock Local Read-Only API','version':'0.7.1-beta'},
    'paths':{},
}
for path,summary in READ_PATHS.items():
    params=[]
    for token in ('chain_id','name'):
        if '{'+token+'}' in path:
            params.append({'name':token,'in':'path','required':True,'schema':{'type':'integer' if token=='chain_id' else 'string'}})
    if path.startswith('/v1/pools/'):
        params.extend([{'name':name,'in':'query','required':name!='limit','schema':{'type':'integer','minimum':0}} for name in ('from_block','to_block','limit')])
    if path.startswith('/v1/deployments/'):
        params.append({'name':'task','in':'query','required':False,'schema':{'type':'string'}})
    OPENAPI['paths'][path]={'get':{'summary':summary,'parameters':params,'responses':{
        '200':{'description':'Read-only JSON envelope','content':{'application/json':{'schema':{
            'type':'object','properties':{'ok':{'type':'boolean'},'effect':{'const':'read'},'result':{}},
            'required':['ok','result']}}}},
        '400':{'description':'Validation or unavailable source error'},
    }}}
OPENAPI['paths']['/v1/tools/call']={'post':{'summary':'Invoke a shared read-only toolkit capability with typed JSON arguments',
    'requestBody':{'required':True,'content':{'application/json':{'schema':{'type':'object','required':['name','arguments'],
        'additionalProperties':False,'properties':{'name':{'type':'string'},'arguments':{'type':'object'}}}}}},
    'responses':{'200':{'description':'Read-only capability result'},'400':{'description':'Invalid or denied capability'}}}}
OPENAPI['paths']['/openapi.json']={'get':{'summary':'Machine-readable local API schema','responses':{'200':{'description':'OpenAPI 3.1 document'}}}}

def make_handler(toolchain:Toolchain):
    class Handler(BaseHTTPRequestHandler):
        server_version='RootstockLocalReadOnly/0.7.1'
        def log_message(self,*args): return # never log requested skill contents
        def send_json(self,code,content):
            body=json.dumps(content,ensure_ascii=True,sort_keys=True).encode('utf8')
            self.send_response(code)
            self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Length',str(len(body)))
            self.end_headers();self.wfile.write(body)
        def do_POST(self):
            if self.path != '/v1/tools/call':
                self.send_json(405,{'ok':False,'error':'No write or signing endpoints exist'});return
            try:
                host=self.headers.get('Host','').split(':')[0].strip('[]').lower()
                if host not in ('localhost','127.0.0.1','::1'):
                    self.send_json(403,{'ok':False,'error':'Only loopback Host headers accepted'});return
                if self.headers.get('Content-Type','').split(';')[0].strip().lower()!='application/json':
                    raise CapabilityError('JSON Content-Type required')
                n=int(self.headers.get('Content-Length','-1'))
                if not 1<=n<=65536:raise CapabilityError('Invalid request body length')
                payload=json.loads(self.rfile.read(n))
                if not isinstance(payload,dict) or set(payload)!={'name','arguments'} or not isinstance(payload['arguments'],dict):
                    raise CapabilityError('Expected name and arguments fields only')
                result=toolchain.run(payload['name'],payload['arguments'])
                self.send_json(200,{'ok':True,'effect':'read','result':result})
            except (ValueError,TypeError,CapabilityError,ChainError,RegistryError,PolicyError,OSError) as exc:
                self.send_json(400,{'ok':False,'error':str(exc)})
        def do_PUT(self):self.send_json(405,{'ok':False,'error':'Write endpoints do not exist'})
        do_PATCH=do_DELETE=do_PUT
        def do_GET(self):
            try:
                host=self.headers.get('Host','').split(':')[0].strip('[]').lower()
                if host not in ('localhost','127.0.0.1','::1'):
                    self.send_json(403,{'ok':False,'error':'Only loopback Host headers accepted'});return
                if len(self.path)>2000: raise CapabilityError('URL too long')
                u=urlsplit(self.path)
                parts=[unquote(x) for x in u.path.strip('/').split('/')]
                query=parse_qs(u.query,keep_blank_values=True)
                allowed_keys=({'task'} if len(parts)==4 and parts[:2]==['v1','deployments'] else
                              {'from_block','to_block','limit'} if len(parts)==3 and parts[:2]==['v1','pools'] else set())
                if set(query)-allowed_keys: raise CapabilityError('Unknown query parameters')
                if u.path=='/openapi.json': result=OPENAPI
                elif parts==['v1','networks']: result=toolchain.run('registry.list_networks')
                elif parts==['v1','capabilities']: result=toolchain.run('capabilities.list')
                elif parts==['v1','skills']: result=toolchain.run('skills.list')
                elif len(parts)==3 and parts[:2]==['v1','skills']:
                    result=toolchain.run('skills.read',{'name':parts[2]})
                elif len(parts)==4 and parts[:2]==['v1','deployments']:
                    args={'chain_id':int(parts[2]),'name':parts[3]}
                    if 'task' in query:
                        if len(query['task'])!=1: raise CapabilityError('One task parameter required')
                        args['task']=query['task'][0]
                    result=toolchain.run('registry.resolve_deployment',args)
                elif len(parts)==4 and parts[:2]==['v1','rpc'] and parts[3]=='health':
                    result=toolchain.run('rpc.get_health',{'chain_id':int(parts[2])})
                elif len(parts)==3 and parts[:2]==['v1','contracts']:
                    result=toolchain.run('registry.list_contracts',{'chain_id':int(parts[2])})
                elif len(parts)==3 and parts[:2]==['v1','history']:
                    result=toolchain.run('history.status',{'chain_id':int(parts[2])})
                elif len(parts)==3 and parts[:2]==['v1','analytics']:
                    result=toolchain.run('analytics.volume_fees',{'chain_id':int(parts[2])})
                elif len(parts)==3 and parts[:2]==['v1','graph']:
                    result=toolchain.run('topology.explore',{'chain_id':int(parts[2]),'limit':5})
                elif len(parts)==4 and parts[:2]==['v1','assets']:
                    result=toolchain.run('assets.lookup',{'chain_id':int(parts[2]),'address':parts[3]})
                elif len(parts)==5 and parts[:2]==['v1','portfolio']:
                    result=toolchain.run('accounts.positions',{'chain_id':int(parts[2]),'wallet':parts[3],'token':parts[4]})
                elif len(parts)==3 and parts[:2]==['v1','pools']:
                    def num(k,default=None):
                        if k not in query:
                            if default is not None:return default
                            raise CapabilityError('Missing query: '+k)
                        if len(query[k])!=1:return raise_error('Repeated query parameter '+k)
                        return int(query[k][0])
                    result=toolchain.run('pools.list',{'chain_id':int(parts[2]),'from_block':num('from_block'),
                        'to_block':num('to_block'),'limit':num('limit',250)})
                else: self.send_json(404,{'ok':False,'error':'Unknown read-only endpoint'});return
                self.send_json(200,{'ok':True,'effect':'read','result':result})
            except (ValueError,CapabilityError,ChainError,RegistryError,PolicyError,OSError) as exc:
                self.send_json(400,{'ok':False,'error':str(exc)})
    return Handler

def raise_error(message): raise CapabilityError(message)

def serve(toolchain=None,port=8765):
    if type(port) is not int or not 0<=port<=65535:raise ValueError('Invalid port')
    httpd=ThreadingHTTPServer(('127.0.0.1',port),make_handler(toolchain or Toolchain()))
    try: httpd.serve_forever()
    finally:httpd.server_close()


def main():
    serve()
