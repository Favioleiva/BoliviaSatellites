"""Bolivia Satellites: local, lossless aggregate pipeline. Never acquires satellites or publishes."""
from pathlib import Path
import argparse, csv, datetime, gzip, hashlib, io, json, math, re, shutil, sys, time, zipfile, warnings
import numpy as np
import pandas as pd
import geopandas as gpd
from webcodec import encode,decode
from blackmarble_variables import FIELDS,metadata as bm_metadata
from preflight import PRODUCTS, sha, write_json

CFG={
 'era5':dict(name=['Temperatura','Temperature'],unit='°C',prefix='temperature_',default='temperature_mean',frequency='monthly',source='ECMWF/ERA5_LAND/MONTHLY_AGGR',resolution='11132 m reduction; reanalysis',status='qualified',note=['Cobertura espacial sin certificar; 27 municipios superan 1. Temperaturas conservadas.','Spatial coverage uncertified; 27 municipalities exceed 1. Temperatures preserved.']),
 'gpm':dict(name=['Precipitación','Precipitation'],unit='mm/month',prefix='precip_',default='precip_mean',frequency='monthly',source='NASA/GPM_L3/IMERG_V07',resolution='11132 m reduction; 30-minute source',status='qualified',note=['Lluvia numérica recuperada. Cobertura espacial sin certificar; 27 municipios superan 1.','Numeric rainfall recovered. Spatial coverage uncertified; 27 municipalities exceed 1.']),
 'hku':dict(name=['Luces nocturnas · HKU','Night lights · HKU'],unit='source radiance',prefix='',default='mean',frequency='monthly',source='HKU VIIRS-like monthly; DOI 10.25442/hku.31321315.v2',resolution='15 arc seconds (~500 m)',status='qualified',note=['Serie municipal fuente sin filtros locales. La historia temprana es reconstruida por el proveedor.','Municipal source series without local filtering. Early history is reconstructed by the provider.']),
 'fire':dict(name=['Área quemada','Burned area'],unit='km²',prefix='burned_',default='burned_area_km2',frequency='monthly',source='MODIS/061/MCD64A1',resolution='500 m',status='blocked',note=['Exploración de fuente: conteos y QA no reconciliados. Cero sin área válida no significa ausencia de fuego.','Source exploration: counts and QA unresolved. Zero without valid area does not mean no fire.']),
 'vegetation':dict(name=['Vegetación · NDVI/EVI','Vegetation · NDVI/EVI'],unit='dimensionless',prefix='ndvi_',default='ndvi_mean',frequency='monthly',source='MODIS/061/MOD13Q1',resolution='250 m; 16-day composites',status='qualified',note=['Mediana de compuestos iniciados en el mes; cobertura baja explícita. No es una media diaria.','Median of composites starting in the month; low coverage explicit. Not a daily mean.']),
 'pm25':dict(name=['Calidad del aire · PM2.5','Air quality · PM2.5'],unit='µg/m³',prefix='pm25_',default='pm25_mean',frequency='monthly',source='SatPM V6.GL.03',resolution='0.01 degrees',status='qualified',note=['Estimación modelada, no estación municipal. Extremos y revisión cartográfica upstream pendientes.','Modelled estimate, not a municipal monitor. Extremes and upstream map revision pending.']),
 'blackmarble':dict(name=['Black Marble · diario','Black Marble · daily'],unit='source radiance · scale unverified',prefix='',default='sum',frequency='daily',source='VNP46A2 collection 5200, Gap_Filled_DNB_BRDF-Corrected_NTL',resolution='15 arc seconds (~500 m)',status='blocked',note=['Exploración de fuente con relleno NASA. Escala, QA y extractor original pendientes; no certificada.','NASA gap-filled source exploration. Scale, QA and original extractor pending; uncertified.'])}
