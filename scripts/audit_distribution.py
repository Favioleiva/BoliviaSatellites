"""Publication candidate inventory and conservative secret-pattern scan; local only."""
from pathlib import Path
import json,re,hashlib,gzip,sys
from build_release import source_files,ROOT,OUT
entries=[];findings=[]
patterns=[r'\bgh[pousr]_[A-Za-z0-9]{30,}\b',r'\bhf_[A-Za-z0-9]{25,}\b',r'\bAKIA[A-Z0-9]{16}\b',r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']
for p,rel in source_files():
    entries.append({'path':rel,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    if p.suffix.lower() in {'.py','.js','.json','.ipynb','.txt','.md','.mjs','.html','.toml','.csv'}:
        text=p.read_text(encoding='utf-8',errors='replace')
        if any(re.search(pattern,text) for pattern in patterns):findings.append(rel)
assert not findings,findings
assert all(x['bytes']<100*2**20 for x in entries)
assert sum(x['bytes'] for x in entries)<500*2**20
dist=[p for p in (ROOT/'dist').rglob('*') if p.is_file()]
web=list((ROOT/'public/data').rglob('*.gz'))
result={'allowlist':entries,'source_bytes':sum(x['bytes'] for x in entries),'source_max_file_bytes':max(x['bytes'] for x in entries),'dist_bytes':sum(p.stat().st_size for p in dist),'dist_files':len(dist),'largest_web_chunk_bytes':max(p.stat().st_size for p in web),'compressed_JS_CSS_bytes':sum(len(gzip.compress((ROOT/'src'/n).read_bytes())) for n in ['app.js','worker.js','styles.css']),'initial_catalog_bytes':(ROOT/'public/catalog/index.json').stat().st_size,'secret_pattern_findings':findings,'scan_scope':'Pattern scan is not a license determination; no Evidence, original notebooks with outputs, credentials or private census records are allowlisted.'}
(OUT/'Evidence/distribution_audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='allowlist'},indent=2))
