"""Losslessly regroup daily transport into months; scientific periods stay daily."""
from pathlib import Path
import sys,json,numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'code'))
from webcodec import decode,encode
E=R.parent.parent/'Evidence/revision_02';old=E/'blackmarble_candidate/Deliverables/BoliviaSatellites/public';new=E/'blackmarble_compact';assert not new.exists()
card=json.loads((old/'catalog/blackmarble.json').read_text(encoding='utf-8'));T=len(card['periods']);V=card['matrix_width'];records=[]
def write(rel,arr):
    p=new/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(encode(arr,True));assert np.array_equal(decode(p.read_bytes()).reshape(arr.shape),arr,equal_nan=True);records.append(str(rel))
wd=old/'data/blackmarble'
for month in sorted({x[:7] for x in card['periods']}):
    rows=[decode((wd/'maps'/f'{date}.bin.gz').read_bytes()).reshape(339,V) for date in card['periods'] if date.startswith(month)]
    write(Path('maps')/(month+'.bin.gz'),np.concatenate(rows))
for kind,shape in [('series',(T,V)),('groups',(T,7)),('lod',None)]:
    for p in (wd/kind).rglob('*.gz'):
        a=decode(p.read_bytes());write(p.relative_to(wd),a.reshape(shape) if shape else a)
card.update(map_layout='month_blocks',series_layout='municipality_all_variables',encoding='C05SHF02 + gzip; exact Float64; column-major byte shuffle')
(E/'blackmarble_extended_catalog.json').write_text(json.dumps(card,ensure_ascii=False,indent=2),encoding='utf-8')
files=list(new.rglob('*.gz'));size=sum(p.stat().st_size for p in files)
result={'status':'EXACT_ROUNDTRIP_PASS','files':len(files),'blackmarble_bytes':size,'max_map_bytes':max(p.stat().st_size for p in (new/'maps').glob('*.gz')),'max_series_bytes':max(p.stat().st_size for p in (new/'series').glob('*.gz')),'periods_unchanged':True,'fields':len(card['variables'])}
(E/'blackmarble_compact_validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