STATS=['mean','median','min','max','stddev','p10','p25','p75','p90','iqr']
def jsonwrite(p,obj):write_json(p,obj)
def checkpoint(out,**kw):
    p=out/'Evidence/checkpoint.json';d=json.loads(p.read_text(encoding='utf-8')) if p.exists() else {'state':'EXECUTING','products':{}}
    d.update(kw);d['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();jsonwrite(p,d)
def read_csv(source):
    return pd.read_csv(source,dtype={'mun_code':'str','cna_code':'str'},float_precision='round_trip')
def attach(d,path):
    d=d.copy();d['_source_file']=path;d['_source_row']=np.arange(len(d),dtype='int64');return d
def inputs(root,pid):
    folder=root/'Inputs/Satellites'/PRODUCTS[pid]
    if pid=='era5':
        p=next(folder.rglob('*.zip'))
        with zipfile.ZipFile(p) as z:
            frames=[attach(read_csv(io.BytesIO(z.read(n))),p.relative_to(root).as_posix()+'!'+n) for n in sorted(z.namelist()) if n.endswith('.csv')]
        return [('base',pd.concat(frames,ignore_index=True))],[p]
    if pid in ('gpm','fire','vegetation'):
        fs=sorted(folder.rglob('*.csv'));return [('base',pd.concat([attach(read_csv(p),p.relative_to(root).as_posix()) for p in fs],ignore_index=True))],fs
    if pid=='hku':
        fs=sorted(folder.glob('Inputs/NTLVIIRSMonthly/hku_viirs_bolivia_work/outputs/*Admin_Stats*.parquet'))
        assert len(fs)==1,'Exactly one unfiltered HKU base expected'
        return [('base',attach(pd.read_parquet(fs[0]),fs[0].relative_to(root).as_posix()))],fs+sorted(folder.rglob('checkpoints_yearly/*.parquet'))
    if pid=='pm25':
        p=next((folder/'Inputs').glob('*.parquet'));return [('base',attach(pd.read_parquet(p),p.relative_to(root).as_posix()))],[p]+sorted((folder/'Inputs/pm25_monthly').rglob('*.parquet'))
    fs=sorted((folder/'Inputs/daily_raw/vnp46a2_c5200/main_gapfilled').rglob('*.parquet'))
    return [('base',pd.concat([attach(pd.read_parquet(p),p.relative_to(root).as_posix()) for p in fs],ignore_index=True))],fs
def geography(root,out):
    agro=root/'Outputs/Contract_04/Deliverables/BoliviaAgriculturalCensus2013';g=gpd.read_file(agro/'EarthEngine/bolivia339_2015.shp');g['asdf_id']=g.asdf_id.astype(int)
    g=g.sort_values('asdf_id');assert g.asdf_id.tolist()==list(range(339)) and g.is_valid.all() and not g.is_empty.any()
    source=root/'Maps/GeoBolivia_2015_339/bolivia339geoqueryOpt.geojson';j=json.loads(source.read_text(encoding='utf-8'))
    reference=gpd.read_file(source);reference['asdf_id']=reference.asdf_id.astype(int);reference=reference.set_index('asdf_id')
    assert all(row.geometry.equals(reference.loc[row.asdf_id].geometry) for row in g.itertuples())
    repo=out/'Deliverables/BoliviaSatellites';dst=repo/'public/geo';dst.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dst/'bolivia339.geojson')
    (dst/'bolivia339.geojson.gz').write_bytes(gzip.compress(source.read_bytes(),mtime=0))
    meta=g.drop(columns='geometry').to_dict('records');jsonwrite(repo/'public/catalog/geography.json',meta)
    gd=repo/'data/geography';gd.mkdir(parents=True,exist_ok=True)
    for p in (agro/'EarthEngine').glob('bolivia339_2015.*'):
        if not (gd/p.name).exists():shutil.copyfile(p,gd/p.name)
        assert sha(p)==sha(gd/p.name)
    if not (gd/'crosswalk_cna2013_geo4bolivia339.csv').exists():shutil.copyfile(agro/'Agro2013/crosswalk_cna2013_geo4bolivia339.csv',gd/'crosswalk_cna2013_geo4bolivia339.csv')
    jsonwrite(out/'Evidence/audit/geography.json',{'count':339,'valid':339,'equal_geometries':339,'source_sha256':sha(source),'crosswalk_sha256':sha(gd/'crosswalk_cna2013_geo4bolivia339.csv')})
    return g
