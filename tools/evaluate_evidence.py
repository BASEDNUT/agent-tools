#!/usr/bin/env python3
"""JIT case 0001 evaluator: compare source claims, infer allowed conclusions, detect drift."""
import json
from pathlib import Path
import re
from collections import defaultdict

ROOT=Path(__file__).resolve().parents[1]
sources=json.loads((ROOT/'reference/source-locks.json').read_text())
graph=json.loads((ROOT/'reference/evidence-graph.json').read_text())
ids={s['id'] for s in sources['source_files']}
assert len(ids)==len(sources['source_files']), 'duplicate sources'
assert set(graph['source_ids'])==ids, 'mismatched source catalog'
for c in graph['claims']:
    assert c['source_ids'] and set(c['source_ids'])<=ids, c
    assert c['status'] in {'source-inspected','unverified-runtime','not-tested'},c
for s in sources['source_files']:
    assert re.fullmatch('[a-f0-9]{40}',s['blob_sha']),s
    assert s['url'].startswith('https://github.com/'),s
addr=defaultdict(dict)
for row in graph['address_observations']:
    assert row['source'] in ids
    assert re.fullmatch('0x[a-fA-F0-9]{40}',row['address'])
    addr[(row['chain_id'],row['contract'])][row['origin']]=row['address'].lower()
base=addr[(8453,'Router')]
sep=addr[(84532,'Router')]
assert base['upstream-balancer-unpatched'] != base['rootstock-registry'], 'difference signal lost'
assert base['rootstock-pnpm-patch'] == base['rootstock-registry'], 'patch diverges from registry on Base'
assert sep['rootstock-pnpm-patch'] == sep['rootstock-registry'], 'patch diverges from registry on Sepolia'
assert any(c['id']=='C04' and c['status']=='unverified-runtime' for c in graph['claims']), 'runtime unproven'
assert graph['revisions'], 'counter-evidence and revisions must remain visible'
print(json.dumps({'ok':True,'sources':len(ids),'claims':len(graph['claims']),'observations':len(graph['address_observations']),'patch_registry_matches':2,'upstream_base_router_differs':True,'runtime_proven':False,'live_chain_proven':False},indent=2))
