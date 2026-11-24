"""Read-only source inventory and C05 execution checkpoint. No extraction or publishing."""
from pathlib import Path
import json, hashlib, platform, sys, shutil, datetime, time, zipfile, csv
import importlib.metadata as md

PRODUCTS = {'era5':'ERA5_Land_Temperature_Monthly','gpm':'GPM_IMERG_V07_Precipitation_Monthly','hku':'HKU_NTL_Monthly','fire':'MODIS_MCD64A1_Burned_Area_Monthly','vegetation':'MODIS_MOD13Q1_NDVI_EVI_Monthly','pm25':'PM25_Satellite_Estimates','blackmarble':'NASA_BlackMarble_Daily'}
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''): h.update(b)
    return h.hexdigest()
def write_json(p,o):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
def main():
    t=time.perf_counter();root=Path.cwd().resolve();out=root/'Outputs/Contract_05';ev=out/'Evidence';ev.mkdir(parents=True,exist_ok=True)
    assert (root/'Contracts/Contract_05.txt').is_file()
    assert shutil.disk_usage(root).free>25*2**30
    baseline=ev/'contract_v1.1_authorized.txt'
    if not baseline.exists(): shutil.copy2(root/'Contracts/Contract_05.txt',baseline)
    rows=[];members=[]
    for product,folder in PRODUCTS.items():
        for p in sorted((root/'Inputs/Satellites'/folder).rglob('*')):
            if not p.is_file():continue
            rows.append({'product':product,'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p),'suffix':p.suffix})
            if p.suffix.lower()=='.zip':
                with zipfile.ZipFile(p) as z:
                    for a in z.infolist():members.append({'path':p.relative_to(root).as_posix(),'member':a.filename,'bytes':a.file_size,'compressed':a.compress_size,'crc':a.CRC})
    bases=[root/x for x in ['AGENTS.md','VISION.md','ROADMAP.md','PLANNING_FREEZE_MANIFEST.json','Contracts/Contract_01_approved.txt','Contracts/Contract_02_approved.txt','Contracts/Contract_04_approved.txt','Maps/GeoBolivia_2015_339/bolivia339geoqueryOpt.geojson']]
    agro=root/'Outputs/Contract_04/Deliverables/BoliviaAgriculturalCensus2013'
    bases+=list((agro/'EarthEngine').glob('bolivia339_2015.*'))+[agro/'Agro2013/crosswalk_cna2013_geo4bolivia339.csv']
    manifest={'sources':rows,'bases':[{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in bases if p.is_file()]}
    dest=ev/'baseline_manifest.json'
    if dest.exists():
        old=json.loads(dest.read_text(encoding='utf-8'));assert old==manifest,'Source inventory changed; investigate before resuming'
    else:write_json(dest,manifest)
    for name,data in [('source_inventory',rows),('archive_members',members)]:
        with (ev/(name+'.csv')).open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    env={'python':sys.version,'platform':platform.platform(),'dependencies':{x:md.version(x) for x in ['pandas','pyarrow','numpy','geopandas','shapely','pyproj','psutil','playwright','brotli']},'disk_free_bytes':shutil.disk_usage(root).free,'preflight_seconds':time.perf_counter()-t,'contract_sha256':sha(baseline)}
    write_json(ev/'environment.json',env)
    write_json(ev/'authorization.json',{'state':'EXECUTING','contract_version':'1.1','human_command':'Contract 5','scope':'Local execution and reviewable packages only','accepted_policy':'Show ERA5/GPM with warnings; coverage above one remains uncertified','geography':'Exact Agriculture 339; use asdf_id; preserve six source code discrepancies','prohibited':['publication','paid compute','new satellite extraction','source modification','frozen project modification'],'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    write_json(ev/'checkpoint.json',{'state':'EXECUTING','phase':'P0_COMPLETE','last_success':'Source inventory and immutable baseline','next':'audit/build-data','products':{x:'PENDING' for x in PRODUCTS},'resume':'python -B Outputs/Contract_05/Deliverables/BoliviaSatellites/code/run.py resume --checkpoint Outputs/Contract_05/Evidence/checkpoint.json'})
    for n,title,body in [('90','EXECUTION','P0 complete. All source reads; no extraction or publication.'),('91','VALIDATION','T01 baseline recorded. T02-T15 NOT_RUN; product criteria tracked separately.'),('99','CLOSURE','PENDING HUMAN ACCEPTANCE. Contract EXECUTING. No acceptance, freeze, or publication.')]:
        (out/f'{n}_{title}_REPORT.md').write_text(f'# Contract 05 — {title}\n\n{body}\n\nSee Evidence/checkpoint.json and baseline_manifest.json.\n',encoding='utf-8')
    print(json.dumps({'files':len(rows),'bytes':sum(x['bytes'] for x in rows),'seconds':env['preflight_seconds'],'free':env['disk_free_bytes']}))
if __name__=='__main__':main()
