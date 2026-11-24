"""Build local review packages only. No network, Git push, deployment or credentials."""
from pathlib import Path
import argparse,hashlib,json,zipfile,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];DELIVERY=ROOT.parent;OUT=DELIVERY.parent;PACK=DELIVERY/'Packages';LIMIT=240*2**20
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()
def archive(name,files):
    path=PACK/name
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        for p,arc in files:
            info=zipfile.ZipInfo(arc.replace('\\','/'),(2026,11,24,0,0,0));info.compress_type=zipfile.ZIP_STORED if p.suffix in ['.parquet','.gz','.zip'] else zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
            with p.open('rb') as source,z.open(info,'w',force_zip64=True) as target:shutil.copyfileobj(source,target,2**20)
    assert path.stat().st_size<250*2**20,(path,path.stat().st_size)
    return {'name':name,'url':'downloads/packages/'+name,'bytes':path.stat().st_size,'sha256':sha(path),'publication':'LOCAL_REVIEW_ONLY'}
def parts(prefix,files):
    batches=[];batch=[];size=0
    for p,arc in sorted(files,key=lambda x:x[1]):
        if batch and size+p.stat().st_size>LIMIT:batches.append(batch);batch=[];size=0
        assert p.stat().st_size<250*2**20,p
        batch.append((p,arc));size+=p.stat().st_size
    if batch:batches.append(batch)
    return [archive(f'{prefix}_part{i:02}.zip',b) for i,b in enumerate(batches,1)]
def source_files():
    excluded={'dist','.git','node_modules','__pycache__','.pytest_cache'}
    allowed_dirs={'code','data','LICENSES','provenance','public','scripts','src','tests','distribution'}
    allowed_files={'.gitignore','.gitattributes','netlify.toml','package-lock.json','package.json','README.en.md','README.md','requirements.lock','THIRD_PARTY_NOTICES.txt','index.html'}
    for p in ROOT.rglob('*'):
        rel=p.relative_to(ROOT)
        if (len(rel.parts)==1 and rel.name not in allowed_files) or (len(rel.parts)>1 and rel.parts[0] not in allowed_dirs):continue
        if not p.is_file() or any(x in excluded for x in rel.parts) or rel.parts[:2] in [('public','data'),('data','master'),('data','native')] or rel.parts[:3]==('public','downloads','packages') or rel.as_posix()=='public/downloads/download_manifest.json' or p.suffix=='.pyc':continue
        yield p,rel.as_posix()
