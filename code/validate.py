"""Independent local integrity checks; no cloud calls or data mutations."""
from pathlib import Path
import json,gzip,csv,math,time
import numpy as np,pandas as pd
from webcodec import decode
from preflight import sha,write_json
EXPECTED={'era5':148143,'gpm':105768,'hku':133227,'fire':104073,'vegetation':106785,'pm25':109836,'blackmarble':1778733}
def main(root,out):
    repo=out/'Deliverables/BoliviaSatellites';result={};manifest=json.loads((out/'Evidence/baseline_manifest.json').read_text(encoding='utf-8'))
    changes=[x['path'] for x in manifest['sources']+manifest['bases'] if sha(root/x['path'])!=x['sha256']];assert not changes
    write_json(out/'Evidence/hash_diff.json',{'changed':changes,'checked':len(manifest['sources'])+len(manifest['bases'])})
    for pid,expected in EXPECTED.items():
        t=time.perf_counter();parts=sorted((out/f'Deliverables/ScientificData/master/{pid}/base').glob('*.parquet'));d=pd.concat([pd.read_parquet(p) for p in parts],ignore_index=True);assert len(d)==expected;assert not d.duplicated(['geo_id','period_id']).any();assert set(d.geo_id)==set(range(339))
        csv_rows=sum(sum(1 for _ in csv.DictReader(gzip.open(p.with_suffix('.csv.gz'),'rt',encoding='utf-8')) ) for p in parts);assert csv_rows==expected
        # Validate every full municipal web series and snapshot against the exact intermediate.
        prep=pd.read_parquet(out/f'Evidence/webprep/{pid}.parquet').sort_values(['period_id','geo_id']);card=json.loads((repo/f'public/catalog/{pid}.json').read_text(encoding='utf-8'));T=len(card['periods']);cols=card['columns'];V=len(cols);raw=np.stack([prep[c].to_numpy(dtype=float).reshape(T,339) for c in cols],axis=2);wd=repo/'public/data'/pid;checked=0
        for i,date in enumerate(card['periods']):
            x=decode((wd/'maps'/(date[:7]+'.bin.gz' if card.get('map_layout')=='month_blocks' else date+'.bin.gz')).read_bytes()).reshape(-1,339,V+3)[i-next(k for k,x in enumerate(card['periods']) if x.startswith(date[:7]))] if card.get('map_layout')=='month_blocks' else decode((wd/'maps'/f'{date}.bin.gz').read_bytes()).reshape(339,V+3);assert np.array_equal(x[:,:V],raw[i],equal_nan=True),(pid,date,'map');checked+=1
        for geo in range(339):
            if pid=='blackmarble' and card.get('series_layout')!='municipality_all_variables':
                for j,col in enumerate(cols):
                    x=decode((wd/'series'/col/f'{geo}.bin.gz').read_bytes()).reshape(T,4);assert np.array_equal(x[:,0],raw[:,geo,j],equal_nan=True);checked+=1
            else:
                x=decode((wd/'series'/f'{geo}.bin.gz').read_bytes()).reshape(T,V+3);assert np.array_equal(x[:,:V],raw[:,geo],equal_nan=True);checked+=1
        group_checks=0;lod_checks=0
        geography=json.loads((repo/'public/catalog/geography.json').read_text(encoding='utf-8'))
        for j,col in enumerate(cols):
            arr=raw[:,:,j].copy()
            if pid=='fire':arr[prep['base__qa_flags'].to_numpy(dtype=int).reshape(T,339)&8!=0]=np.nan
            for group,ids in [('national',list(range(339)))]+[(dep,[g['asdf_id'] for g in geography if g['depto']==dep]) for dep in sorted({g['depto'] for g in geography})]:
                actual=decode((wd/'groups'/col/(group+'.bin.gz')).read_bytes()).reshape(T,7)
                # pandas implementation independent of generator's numpy quantiles
                frame=pd.DataFrame(arr[:,ids]);q=frame.quantile([.1,.25,.5,.75,.9],axis=1).T.to_numpy();expected_stats=np.column_stack([frame.mean(axis=1),q,frame.count(axis=1)]);assert np.allclose(actual,expected_stats,equal_nan=True,rtol=1e-8,atol=1e-10);group_checks+=1
            for f in (wd/'lod'/col).rglob('*.bin.gz'):
                packed=decode(f.read_bytes());at=1;lines=[]
                for _ in range(int(packed[0])):
                    geo,n=int(packed[at]),int(packed[at+1]);at+=2;pair=packed[at:at+2*n].reshape(n,2);at+=2*n;lines.append({'id':geo,'i':pair[:,0].astype(int).tolist(),'v':pair[:,1].tolist()})
                for line in lines:
                    ix=np.array(line['i'],dtype=int);a=np.array([np.nan if x is None else x for x in line['v']]);source=arr[:,line['id']];assert np.array_equal(a,source[ix],equal_nan=True)
                    # Every source transition must survive LOD; no hidden bridge over missing periods.
                    for tr in np.flatnonzero(np.isfinite(source[1:])!=np.isfinite(source[:-1]))+1:assert tr in ix and tr-1 in ix
                    lod_checks+=1
        result[pid]={'rows':len(d),'unique':True,'municipalities':339,'csv_rows':csv_rows,'exact_series_and_map_files':checked,'independent_group_checks':group_checks,'LOD_series_checks':lod_checks,'seconds':time.perf_counter()-t,'data_integrity':'PASS','scientific_status':card['status']};print(pid,result[pid],flush=True)
    write_json(out/'Evidence/audit/integrity_validation.json',result)
    # Actual source ratio identity, not a claim about the cause.
    a=pd.concat([pd.read_parquet(p,columns=['mun_code','municipality_area_m2','temperature_valid_area_m2','temperature_valid_area_share']) for p in (out/'Deliverables/ScientificData/master/era5/base').glob('*.parquet')]).drop_duplicates('mun_code').sort_values('mun_code')
    b=pd.concat([pd.read_parquet(p,columns=['mun_code','municipality_area_m2','precip_valid_area_m2','precip_valid_area_share']) for p in (out/'Deliverables/ScientificData/master/gpm/base').glob('*.parquet')]).drop_duplicates('mun_code').sort_values('mun_code')
    assert np.array_equal(a.iloc[:,1:].to_numpy(),b.iloc[:,1:].to_numpy());write_json(out/'Evidence/audit/area_comparison.json',{'same_area_denominator_ratio_all_339':True,'affected_codes':b.loc[b.precip_valid_area_share>1,'mun_code'].tolist(),'cause':'UNRESOLVED; no new GEE extraction authorized','action':'Raw ratios retained; ERA/GPM display with human-authorized warnings'})
    print('SOURCE_AND_WEB_INTEGRITY_PASS')
