"""Fail-closed offline packaging/integrity checks for released source + wheel."""
import json
from pathlib import Path
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from rootstock_tools import Toolchain
from rootstock_tools.http_api import OPENAPI

def verify():
    source=list((ROOT/'skills').glob('*/SKILL.md'))
    if len(source)!=20:raise SystemExit('Expected exactly twenty reviewed skills')
    for p in source:
        q=ROOT/'src/rootstock_tools/bundled_skills'/p.parent.name/'SKILL.md'
        if not q.is_file() or q.read_bytes()!=p.read_bytes():raise SystemExit('Skill parity violation: '+p.parent.name)
        for ref in (p.parent/'references').glob('*.md'):
            installed=q.parent/'references'/ref.name
            if not installed.is_file() or installed.read_bytes()!=ref.read_bytes():raise SystemExit('Missing/mismatched skill reference '+str(ref))
    capabilities=Toolchain().run('capabilities.list')
    if len(capabilities)!=len(Toolchain().run('capabilities.list')):raise SystemExit('Unexpected capability count')
    if json.loads((ROOT/'schemas/capability-manifest.json').read_text())['capabilities']!=capabilities:
        raise SystemExit('Capability schema drift')
    if json.loads((ROOT/'schemas/openapi-readonly.json').read_text())!=OPENAPI:
        raise SystemExit('HTTP OpenAPI artifact drift')
    wheels=list((ROOT/'dist').glob('*.whl'))
    if len(wheels)!=1:raise SystemExit('Expected exactly one built beta wheel')
    with zipfile.ZipFile(wheels[0]) as z:
        if z.testzip() is not None:raise SystemExit('Wheel CRC failed')
        bundled={x for x in z.namelist() if x.endswith('/SKILL.md')}
        if len(bundled)!=20:raise SystemExit('Wheel does not contain all twenty skills')
        # Verify wheel skill content equals approved source bytes, not merely file names.
        for p in source:
            f=f'rootstock_tools/bundled_skills/{p.parent.name}/SKILL.md'
            if z.read(f)!=p.read_bytes():raise SystemExit('Wheel skill differs from source: '+f)
        # Security-critical: a wheel built before a fix can ship stale Python behavior.
        # Check ALL Python modules, not just the bundled skill bytes.
        modules=list((ROOT/'src/rootstock_tools').glob('*.py'))
        if not modules:raise SystemExit('No Python source modules found')
        for module in modules:
            wheel_path='rootstock_tools/'+module.name
            if wheel_path not in z.namelist() or z.read(wheel_path)!=module.read_bytes():
                raise SystemExit('Wheel executable module differs from source: '+module.name)
        if not any(x.endswith('entry_points.txt') for x in z.namelist()):raise SystemExit('Console scripts absent')
    print(json.dumps({'ok':True,'skills':len(source),'capabilities':len(capabilities),'wheel':wheels[0].name,'wheel_bytes':wheels[0].stat().st_size},indent=2))
if __name__=='__main__':verify()
