"""Independently verify every displayed Black Marble field against original masters."""
from pathlib import Path
import sys,json,numpy as np,pandas as pd,hashlib,time
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'code'))
from webcodec import decode
E=R.parent.parent/'Evidence/revision_02';c=json.loads((R/'public/catalog/blackmarble.json').read_text(encoding='utf-8'));native=[v['native'] for v in c['variables']];V=len(native);T=len(c['periods']);start=time.perf_counter()
d=pd.concat([pd.read_parquet(p,columns=['geo_id','period_id','qa_flags']+native) for p in sorted((R.parent/'ScientificData/master/blackmarble/base').glob('*.parquet'))],ignore_index=True).sort_values(['period_id','geo_id']).reset_index(drop=True)
assert not d.duplicated(['period_id','geo_id']).any();assert len(d)==T*339
raw=d[native].to_numpy(float).reshape(T,339,V);wd=R/'public/data/blackmarble';maps=series=groups=lod=0;roundtrip=[]
for month in sorted({p[:7] for p in c['periods']}):
    ix=[i for i,p in enumerate(c['periods']) if p.startswith(month)];a=decode((wd/'maps'/f'{month}.bin.gz').read_bytes()).reshape(len(ix),339,V+3)
    assert np.array_equal(a[:,:,:V],raw[ix],equal_nan=True),month;maps+=1
for g in range(339):
    a=decode((wd/'series'/f'{g}.bin.gz').read_bytes()).reshape(T,V+3);assert np.array_equal(a[:,:V],raw[:,g,:],equal_nan=True),g;series+=1
geography=json.loads((R/'public/catalog/geography.json').read_text(encoding='utf-8'))
for j,v in enumerate(c['variables']):
    for group,ids in [('national',list(range(339)))]+[(dep,[g['asdf_id'] for g in geography if g['depto']==dep]) for dep in sorted({g['depto'] for g in geography})]:
        actual=decode((wd/'groups'/v['id']/f'{group}.bin.gz').read_bytes()).reshape(T,7);f=pd.DataFrame(raw[:,ids,j]);q=f.quantile([.1,.25,.5,.75,.9],axis=1).T.to_numpy();expected=np.column_stack([f.mean(axis=1),q,f.count(axis=1)])
        assert np.allclose(actual,expected,equal_nan=True,rtol=1e-8,atol=1e-10),(v['id'],group);groups+=1
    for p in (wd/'lod'/v['id']).rglob('*.gz'):
        a=decode(p.read_bytes());at=1
        for k in range(int(a[0])):
            g,n=map(int,a[at:at+2]);at+=2;pairs=a[at:at+2*n].reshape(n,2);at+=2*n;ix=pairs[:,0].astype(int);source=raw[:,g,j]
            assert np.array_equal(pairs[:,1],source[ix],equal_nan=True)
            for edge in np.flatnonzero(np.isfinite(source[1:])!=np.isfinite(source[:-1]))+1:assert edge in ix and edge-1 in ix
            lod+=1
    roundtrip.append({'native':v['native'],'unit':v['unit'],'category':v['category'],'finite':int(np.isfinite(raw[:,:,j]).sum()),'exact':'PASS'})
result={'status':'PASS','rows':len(d),'fields':roundtrip,'all_original_cells_checked':T*339*V,'month_transport_blocks':maps,'municipal_series':series,'independent_group_checks':groups,'LOD_series_checks':lod,'seconds':time.perf_counter()-start,'science':'Units/extractor/mean0 and original min>mean discrepancies remain uncertified; no source values modified'}
(E/'blackmarble_source_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='fields'},indent=2))