def variable_metadata(pid,d,variant):
    cfg=CFG[pid];out=[]
    descriptions={
        'country':'Country name/code supplied by source; not a pixel count.',
        'asdf_id':'Original Agriculture polygon identifier; retained from source.',
        'geo_id':'Integer Agriculture asdf_id used for the one-to-one spatial join.',
        'normalized_code':'Agriculture municipal code; original source code remains separately preserved.',
        'period_id':'ISO calendar period YYYY-MM or YYYY-MM-DD, without timezone conversion.',
        '_source_file':'Relative immutable source path; ! separates a ZIP member.',
        '_source_row':'Zero-based row offset within that source table, excluding header.',
        'qa_flags':'C05 diagnostic bitmask: 1 missing, 2 area ratio >1, 4 provider fill, 8 no valid area, 16 upstream unverified, 64 code discrepancy, 256 fire QA unresolved.',
        'mean0':'Native source statistic with definition unresolved; do not infer zero handling or imputation from its name.',
        'prop_non_na_pixels':'Source valid-pixel proportion; dimensionless. Aggregate identity does not certify provider mask.',
        'is_observed':'Native presence flag, not proof of direct unfilled satellite observation.',
        'is_missing_due_to_tile':'Native missing-tile diagnostic; preserved without imputation.',
        'scale_m':'Requested spatial reduction scale in metres, not polygon resolution.',
        'missing_tiles_day':'Native list of missing tile identifiers for the date.',
        'available_tiles_day':'Native list of available tile identifiers for the date.',
        'municipality_area_m2':'Supplied polygon area denominator; original value retained.',
    }
    for col in d.columns:
        numeric=pd.api.types.is_numeric_dtype(d[col]);role='metadata';unit=None
        if col in ['ID_ADMIN','asdf_id','mun_code','cna_code','mun_id','dep_id','ID_PROVINCE','ID_DEPARTMENT','geo_id','normalized_code','gid_3']:role='identifier'
        elif numeric and (col.startswith('prop_') or any(x in col for x in ['share','coverage','fallback','is_observed','is_missing','complete'])):role='quality';unit='dimensionless'
        elif numeric and (col=='nan' or re.search(r'(^|_)count($|_)|pixels$|_images$',col)):role='quality';unit='count'
        elif numeric and 'valid_area' in col:role='quality';unit='m²'
        elif numeric and (col.startswith(('precip_','temperature_','ndvi_','evi_','pm25_','burned_','hp_','kalman_','rolling_','epan_','log_')) or col in ['mean','median','min','max','std','sum','sumsq','mean0']):role='derived' if variant!='base' or col.startswith('log_') else 'value';unit=cfg['unit']
        if col in ['raster_min','raster_max','raster_mean'] and pid=='pm25':role='value';unit=cfg['unit']
        if col=='qa_flags':role='quality';unit='bitmask'
        if col=='_source_row':unit='zero-based row index'
        if col=='scale_m':unit='m'
        if col in ['COORD_X','COORD_Y']:unit='degrees; supplied geographic coordinate'
        if col.endswith('_m2'):unit='m²'
        if col.endswith('_km2') or col=='area_km2':unit='km²'
        if col.startswith(('ndvi_','evi_')) and role!='quality':unit='dimensionless'
        if col=='sumsq':unit='('+cfg['unit']+')²'
        if col.startswith(('log_','hp_','kalman_','rolling_','epan_')):unit='transformed source; see recipe'
        definition=descriptions.get(col,'Native source metadata: '+col)
        stat=col.removeprefix(cfg['prefix']).removeprefix('evi_').removeprefix('ndvi_')
        if role=='value' and col not in descriptions:
            definition={'mean':'Spatial mean over source-valid support; weighting follows upstream recipe.','median':'Spatial median of source-valid values.','min':'Minimum source-valid value.','max':'Maximum source-valid value.','std':'Source spatial standard deviation.','stddev':'Source spatial standard deviation.','iqr':'Spatial p75 minus p25.','sum':'Sum of source pixel values; not a population-weighted total or emission mass.','sumsq':'Sum of squared source values; not a physical total.'}.get(stat,'Native quantitative statistic '+col+'; processing and support follow the product recipe.')
            if re.fullmatch(r'p\d+',stat):definition='Spatial percentile '+stat[1:]+' over source-valid support; not a temporal percentile.'
        if col.startswith('log_'):definition='Native logarithmic diagnostic retained as supplied, not an added map transformation or offered raw indicator.'
        if role=='quality' and col not in descriptions:definition='Native quality/count/support diagnostic '+col+'; raw value retained, certification subject to product limitations.'
        out.append(dict(product=pid,variant=variant,column=col,dtype=str(d[col].dtype),role=role,unit=unit,definition=definition,recipe_id=pid+'-'+variant,verification='documented source / limitations in product card'))
    return out
