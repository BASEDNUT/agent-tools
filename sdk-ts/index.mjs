/** Dependency-free Node consumer of the Python CLI. Never invokes a shell. */
import {spawnSync} from 'node:child_process';

export class RootstockClient {
  constructor({command='rootstock', prefix=[], timeoutMs=30000, env=process.env}={}) {
    if(typeof command!=='string'||!command.trim()) throw new TypeError('CLI executable required');
    if(!Array.isArray(prefix)||!prefix.every(x=>typeof x==='string')) throw new TypeError('Invalid CLI prefix');
    this.command=command;this.prefix=prefix;this.timeoutMs=timeoutMs;this.env=env;
  }
  call(name, args={}) {
    if(typeof name!=='string'||!/^[a-z][a-z0-9]*(?:\.[a-z][a-z0-9_]*)+$/.test(name))throw new TypeError('Invalid capability name');
    if(!args||typeof args!=='object'||Array.isArray(args))throw new TypeError('Arguments must be object');
    const result=spawnSync(this.command,[...this.prefix,'call',name,'--args',JSON.stringify(args)],{
      shell:false,encoding:'utf8',timeout:this.timeoutMs,maxBuffer:4*1024*1024,env:this.env,
    });
    if(result.error)throw new Error('Rootstock CLI launch failed: '+result.error.message);
    let parsed;
    try{parsed=JSON.parse(result.status===0?result.stdout:result.stderr)}catch{throw new Error('Rootstock CLI invalid response; check installation and invocation')}
    if(result.status!==0||!parsed?.ok)throw new Error(parsed?.error||'Rootstock CLI denied request');
    return parsed.result;
  }
  capabilities(){return this.call('capabilities.list')}
  skills(){return this.call('skills.list')}
  networks(){return this.call('registry.list_networks')}
}
