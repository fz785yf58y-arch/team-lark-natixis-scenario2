#!/usr/bin/env python3
"""Maintainer-only: freeze tracked inputs/code before validation, excluding outputs."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    files={}
    for folder in ['src','scripts','data','docs']:
        for p in sorted((ROOT/folder).rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ['.pyc','.pyo']:
                files[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
    for rel in ['checks/expected_metrics.json','README.md','requirements.txt','requirements-research.txt','.gitignore']:
        p=ROOT/rel;files[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    (ROOT/'checks/sha256_manifest.json').write_text(json.dumps({'cutoff':'2026-09-17','files':files,'excludes':'acceptance results, caches and this manifest itself'},indent=2)+'\n')
if __name__=='__main__':main()