def normalize(pid,v,d,g,out):
    native=list(c for c in d.columns if not c.startswith('_'));codes=g.set_index('mun_code').asdf_id.to_dict()
    if 'mun_code' in d:
        ids=d.mun_code.map(codes);assert ids.notna().all();d['geo_id']=ids.astype('int16')
    else:d['geo_id']=d.asdf_id.astype('int16')
    assert set(d.geo_id)==set(range(339))
    if pid=='blackmarble':d['period_id']=pd.to_datetime(d.date).dt.strftime('%Y-%m-%d')
    else:d['period_id']=d.year.astype(int).astype(str)+'-'+d.month.astype(int).astype(str).str.zfill(2)
    key=['geo_id','period_id'];dups=d.duplicated(key,keep=False);compare=[x for x in native if x!='system:index']
    evidence=[]
    for k,x in d[dups].groupby(key):
        assert all(x[c].nunique(dropna=False)==1 for c in compare),(pid,k,'conflicting duplicate')
        evidence.append({'geo_id':int(k[0]),'period':k[1],'sources':x[['_source_file','_source_row']].to_dict('records')})
    d=d.drop_duplicates(key).sort_values(['period_id','geo_id']).reset_index(drop=True)
    periods=sorted(d.period_id.unique());assert all(x==339 for x in d.groupby('period_id').size())
    freq='D' if pid=='blackmarble' else 'MS';expected=pd.date_range(periods[0],periods[-1],freq=freq).strftime('%Y-%m-%d' if freq=='D' else '%Y-%m').tolist();assert periods==expected
    d['normalized_code']=d.geo_id.map(g.set_index('asdf_id').mun_code)
    q=np.zeros(len(d),dtype='uint16');prefix=CFG[pid]['prefix'];mean=CFG[pid]['default']
    q[~np.isfinite(d[mean].astype(float))]|=1
    area_col=prefix+'valid_area_share'
    if area_col in d:q[d[area_col].gt(1).fillna(False)]|=2
    if pid=='blackmarble':q|=4|16
    if pid=='fire':q|=256;q[d.burned_valid_area_m2.eq(0)]|=8
    if v!='base':q|=32
    if 'mun_id' in d:
        mismatch=d.mun_id.astype(str).str.replace(r'\.0$','',regex=True).str.zfill(6)!=d.normalized_code
        if pid in ('hku','blackmarble'):q[mismatch]|=64
    d['qa_flags']=q
    audit={'product':pid,'variant':v,'rows':len(d),'periods':len(periods),'first':periods[0],'last':periods[-1],'municipalities':339,'duplicates_removed':sum(len(x['sources'])-1 for x in evidence),'duplicate_groups':evidence,'geography_discrepancies':d.loc[(q&64)!=0,[c for c in ['geo_id','mun_id','normalized_code'] if c in d]].drop_duplicates().to_dict('records'),'numeric':{}}
    for col in native:
        if pd.api.types.is_numeric_dtype(d[col]):
            x=d[col].astype(float);finite=x[np.isfinite(x)];audit['numeric'][col]={'null':int(x.isna().sum()),'nonfinite_nonnull':int((~np.isfinite(x)&x.notna()).sum()),'min':float(finite.min()) if len(finite) else None,'max':float(finite.max()) if len(finite) else None}
    audit['area_gt1_rows']=int(((q&2)!=0).sum());audit['missing_rows']=int(((q&1)!=0).sum());audit['no_valid_area_rows']=int(((q&8)!=0).sum())
    audit['checks']={}
    for pre in ([prefix] if pid!='vegetation' else ['ndvi_','evi_']):
        for low,high in [('min','mean'),('mean','max'),('min','median'),('median','max'),('p10','p25'),('p25','p75'),('p75','p90')]:
            a,b=pre+low,pre+high
            if a in d and b in d:audit['checks'][a+'<='+b]=int((d[a]>d[b]+1e-10).sum())
        if pre+'iqr' in d:audit['checks'][pre+'iqr_error']=float((d[pre+'iqr']-d[pre+'p75']+d[pre+'p25']).abs().max())
    if pid=='gpm':
        expected=pd.to_datetime(d.period_id).dt.days_in_month*48
        audit['checks']['expected_images']=int((d.expected_gpm_images!=expected).sum());audit['checks']['actual_images']=int((d.n_gpm_images!=expected).sum())
    if pid=='fire':audit['checks']['count_zero_positive_area']=int((d.burned_valid_pixel_count.eq(0)&d.burned_valid_area_m2.gt(0)).sum())
    if pid=='blackmarble':audit['checks']['log_mean_error']=float((d.log_mean-np.log1p(d['mean'])).abs().max())
    jsonwrite(out/f'Evidence/audit/{pid}_{v}.json',audit)
    return d,audit,variable_metadata(pid,d,v)

