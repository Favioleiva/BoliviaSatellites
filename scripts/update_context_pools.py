"""Small display summaries from immutable local masters, one year at a time."""
from pathlib import Path
import json
import math
import numpy as np
import pyarrow.parquet as pq

R = Path(__file__).resolve().parents[1]

def main():
    for pid in ['era5','gpm','hku','fire','vegetation','pm25','blackmarble']:
        path = R / 'public/catalog' / (pid + '.json')
        card = json.loads(path.read_text(encoding='utf-8'))
        stats = {v['id']:dict(sums=[], count=0, minimum=math.inf, maximum=-math.inf,
            transforms={key:dict(sums=[],invalid=0) for key in ['log1p','log1p1000']}) for v in card['variables']}
        columns = ['qa_flags'] + list(dict.fromkeys(v['native'] for v in card['variables']))
        for source in sorted((R.parent/'ScientificData/master'/pid/'base').glob('*.parquet')):
            table = pq.read_table(source, columns=columns)
            eligible = (table['qa_flags'].to_numpy().astype(int) & 8) == 0
            for var in card['variables']:
                values = table[var['native']].to_numpy().astype(float)
                values = values[eligible & np.isfinite(values)]
                if not len(values): continue
                s = stats[var['id']]
                s['sums'].append(math.fsum(values)); s['count'] += len(values)
                s['minimum'] = min(s['minimum'], float(values.min()))
                s['maximum'] = max(s['maximum'], float(values.max()))
                for key,k in [('log1p',1),('log1p1000',1000)]:
                    ok=1+k*values>0
                    t=s['transforms'][key];t['invalid']+=int((~ok).sum())
                    t['sums'].append(math.fsum(np.log1p(k*values[ok])))
        for var in card['variables']:
            s = stats[var['id']]; n = s['count']
            pool = dict(minimum=s['minimum'] if n else None, maximum=s['maximum'] if n else None,
                mean=math.fsum(s['sums'])/n if n else None, count=n, first=card['first'], last=card['last'],
                weighting='equal municipality-period observations',
                eligibility='finite source value and no qa_flags bit 8; area ratio >1 retained',
                scope='all municipalities and all available periods, separately for each variable')
            if var.get('historical_pool'):
                assert math.isclose(var['historical_pool']['mean'],pool['mean'],rel_tol=1e-14,abs_tol=1e-14)
                # Preserve previously computed fixed-temperature reference exactly.
            else: var['historical_pool'] = pool
            pool=var['historical_pool']
            centres={'linear':dict(available=bool(n),count=n,invalid_count=0,
                display_mean=pool['mean'],original_center=pool['mean'])}
            for key,k in [('log1p',1),('log1p1000',1000)]:
                t=s['transforms'][key];available=bool(n) and not t['invalid']
                mean=math.fsum(t['sums'])/n if available else None
                centres[key]=dict(available=available,count=n,invalid_count=t['invalid'],
                    display_mean=mean,original_center=math.expm1(mean)/k if available else None)
            pool['centres']=centres
        path.write_text(json.dumps(card,ensure_ascii=False,indent=2),encoding='utf-8')
        print(pid,len(card['variables']),flush=True)

if __name__ == '__main__': main()
