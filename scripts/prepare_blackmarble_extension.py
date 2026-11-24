"""Prepare a candidate from existing masters, preserving originals and prior output."""
from pathlib import Path
import sys,json,shutil,numpy as np,pandas as pd
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'code'))
from blackmarble_variables import FIELDS
from run import build_webdata
O=R.parent.parent;C=O/'Evidence/revision_02/blackmarble_candidate'
assert not C.exists(),'Use a fresh candidate path; do not overwrite prior evidence.'
repo=C/'Deliverables/BoliviaSatellites';shutil.copytree(R/'public/catalog',repo/'public/catalog');(repo/'data/catalog').mkdir(parents=True)
shutil.copy2(R/'data/catalog/products.json',repo/'data/catalog/products.json')
parts=sorted((R.parent/'ScientificData/master/blackmarble/base').glob('*.parquet'))
d=pd.concat([pd.read_parquet(p,columns=['geo_id','period_id','qa_flags']+FIELDS) for p in parts],ignore_index=True).sort_values(['period_id','geo_id']).reset_index(drop=True)
old=pd.read_parquet(O/'Evidence/webprep/blackmarble.parquet').sort_values(['period_id','geo_id']).reset_index(drop=True)
assert np.array_equal(d[['geo_id','period_id']].to_numpy(),old[['geo_id','period_id']].to_numpy())
prep=d.rename(columns={c:'base__'+c for c in d if c not in ['geo_id','period_id']})
prep['base__coverage']=old['base__coverage'];prep['base__pixel_count']=old['base__pixel_count']
for c in old:assert np.array_equal(prep[c].to_numpy(),old[c].to_numpy(),equal_nan=True) if old[c].dtype.kind in 'fi' else np.array_equal(prep[c].to_numpy(),old[c].to_numpy())
(C/'Evidence/webprep').mkdir(parents=True);prep.to_parquet(C/'Evidence/webprep/blackmarble.parquet',index=False,compression='zstd')
build_webdata(C,['blackmarble'])
files=[p for p in (repo/'public/data/blackmarble').rglob('*') if p.is_file()]
other=[p for p in (R/'public').rglob('*') if p.is_file() and 'blackmarble' not in p.relative_to(R/'public').parts]
result={'fields':FIELDS,'new_bm_files':len(files),'new_bm_bytes':sum(p.stat().st_size for p in files),'estimated_dist_bytes':sum(p.stat().st_size for p in files+other)+100000,'max_series_bytes':max(p.stat().st_size for p in (repo/'public/data/blackmarble/series').glob('*.gz'))}
(O/'Evidence/revision_02/blackmarble_extension_size.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