def write_recipes(repo,cards,sources):
    methods={
      'era5':dict(band='temperature_2m',conversion='K - 273.15 -> Celsius',temporal='Monthly aggregate of hourly reanalysis',mask='Supplied GEE band mask; spatial coverage diagnostic unresolved'),
      'gpm':dict(band='precipitation',conversion='sum of half-hourly mm/h * 0.5 h -> mm/month',temporal='Calendar month; image count equals days * 48',mask='Supplied band validity; per-pixel temporal QA not certified'),
      'hku':dict(band='VIIRS-like monthly raster',conversion='Source radiance; local raster-to-provider scale provenance pending',temporal='Provider reconstructed monthly history',mask='rasterstats all_touched=False; nodata handling in supplied notebook'),
      'fire':dict(band='BurnDate and QA',conversion='m2 / 1000000 -> km2',temporal='Monthly product; BurnDate>0',mask='Land/valid QA source recipe; exported count inconsistencies unresolved'),
      'vegetation':dict(band='NDVI, EVI, SummaryQA',conversion='raw index * 0.0001',temporal='Median of 16-day composites with start date in calendar month',mask='SummaryQA <= 1; original mask and coverage preserved'),
      'pm25':dict(band='pm25',conversion='Source concentration micrograms/m3; no emission conversion',temporal='Monthly model estimate',mask='Strict cells and optional all_touched fallback; fallback not activated in these sources'),
      'blackmarble':dict(band='Gap_Filled_DNB_BRDF-Corrected_NTL',conversion='Applied source scale/offset UNVERIFIED',temporal='Daily provider-filled product; original missing days retained',mask='Original Bolivia HDF extractor and masks unavailable; BLOCKED')}
    for card in cards:
        pid=card['id'];code=[{'path':p.relative_to(repo).as_posix(),'sha256':sha(p)} for p in sorted((repo/'code/source_workflows'/pid).rglob('*')) if p.is_file()]
        jsonwrite(repo/'data/recipes'/f'{pid}-base.json',dict(recipe_id=pid+'-base',product=pid,frequency=card['frequency'],resolution=card['resolution'],source=card['source'],method=methods[pid],local_pipeline='code/run.py',workflow_copies=code,immutable_sources=[x for x in sources if x['product']==pid],level_A='Lossless reconstruction from supplied municipal aggregates',level_B='See scientific limitations; no new extraction executed',geography='Original Agriculture 339; asdf_id join; original codes retained'))
def qualify_columns(pid,v,d):
    assert v=='base','Human instruction: unfiltered source series only'
    if pid in ('era5','gpm','pm25'):return [CFG[pid]['prefix']+x for x in STATS+(['std'] if pid=='pm25' else []) if CFG[pid]['prefix']+x in d]
    if pid=='vegetation':return [p+x for p in ['ndvi_','evi_'] for x in STATS if p+x in d]
    if pid=='fire':return ['burned_area_km2','burned_area_share']
    if pid=='blackmarble':return [c for c in FIELDS if c in d]
    if v=='base':return ['mean','median','min','max','std']
    return []
def initial(periods,values,daily=False):
    available=[p for p,row in zip(periods,values) if np.isfinite(row).any()]
    if not available:return {'requested':'2025-11-10' if daily else '2025-11','effective':None,'reason':'no eligible values'}
    year=2025;requested='2025-11-10' if daily else '2025-11'
    effective=next((f'{y}-11-10' if daily else f'{y}-11' for y in range(year,int(periods[0][:4])-1,-1) if (f'{y}-11-10' if daily else f'{y}-11') in available),None)
    return {'requested':requested,'effective':effective,'reason':None if requested==effective else 'Fixed November 2025 reference unavailable; previous November shown explicitly' if effective else 'No November reference'}
