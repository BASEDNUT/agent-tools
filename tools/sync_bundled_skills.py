"""Explicit copy of authored Agent Skills into installable package content."""
from pathlib import Path
from shutil import copytree,rmtree
ROOT=Path(__file__).resolve().parents[1]
a=ROOT/'skills'
b=ROOT/'src/rootstock_tools/bundled_skills'
if not a.is_dir():raise SystemExit('Source skill directory missing')
if b.is_symlink():raise SystemExit('Refusing symlink destination')
if b.exists():rmtree(b)
copytree(a,b,symlinks=False)
print('Synchronized',len(list(a.glob('*/SKILL.md'))),'skills into wheel package')
