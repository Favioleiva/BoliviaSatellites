"""Verify every published CSV.gz cell against its exact Parquet counterpart."""
from pathlib import Path
import pandas as pd,numpy as np,json,time
repo=Path(__file__).resolve().parents[2];out=repo.parent.parent;t=time.perf_counter();results=[]
for f in sorted((repo.parent/'ScientificData/master').rglob('*.parquet')):
    a=pd.read_parquet(f);strings={c:'str' for c in a if pd.api.types.is_string_dtype(a[c].dtype) or a[c].dtype=='object'}
    b=pd.read_csv(f.with_suffix('.csv.gz'),dtype=strings,float_precision='round_trip',keep_default_na=False,na_values=[r'\N'])
    assert list(a.columns)==list(b.columns)
    assert len(a)==len(b)
    for c in a:
        if pd.api.types.is_datetime64_any_dtype(a[c].dtype):b[c]=pd.to_datetime(b[c])
        av,bv=a[c],b[c]
        equal=(av==bv)|(av.isna()&bv.isna())
        assert equal.fillna(False).all(),(f,c,int((~equal.fillna(False)).sum()))
    results.append({'path':f.relative_to(repo.parent/'ScientificData').as_posix(),'rows':len(a),'columns':len(a.columns),'all_cells_equal':True})
report={'status':'PASS','partitions':results,'seconds':time.perf_counter()-t};(out/'Evidence/csv_roundtrip.json').write_text(json.dumps(report,indent=2));print('CSV_ROUNDTRIP_PASS',len(results),round(report['seconds'],2))
