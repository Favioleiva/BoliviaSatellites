"""Convert retained first-candidate LOD to the tested compact format; source data untouched."""
from pathlib import Path
import gzip,json,numpy as np,pandas as pd
from run import binary
out=Path.cwd()/'Outputs/Contract_05';repo=out/'Deliverables/BoliviaSatellites'
for product in (out/'Evidence/benchmarks/candidate_json_lod').iterdir():
    for f in product.rglob('*.json.gz'):
        rel=f.relative_to(product)
        if product.name!='blackmarble' and rel.parts[1]=='512':continue
        values=json.loads(gzip.decompress(f.read_bytes()));packed=[len(values)]
        for line in values:
            packed.extend([line['id'],len(line['i'])])
            for i,v in zip(line['i'],line['v']):packed.extend([i,np.nan if v is None else v])
        binary(repo/'public/data'/product.name/'lod'/rel.parent/(f.stem.replace('.json','')+'.bin.gz'),packed)
# Restore fire raw zeros in exact distribution arrays. QA masks only the view.
d=pd.read_parquet(out/'Evidence/webprep/fire.parquet').sort_values(['period_id','geo_id']);card=json.loads((repo/'public/catalog/fire.json').read_text(encoding='utf-8'));T=len(card['periods']);cols=card['columns'];raw=np.stack([d[c].to_numpy(float).reshape(T,339) for c in cols],axis=2);flags=d['base__qa_flags'].to_numpy(float).reshape(T,339);cov=d['base__coverage'].to_numpy(float).reshape(T,339);cnt=d['base__pixel_count'].to_numpy(float).reshape(T,339)
for i,date in enumerate(card['periods']):binary(repo/'public/data/fire/maps'/f'{date}.bin.gz',np.column_stack([raw[i],flags[i],cov[i],cnt[i]]))
for geo in range(339):binary(repo/'public/data/fire/series'/f'{geo}.bin.gz',np.column_stack([raw[:,geo],flags[:,geo],cov[:,geo],cnt[:,geo]]))
files=[p for p in (repo/'public').rglob('*') if p.is_file()];print({'files':len(files),'bytes':sum(p.stat().st_size for p in files)})
