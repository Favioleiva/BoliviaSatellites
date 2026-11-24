"""Create a clean allowlisted source directory; never push, upload, or deploy."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_release import source_files

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--destination',type=Path,required=True);a=parser.parse_args()
    destination=a.destination.resolve()
    if destination.exists():raise ValueError('Destination must be absent; existing repositories are never overwritten')
    files=list(source_files())+[(ROOT/'public/downloads/download_manifest.json','public/downloads/download_manifest.json')]
    denied={'Inputs','Evidence','ScientificData','Packages','Offline','dist','.git','node_modules','__pycache__'}
    token=re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{25,}|sk-[A-Za-z0-9_-]{25,}|AKIA[0-9A-Z]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)')
    records=[]
    for source,relative in files:
        parts=Path(relative).parts
        if source.is_symlink() or any(x in denied for x in parts) or relative.startswith(('public/data/','data/native/','data/master/')):
            raise ValueError('Excluded path in publication list')
        if source.stat().st_size>25*2**20:raise ValueError('File exceeds source budget: '+relative)
        raw=source.read_bytes()
        if token.search(raw.decode('utf-8',errors='replace')):raise ValueError('Credential-shaped content found; inspect locally: '+relative)
        if source.suffix=='.ipynb':
            nb=json.loads(raw)
            if 'widgets' in nb.get('metadata',{}) or any(c.get('outputs') or c.get('execution_count') is not None for c in nb['cells']):
                raise ValueError('Notebook session/output metadata present')
        records.append({'path':relative,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    if sum(x['bytes'] for x in records)>500*2**20:raise ValueError('Source repository exceeds 500 MiB')
    for source,relative in files:
        target=destination/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    manifest={'status':'PREPARED_PENDING_HUMAN_PUBLICATION_AUTHORIZATION','target':'Favioleiva/BoliviaSatellites','published':False,
        'scope':'All candidate source files except this manifest itself; Git metadata excluded',
        'license':'Project code license pending human selection; third-party terms retained',
        'files':records,'files_count':len(records),'bytes':sum(x['bytes'] for x in records)}
    (destination/'publication_allowlist.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'destination':str(destination),'files':len(records)+1,'bytes':manifest['bytes'],'status':manifest['status']}))

if __name__=='__main__':main()
