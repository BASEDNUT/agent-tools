import test from 'node:test';import assert from 'node:assert/strict';
import {RootstockClient} from './index.mjs';
const client=new RootstockClient({command:'python',prefix:['-m','rootstock_tools'],timeoutMs:10000});
test('Node SDK reads shared Python capability contract',()=>{
  const c=client.capabilities();assert(c.length>=25);assert(c.some(x=>x.name==='policy.evaluate'));
});
test('Node SDK returns policy-denied execution',()=>{
  const r=client.call('policy.evaluate',{chain_id:8453,action:'execute'});
  assert.equal(r.decision,'DENY');assert.equal(r.signing_authority,false);
});
test('Arbitrary tool injection remains rejected by the shared core',()=>{
  assert.throws(()=>client.call('transactions.execute',{}));
  assert.throws(()=>client.call('rpc.get_health',{chain_id:8453,untrusted:'x'}));
});
test('Shell injection stays a literal argument',()=>{
  assert.throws(()=>client.call('skills.read',{name:';touch /tmp/unsafe;'}));
});
test('Bundled skills visible in Node SDK',()=>{
  const s=client.skills();assert(s.length>=13);assert(s.some(x=>x.name==='rootstock-agent-security'));
});
