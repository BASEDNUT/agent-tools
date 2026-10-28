#!/usr/bin/env python3
"""Offline schema-based fixtures plus cross-field contract assertions."""
import json,pathlib,sys
from jsonschema import Draft202012Validator
p=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve();s=json.loads((p/'schemas/observation.schema.json').read_text());Draft202012Validator.check_schema(s);v=Draft202012Validator(s)
tests=json.loads((p/'tests/fixtures/cases.json').read_text());fail=[]
for t in tests:
 d=json.loads((p/'tests/fixtures'/t['file']).read_text()); errs=list(v.iter_errors(d));
 # JSON schema cannot compare properties dynamically; test these semantic invariants separately.
 if d.get('source',{}).get('chainId')!=d.get('chainId'):errs.append('cross-chain provenance mismatch')
 c=d.get('coverage');
 if c and c['available']>c['total']:errs.append('coverage numerator exceeds denominator')
 valid=not errs
 if valid!=t['valid']:fail.append((t['file'],valid,errs))
print(f'Observation fixture tests: {len(tests)} cases; '+('PASS' if not fail else 'FAIL'))
for x in fail:print('FAIL:',x)
raise SystemExit(1 if fail else 0)
