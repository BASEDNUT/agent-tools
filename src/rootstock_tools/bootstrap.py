"""Explicit, opt-in pinned-source download; never invoked automatically."""
import os
from pathlib import Path
from urllib.request import Request, build_opener
from .registry import CANONICAL_BLOBS, git_blob_sha, RegistryError
from .rpc import NoRedirect
SOURCE_COMMIT='6206c91643e2e87c43164be90f963c91a11329ab'
SOURCE_PREFIX='https://raw.githubusercontent.com/BASEDNUT/rootstock-monorepo/'+SOURCE_COMMIT+'/deployments/'

def fetch_registries(dest:Path):
    opener=build_opener(NoRedirect())
    validated={}
    for name,blob in CANONICAL_BLOBS.items():
        req=Request(SOURCE_PREFIX+name,headers={'Accept':'application/json','User-Agent':'rootstock-agent-tools/0.9.1'})
        try:
            with opener.open(req,timeout=15) as r: raw=r.read(100_001)
        except OSError as exc: raise RegistryError('Unable to download frozen canonical source: '+str(exc)) from exc
        if len(raw)>100_000 or git_blob_sha(raw)!=blob:
            raise RegistryError('Downloaded source does not match frozen source SHA for '+name+'; nothing written')
        validated[name]=raw
    dest=Path(dest).expanduser()
    if any(part.is_symlink() for part in (dest,*dest.parents)):
        raise RegistryError('Symlink registry output path refused')
    dest.mkdir(parents=True,exist_ok=True)
    # Preflight *both* existing files before any writes: no partial override on conflicts.
    for name,raw in validated.items():
        path=dest/name
        if path.is_symlink(): raise RegistryError('Refusing symlink registry output')
        if path.exists() and path.read_bytes()!=raw:
            raise RegistryError('Refusing to overwrite existing different registry '+str(path))
    for name,raw in validated.items():
        path=dest/name
        if path.exists(): continue
        tmp=dest/(name+'.tmp-'+str(os.getpid()))
        try:
            with tmp.open('xb') as f: f.write(raw)
            os.replace(tmp,path)
        finally:
            tmp.unlink(missing_ok=True)
    return {'frozen_source_commit':SOURCE_COMMIT,'directory':str(dest),'files':sorted(validated),'verified_against_pinned_blobs':True}
