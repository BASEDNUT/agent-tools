#!/usr/bin/env python3
"""Offline Agent Skills compliance & local-document hygiene gate."""
import pathlib, re, sys, yaml
root=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
errors=[];checked=0
skills=root/'skills'
for f in sorted(skills.glob('*/SKILL.md')):
    checked+=1;text=f.read_text(encoding='utf-8')
    m=re.match(r'^---\n(.*?)\n---\n',text,re.S)
    if not m: errors.append(f'{f}: missing frontmatter');continue
    try: meta=yaml.safe_load(m.group(1))
    except Exception as exc:errors.append(f'{f}: YAML {exc}');continue
    n=meta.get('name');d=meta.get('description');
    if n!=f.parent.name or not isinstance(n,str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',n) or len(n)>64:errors.append(f'{f}: invalid skill name')
    if not isinstance(d,str) or not (1<=len(d)<=1024) or 'use' not in d.lower():errors.append(f'{f}: description must include trigger')
    if 'author' not in meta.get('metadata',{}):errors.append(f'{f}: metadata.author missing')
    if not text.split('---',2)[2].strip():errors.append(f'{f}: empty body')
    if len(text.splitlines())>500:errors.append(f'{f}: exceeds progressive disclosure recommendation')
    for rel in re.findall(r'\[[^\]]+\]\((references/[^)# ]+|scripts/[^)# ]+)\)',text):
        if not (f.parent/rel).exists():errors.append(f'{f}: missing linked file {rel}')
    if 'wallet' in text.lower() and ('read-only' not in text.lower() and 'sign' not in text.lower()):errors.append(f'{f}: wallet handling lacks explicit boundary')
if checked==0:errors.append('no skills')
print(f'Skill structural checks: {checked} skills; '+('PASS' if not errors else 'FAIL'))
for e in errors:print('ERROR:',e)
raise SystemExit(1 if errors else 0)