def build_data(root,out,selected=None):
    repo=out/'Deliverables/BoliviaSatellites';g=geography(root,out);dictionaries=[];cards=[];files_manifest=[]
    if selected:
        dictionaries=[x for x in json.loads((repo/'data/dictionaries/columns.json').read_text(encoding='utf-8')) if x['product'] not in selected]
        cards=[x for x in json.loads((repo/'data/catalog/products.json').read_text(encoding='utf-8')) if x['id'] not in selected]
        files_manifest=[x for x in json.loads((repo/'provenance/sources.json').read_text(encoding='utf-8')) if x['product'] not in selected]
    for pid in selected or PRODUCTS:
        started=time.perf_counter();variants,files=inputs(root,pid);folder=root/'Inputs/Satellites'/PRODUCTS[pid]
        files+=list(folder.rglob('*.txt'))+list(folder.rglob('*.py'))+list(folder.rglob('*.ipynb'))
        metadata_paths={'pm25':'Inputs/Bolivia_PM25_Validation.json','blackmarble':'Inputs/daily_raw/vnp46a2_c5200/main_gapfilled/metadata/run_metadata.json'}
        if pid in metadata_paths and (folder/metadata_paths[pid]).is_file():files.append(folder/metadata_paths[pid])
        for p in files:
            # All originals remain in Inputs; portable sources retain canonical aggregate versions.
            target=out/'Deliverables/ScientificData/native'/p.relative_to(root);target.parent.mkdir(parents=True,exist_ok=True)
            if p.suffix not in ['.ipynb','.py','.txt']:shutil.copy2(p,target)
            else:
                content=p.read_text(encoding='utf-8-sig',errors='replace')
                if re.search(r'\b(?:hf_[A-Za-z0-9]{25,}|gh[pousr]_[A-Za-z0-9]{30,})\b',content):raise RuntimeError('Credential-like literal in workflow; manual sanitization required before packaging')
                if p.suffix=='.ipynb':
                    book=json.loads(content)
                    if pid=='hku':
                        stop=next(i+1 for i,c in enumerate(book['cells']) if 'COMPILE FINAL MONTHLY PANEL' in ''.join(c['source']))
                        book['cells']=book['cells'][:stop]
                        book.setdefault('metadata',{})['c05_scope']='Unfiltered extraction and unified base only; later preprocessing/filtering cells excluded by human instruction.'
                    for cell in book.get('cells',[]):
                        if cell.get('cell_type')=='code':cell['outputs']=[];cell['execution_count']=None
                    content=json.dumps(book,ensure_ascii=False,indent=1)
                dst=repo/'code/source_workflows'/pid/p.name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_text(content,encoding='utf-8')
                # Keep native code as evidence only; no execution by this runner.
            files_manifest.append({'product':pid,'path':p.relative_to(root).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size})
        baseaudit=None;webparts=[]
        assert len({v for v,d in variants})==len(variants),'Variant name collision'
        for v,d in variants:
            d,audit,dictionary=normalize(pid,v,d,g,out);dictionaries+=dictionary
            if v=='base':baseaudit=audit
            for year,part in d.groupby('year',sort=True):
                target=out/f'Deliverables/ScientificData/master/{pid}/{v}/{int(year)}.parquet';target.parent.mkdir(parents=True,exist_ok=True)
                part=part.reset_index(drop=True);part.to_parquet(target,index=False,compression='zstd')
                pd.testing.assert_frame_equal(part,pd.read_parquet(target),check_exact=True)
                csvpath=target.with_suffix('.csv.gz');part.to_csv(csvpath,index=False,float_format=None,na_rep=r'\N',compression={'method':'gzip','mtime':0})
                checkpoint(out,phase='P2',last_success=f'{pid}/{v}/{year}: parquet roundtrip PASS')
            cols=qualify_columns(pid,v,d)
            if cols:
                part=d[['geo_id','period_id','qa_flags']+cols].copy()
                if v=='base':
                    cov=CFG[pid]['prefix']+'valid_area_share';cnt=CFG[pid]['prefix']+'valid_pixel_count'
                    part['coverage']=d[cov] if cov in d else d['prop_non_na_pixels'] if 'prop_non_na_pixels' in d else np.nan
                    part['pixel_count']=d[cnt] if cnt in d else d['pm25_count'] if 'pm25_count' in d else d['count'] if 'count' in d else np.nan
                webparts.append((v,part))
        # Independent yearly/consolidated equivalence, retaining source type differences.
        equivalence={}
        if pid in ('hku','pm25'):
            annual=[p for p in files if p.suffix=='.parquet' and ('checkpoints_yearly' in str(p) or 'pm25_monthly' in str(p))]
            annualdf=pd.concat([pd.read_parquet(p) for p in annual],ignore_index=True)
            base=next(d for v,d in variants if v=='base');key=['asdf_id','year','month'];aa=annualdf.copy();bb=base.copy()
            for c in key:aa[c]=aa[c].astype(str);bb[c]=bb[c].astype(str)
            aa=aa.sort_values(key).reset_index(drop=True);bb=bb.sort_values(key).reset_index(drop=True)
            for c in annualdf.columns:
                x,y=aa[c],bb[c]
                if c in ['dep_id','mun_id','asdf_id']:x=x.astype(str);y=y.astype(str)
                equivalence[c]=int((~((x==y)|(x.isna()&y.isna()))).sum())
            assert not any(equivalence.values()),equivalence
        if pid=='blackmarble':
            mismatches=[]
            for p in files:
                if p.suffix!='.parquet':continue
                mirror=folder/'Inputs/_hf_download/bolivia339/daily_raw/vnp46a2_c5200/main_gapfilled'/p.relative_to(folder/'Inputs/daily_raw/vnp46a2_c5200/main_gapfilled')
                if not mirror.is_file() or sha(p)!=sha(mirror):mismatches.append(p.name)
            assert not mismatches;equivalence={'mirror_pairs':173,'mismatches':mismatches}
        jsonwrite(out/f'Evidence/reconciliation/{pid}.json',equivalence)
        cfg=dict(CFG[pid]);cfg.update(id=pid,rows=baseaudit['rows'],first=baseaudit['first'],last=baseaudit['last'],period_count=baseaudit['periods'],variant_names=[v for v,d in variants],elapsed_seconds=time.perf_counter()-started)
        cards.append(cfg);jsonwrite(repo/f'data/catalog/{pid}.json',cfg)
        # Web prep is an exact, compact intermediate; web generation remains a distinct command.
        wp=out/'Evidence/webprep';wp.mkdir(parents=True,exist_ok=True)
        allweb=None
        for v,part in webparts:
            part=part.rename(columns={c:f'{v}__{c}' for c in part if c not in ['geo_id','period_id']})
            allweb=part if allweb is None else allweb.merge(part,on=['geo_id','period_id'],validate='one_to_one')
        allweb.to_parquet(wp/f'{pid}.parquet',index=False,compression='zstd')
        cp=json.loads((out/'Evidence/checkpoint.json').read_text(encoding='utf-8'));cp['products'][pid]={'phase':'P2_COMPLETE','science':cfg['status'],'rows':cfg['rows']};jsonwrite(out/'Evidence/checkpoint.json',cp)
        print(f'{pid}: {cfg["rows"]} rows; {len(variants)} variants; {cfg["elapsed_seconds"]:.1f}s',flush=True)
        del variants,webparts,allweb
    jsonwrite(repo/'data/catalog/products.json',cards);jsonwrite(repo/'data/dictionaries/columns.json',dictionaries);jsonwrite(repo/'provenance/sources.json',files_manifest)
    write_recipes(repo,cards,files_manifest)
    jsonwrite(out/'Evidence/audit/quality_policy.json',{'flags':{'1':'missing_source','2':'area_ratio_gt_one_uncertified','4':'provider_gapfilled','8':'no_valid_area','16':'upstream_units_or_provenance_unverified','32':'derived_modelled','64':'source_code_discrepancy_preserved','256':'fire_counts_QA_unresolved'},'no_imputation':True,'ERA_GPM_presentation':'human authorized with warnings; raw ratio not certified'})
