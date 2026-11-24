"""Restore versioned web arrays from verified local Release assets. No extraction APIs."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import shutil
import tempfile
import urllib.parse
import urllib.request
import zipfile

ROOT=Path(__file__).resolve().parents[1]
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(2**20),b''):h.update(block)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--packages',type=Path,help='Directory containing all webdata ZIP parts')
    p.add_argument('--release-base-url',help='Explicit HTTPS URL for an already published immutable tag; never latest')
    a=p.parse_args()
    if bool(a.packages)==bool(a.release_base_url):p.error('Choose either --packages or --release-base-url')
    manifest=json.loads((ROOT/'distribution/webdata-manifest.json').read_text(encoding='utf-8'))
    expected={x['path']:x for x in manifest['files']}
    base=None
    if a.release_base_url:
        u=urllib.parse.urlparse(a.release_base_url)
        prefix='/Favioleiva/BoliviaSatellites/releases/download/'
        if u.scheme!='https' or u.hostname!='github.com' or not u.path.startswith(prefix) or u.query or u.fragment or u.username:
            p.error('Expected an explicit https://github.com/Favioleiva/BoliviaSatellites/releases/download/TAG URL')
        tag=u.path[len(prefix):].strip('/')
        if not tag or '/' in tag or tag.lower()=='latest':p.error('An immutable tag is required')
        base=a.release_base_url.rstrip('/')+'/'
    # Validate every archive and every path before writing into public/data.
    with tempfile.TemporaryDirectory(prefix='bolivia-webdata-') as temporary:
        archives=[];seen=set()
        for asset in manifest['assets']:
            archive=(a.packages/asset['name']) if a.packages else Path(temporary)/asset['name']
            if base:
                url=base+urllib.parse.quote(asset['name'])
                with urllib.request.urlopen(url,timeout=120) as response,archive.open('wb') as out:
                    shutil.copyfileobj(response,out,2**20)
            if not archive.is_file():raise FileNotFoundError(f'Missing Release part: {archive.name}')
            if archive.stat().st_size!=asset['bytes'] or sha(archive)!=asset['sha256']:
                raise ValueError(f'Checksum/size mismatch: {archive.name}')
            with zipfile.ZipFile(archive) as z:
                for info in z.infolist():
                    name=info.filename;parts=PurePosixPath(name).parts
                    if info.is_dir():continue
                    if name not in expected or '\\' in name or '..' in parts or PurePosixPath(name).is_absolute() or (info.external_attr>>16)&0o170000==0o120000:
                        raise ValueError('Unexpected archive member')
                    if name in seen or info.file_size!=expected[name]['bytes']:raise ValueError('Duplicate member or wrong size')
                    destination=(ROOT/name).resolve()
                    if not destination.is_relative_to((ROOT/'public/data').resolve()):raise ValueError('Unsafe destination')
                    if destination.exists() and sha(destination)!=expected[name]['sha256']:
                        raise ValueError(f'Existing data differ: {name}; use a clean checkout')
                    seen.add(name)
            archives.append(archive)
        if seen!=set(expected):raise ValueError('Incomplete webdata snapshot')
        for archive in archives:
            with zipfile.ZipFile(archive) as z:
                for info in z.infolist():
                    if info.is_dir():continue
                    destination=ROOT/info.filename
                    if destination.exists():continue
                    destination.parent.mkdir(parents=True,exist_ok=True)
                    temporary_file=destination.with_name(destination.name+'.restoring')
                    try:
                        with z.open(info) as source,temporary_file.open('wb') as target:shutil.copyfileobj(source,target,2**20)
                        if sha(temporary_file)!=expected[info.filename]['sha256']:raise ValueError('Member checksum mismatch')
                        temporary_file.replace(destination)
                    finally:
                        if temporary_file.exists():temporary_file.unlink()
    print(json.dumps({'status':'PASS','files':len(expected),'bytes':sum(x['bytes'] for x in expected.values()),'snapshot':manifest['snapshot']}))

if __name__=='__main__':main()
