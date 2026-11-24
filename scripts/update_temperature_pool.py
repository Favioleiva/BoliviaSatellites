"""Refresh only display metadata from preserved masters; no data rewriting."""
from pathlib import Path
import json
import sys
import pyarrow.parquet as pq
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'code'))
from historical_pool import historical_pool

def main():
    path = R / 'public/catalog/era5.json'
    catalog = json.loads(path.read_text(encoding='utf-8'))
    frame = pq.read_table(sorted((R.parent / 'ScientificData/master/era5/base').glob('*.parquet'))).to_pandas()
    eligible = frame.loc[(frame.qa_flags.astype(int) & 8) == 0]
    for variable in catalog['variables']:
        pool = historical_pool(eligible[variable['native']], catalog['first'], catalog['last'])
        assert variable['scale'] == [pool['minimum'], pool['maximum']], variable['id']
        variable['historical_pool'] = pool
    path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({v['id']:v['historical_pool'] for v in catalog['variables']}, indent=2))

if __name__ == '__main__':
    main()