def binary(p,array):
    p.parent.mkdir(parents=True,exist_ok=True);a=np.asarray(array,dtype='<f8');p.write_bytes(encode(a,shuffled='blackmarble' in p.parts));assert np.array_equal(decode(p.read_bytes()).reshape(a.shape),a,equal_nan=True)

def lod_indices(values,bins):
    n=len(values);keep=set()
    # Every missing-run boundary is retained, so no gap is bridged by reduction.
    finite=np.isfinite(values);trans=np.flatnonzero(finite[1:]!=finite[:-1])+1
    for x in trans:keep.update([int(x-1),int(x)])
    for lo in range(0,n,max(1,math.ceil(n/bins))):
        hi=min(n,lo+max(1,math.ceil(n/bins)));ix=np.flatnonzero(finite[lo:hi])+lo
        if len(ix):keep.update([int(ix[0]),int(ix[-1]),int(ix[np.argmin(values[ix])]),int(ix[np.argmax(values[ix])])])
    return np.array(sorted(keep),dtype=int)
def build_webdata(out,selected=None):
    repo=out/'Deliverables/BoliviaSatellites';cards=json.loads((repo/'data/catalog/products.json').read_text(encoding='utf-8'));g=json.loads((repo/'public/catalog/geography.json').read_text(encoding='utf-8'));catalog=[]
    for card in cards:
        if selected and card['id'] not in selected:continue
        pid=card['id'];d=pd.read_parquet(out/f'Evidence/webprep/{pid}.parquet');periods=sorted(d.period_id.unique());d=d.sort_values(['period_id','geo_id']);columns=[c for c in d if '__' in c and not c.endswith(('__qa_flags','__coverage','__pixel_count'))];V=len(columns);T=len(periods);daily=pid=='blackmarble'
        matrix=np.stack([d[c].to_numpy(dtype=float).reshape(T,339) for c in columns],axis=2);flags=d['base__qa_flags'].to_numpy(dtype=float).reshape(T,339);coverage=d['base__coverage'].to_numpy(dtype=float).reshape(T,339);counts=d['base__pixel_count'].to_numpy(dtype=float).reshape(T,339)
        wd=repo/'public/data'/pid
        if daily:
            for month in sorted({x[:7] for x in periods}):
                ix=[k for k,x in enumerate(periods) if x.startswith(month)]
                binary(wd/'maps'/(month+'.bin.gz'),np.concatenate([np.column_stack([matrix[k],flags[k],coverage[k],counts[k]]) for k in ix]))
        else:
            for k,date in enumerate(periods):binary(wd/'maps'/(date+'.bin.gz'),np.column_stack([matrix[k],flags[k],coverage[k],counts[k]]))
        for geo in range(339):
            if daily:binary(wd/'series'/(str(geo)+'.bin.gz'),np.column_stack([matrix[:,geo],flags[:,geo],coverage[:,geo],counts[:,geo]]))
            else:binary(wd/'series'/(str(geo)+'.bin.gz'),np.column_stack([matrix[:,geo],flags[:,geo],coverage[:,geo],counts[:,geo]]))
        variables=[]
        for vi,col in enumerate(columns):
            v,n=col.split('__',1);arr=matrix[:,:,vi].copy();arr[(flags.astype(int)&8)!=0]=np.nan;init=initial(periods,arr,daily)
            finite=arr[np.isfinite(arr)];scale=[float(np.min(finite)),float(np.max(finite))] if len(finite) else [0,1]
            variables.append(dict(id=col,native=n,variant=v,unit=('dimensionless' if n.endswith('_share') else card['unit']) if v=='base' else 'modelled / transformed',scale=scale,initial=init))
            from historical_pool import historical_pool
            variables[-1]['historical_pool']=historical_pool(arr,periods[0],periods[-1])
            if daily:variables[-1].update(bm_metadata(n))
            for group,ids in [('national',list(range(339)))]+[(str(dep),[x['asdf_id'] for x in g if x['depto']==dep]) for dep in sorted({x['depto'] for x in g})]:
                a=arr[:,ids];count=np.isfinite(a).sum(axis=1)
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore');q=np.nanquantile(a,[.1,.25,.5,.75,.9],axis=1,method='linear').T;mean=np.nanmean(a,axis=1)
                binary(wd/'groups'/col/(group+'.bin.gz'),np.column_stack([mean,q,count]))
            for level in [128]:
                for block in range(12):
                    values=[];ids=list(range(block*30,min(339,(block+1)*30)))
                    for geo in ids:
                        ix=lod_indices(arr[:,geo],level);values.append({'id':geo,'i':ix.tolist(),'v':[None if not np.isfinite(x) else float(x) for x in arr[ix,geo]]})
                    packed=[len(values)]
                    for line in values:
                        packed.extend([line['id'],len(line['i'])])
                        for ix,val in zip(line['i'],line['v']):packed.extend([ix,np.nan if val is None else val])
                    binary(wd/'lod'/col/str(level)/(str(block)+'.bin.gz'),packed)
        card.update(periods=periods,variables=variables,columns=columns,matrix_width=V+3,default='base__'+card['default'],snapshot='c05-local-v2',source_exploration_required=False,series_layout='municipality_all_variables',map_layout='month_blocks' if daily else 'date_snapshot');catalog.append(card)
        jsonwrite(repo/f'public/catalog/{pid}.json',card);print(f'web {pid}: {T} periods, {V} variables',flush=True)
    catalog=[json.loads((repo/f'public/catalog/{pid}.json').read_text(encoding='utf-8')) for pid in PRODUCTS];jsonwrite(repo/'public/catalog/index.json',[{k:v for k,v in c.items() if k not in ['periods','variables','columns']} for c in catalog]);checkpoint(out,phase='P4_DATA_READY',last_success='Exact compressed arrays, maps, full series, groups and LOD generated')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['audit','build-data','build-webdata','validate','resume']);p.add_argument('--input-root',type=Path,default=Path.cwd());p.add_argument('--output-root',type=Path,default=Path.cwd()/'Outputs/Contract_05');p.add_argument('--checkpoint',type=Path);p.add_argument('--dry-run',action='store_true');p.add_argument('--resume',action='store_true');p.add_argument('--product',choices=list(PRODUCTS));args=p.parse_args()
    if args.dry_run:print(json.dumps(vars(args),default=str));return
    out=args.output_root.resolve();out.mkdir(parents=True,exist_ok=True)
    if args.command=='resume':
        cp=json.loads((args.checkpoint or out/'Evidence/checkpoint.json').read_text(encoding='utf-8'));print(json.dumps(cp,indent=2));print('Explicitly select build-data/build-webdata/validate after checking last successful phase.');return
    if args.command=='audit':
        from preflight import main as pre;pre()
    if args.command=='build-data':build_data(args.input_root.resolve(),out,[args.product] if args.product else None)
    if args.command=='build-webdata':build_webdata(out,[args.product] if args.product else None)
    if args.command=='validate':
        from validate import main as validate;validate(args.input_root.resolve(),out)
if __name__=='__main__':main()
