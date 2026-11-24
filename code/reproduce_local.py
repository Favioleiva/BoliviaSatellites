"""Create an isolated aggregate-source reproduction and compare every native master cell."""
from pathlib import Path
import shutil,subprocess,sys,json,time
import pandas as pd
from preflight import sha,write_json
root=Path.cwd().resolve();out=root/'Outputs/Contract_05';repo=out/'Deliverables/BoliviaSatellites';work=out/'Evidence/reproduction';sources=work/'Sources';target=work/'Rebuilt';t=time.perf_counter()
assert not target.exists(),'Use a new reproduction directory; do not overwrite an earlier run.'
shutil.copytree(out/'Deliverables/ScientificData/native',sources,copy_function=shutil.copyfile,dirs_exist_ok=True)
for sub in ['Maps/GeoBolivia_2015_339/bolivia339geoqueryOpt.geojson','Outputs/Contract_04/Deliverables/BoliviaAgriculturalCensus2013/Agro2013/crosswalk_cna2013_geo4bolivia339.csv']:
    p=sources/sub;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/sub,p)
sub=Path('Outputs/Contract_04/Deliverables/BoliviaAgriculturalCensus2013/EarthEngine')
for p in (root/sub).glob('bolivia339_2015.*'):
    dst=sources/sub/p.name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst)
# Mirror is only an audit input; recreated from byte-identical canonical sources for the portable rerun.
bm=sources/'Inputs/Satellites/NASA_BlackMarble_Daily/Inputs'
shutil.copytree(bm/'daily_raw',bm/'_hf_download/bolivia339/daily_raw',copy_function=shutil.copyfile,dirs_exist_ok=True)
commands=[[sys.executable,'-B',str(repo/'code/run.py'),cmd,'--input-root',str(sources),'--output-root',str(target)] for cmd in ['build-data','build-webdata']]
with (work/'rebuild.log').open('w',encoding='utf-8') as log:
    for cmd in commands:
        result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT);assert result.returncode==0,cmd
original=out/'Deliverables/ScientificData/master';rebuilt=target/'Deliverables/ScientificData/master';checked=[]
for p in sorted(original.rglob('*.parquet')):
    q=rebuilt/p.relative_to(original);pd.testing.assert_frame_equal(pd.read_parquet(p),pd.read_parquet(q),check_exact=True);checked.append({'path':p.relative_to(original).as_posix(),'same_bytes':sha(p)==sha(q),'same_cells':True})
web=[];a=repo/'public/data';b=target/'Deliverables/BoliviaSatellites/public/data'
for p in sorted(a.rglob('*.gz')):
    q=b/p.relative_to(a);assert q.is_file() and sha(p)==sha(q),(p,q);web.append(p.relative_to(a).as_posix())
write_json(work/'result.json',{'status':'PASS','level':'A aggregate reconstruction','master_partitions':checked,'web_files_exact':len(web),'seconds':time.perf_counter()-t,'commands':commands,'level_B':'BLOCKED for missing upstream extractor/metadata; no satellite extraction run'})
print('LEVEL_A_REPRODUCTION_PASS',len(checked),len(web),flush=True)
