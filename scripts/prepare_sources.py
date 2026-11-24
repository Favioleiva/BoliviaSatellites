"""Assemble the supplied aggregate packages into an isolated reproducible input tree."""
from pathlib import Path
import argparse, shutil

repo=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True,help='Directory containing sources/ from all seven extracted data packages');p.add_argument('--destination',type=Path,required=True);a=p.parse_args()
assert not a.destination.exists(),'Use an absent destination; existing sources are never overwritten.'
assert (a.data/'sources/Inputs/Satellites').is_dir(),'Extract all data parts into the same directory first.'
shutil.copytree(a.data/'sources',a.destination,copy_function=shutil.copyfile)
geo=a.destination/'Outputs/Contract_04/Deliverables/BoliviaAgriculturalCensus2013'
for f in (repo/'data/geography').glob('bolivia339_2015.*'):
    target=geo/'EarthEngine'/f.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target)
f=repo/'data/geography/crosswalk_cna2013_geo4bolivia339.csv';target=geo/'Agro2013'/f.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target)
target=a.destination/'Maps/GeoBolivia_2015_339/bolivia339geoqueryOpt.geojson';target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(repo/'public/geo/bolivia339.geojson',target)
bm=a.destination/'Inputs/Satellites/NASA_BlackMarble_Daily/Inputs'
shutil.copytree(bm/'daily_raw',bm/'_hf_download/bolivia339/daily_raw',copy_function=shutil.copyfile)
print('Prepared isolated aggregate sources. The audit mirror is a byte-identical copy, not additional observations.')