def main():
    PACK.mkdir(parents=True,exist_ok=True);files=[]
    for pid in ['era5','gpm','hku','fire','vegetation','pm25','blackmarble']:
        master=DELIVERY/'ScientificData/master'/pid
        assert [p.name for p in master.iterdir() if p.is_dir()]==['base'],'Raw-only scope violated'
        include=[(p,'master/'+pid+'/'+p.relative_to(master).as_posix()) for p in master.rglob('*') if p.is_file()]
        folder={'era5':'ERA5_Land_Temperature_Monthly','gpm':'GPM_IMERG_V07_Precipitation_Monthly','hku':'HKU_NTL_Monthly','fire':'MODIS_MCD64A1_Burned_Area_Monthly','vegetation':'MODIS_MOD13Q1_NDVI_EVI_Monthly','pm25':'PM25_Satellite_Estimates','blackmarble':'NASA_BlackMarble_Daily'}[pid]
        native=DELIVERY/'ScientificData/native';include +=[(p,'sources/'+p.relative_to(native).as_posix()) for p in (native/'Inputs/Satellites'/folder).rglob('*') if p.is_file()]
        if pid=='hku':assert all(not any(word in p.name for word in ['Filtered','Filter_Base','RollingMedian','Epanechnikov']) for p,arc in include)
        entries=parts(pid+'_data',include)
        for entry in entries:entry.update(product=pid,frequency='daily' if pid=='blackmarble' else 'monthly',variant='base',data='Unfiltered municipal source statistics and lossless masters; original precision')
        files+=entries
    # Metadata and full source are independent assets, not embedded in every data partition.
    web=parts('BoliviaSatellites_webdata',[(p,'public/data/'+p.relative_to(ROOT/'public/data').as_posix()) for p in (ROOT/'public/data').rglob('*') if p.is_file()]);files+=web
    dist_bytes=sum(p.stat().st_size for p in (ROOT/'dist').rglob('*') if p.is_file())
    manifest={'web_distribution':{'bytes':dist_bytes,'limit_bytes':250*2**20,'status':'PASS' if dist_bytes<=250*2**20 else 'FAIL_BUDGET_LOCAL_CANDIDATE_ONLY'},'snapshot':'c05-local-v2','scope':'Seven unfiltered municipal source datasets; visual transforms never change downloads','status':'LOCAL_REVIEW_PENDING_HUMAN_ACCEPTANCE','publication':'NOT_AUTHORIZED','files':files}
    # The source ZIP needs a usable download manifest but cannot contain its own hash.
    source_manifest=PACK/'source_download_manifest.json'
    source_manifest.write_text(json.dumps({**manifest,'source_archive_note':'Self archive omitted to avoid a circular checksum'},ensure_ascii=False,indent=2),encoding='utf-8')
    source_members=list(source_files())+[(source_manifest,'public/downloads/download_manifest.json')]
    code=archive('BoliviaSatellites_source.zip',source_members);code['kind']='source';files.append(code)
    for p in [PACK/'download_manifest.json',ROOT/'public/downloads/download_manifest.json',ROOT/'dist/downloads/download_manifest.json']:
        p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    subprocess.run([sys.executable,'-B',str(ROOT/'scripts/build_offline.py')],check=True)
    # A portable distribution contains the complete site, source and all scientific packages.
    portable=[(p,'site/'+p.relative_to(ROOT/'dist').as_posix()) for p in (ROOT/'dist').rglob('*') if p.is_file() and p.name!='distribution-config.js']
    config=PACK/'portable-config.js';config.write_text("window.C05_PACKAGE_ROOT='../packages/';\n",encoding='utf-8');portable.append((config,'site/distribution-config.js'))
    portable +=[(p,'Offline/'+p.relative_to(ROOT/'Offline').as_posix()) for p in (ROOT/'Offline').rglob('*') if p.is_file()]
    entry=PACK/'ABRIR_BOLIVIA_SATELLITES.html';entry.write_text('''<!doctype html><html lang=es><meta charset=utf-8><title>Bolivia Satellites</title><p><a href=site/index.html>Abrir Bolivia Satellites</a> / <a href=site/index.html?lang=en>Open Bolivia Satellites in English</a></p><script>location.replace('site/index.html'+location.search+location.hash)</script></html>''',encoding='utf-8');portable.append((entry,entry.name))
    portable +=[(p,'code/'+arc) for p,arc in source_files()]
    portable +=[(PACK/e['name'],'packages/'+e['name']) for e in files]
    launch=PACK/'START_LOCAL.txt';launch.write_text('Extract every portable_partNN.zip into the same directory.\nDouble-click ABRIR_BOLIVIA_SATELLITES.html. No server required. Keep site, Offline and packages together.\nOptional HTTP preview: python -B code/scripts/serve_local.py --root site --packages packages --port 8768\nOpen http://127.0.0.1:8768/\nNo internet needed for exploration or scientific package downloads.\nPython is only required for the optional server or data processing; processing additionally needs requirements.lock.\n',encoding='utf-8');portable.append((launch,'START_LOCAL.txt'))
    portable_parts=parts('BoliviaSatellites_portable',portable)
    (PACK/'portable_manifest.json').write_text(json.dumps({'parts':portable_parts,'instructions':'Extract all parts to one directory. No external data API required.','expanded_bytes':sum(p.stat().st_size for p,a in portable)},indent=2),encoding='utf-8')
    # Manifest excluded from source archive: rebuilding must be byte-identical.
    final_source=archive('BoliviaSatellites_source.zip',list(source_files())+[(source_manifest,'public/downloads/download_manifest.json')])
    assert final_source['sha256']==code['sha256'],'Source changed during packaging; portable must be rebuilt.'
    for e in files:
        if e['name']==final_source['name']:e.update(final_source)
    for p in [PACK/'download_manifest.json',ROOT/'public/downloads/download_manifest.json',ROOT/'dist/downloads/download_manifest.json']:p.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'Evidence/package_validation.json').write_text(json.dumps({'files':files,'portable':portable_parts,'all_assets_under_250_MiB':True,'dist_budget':manifest['web_distribution'],'published':False,'originals_unchanged':True},indent=2),encoding='utf-8');print(json.dumps({'data_source_web_parts':len(files),'portable_parts':len(portable_parts),'total_bytes':sum(p.stat().st_size for p in PACK.iterdir() if p.is_file())}))
if __name__=='__main__':main()
