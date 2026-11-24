import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'code'))
from run import initial,lod_indices
import numpy as np
def test_daily_exact_and_partial_endpoint():
    x=initial(['2025-11-10','2026-05-31'],[[1],[2]],True);assert x['requested']=='2025-11-10' and x['effective']=='2025-11-10'
def test_monthly_reference():
    assert initial(['2024-11','2024-12'],[[2],[3]])['effective']=='2024-11'
def test_no_november_and_no_values():
    assert initial(['2026-05'],[[1]])['effective'] is None
    assert initial(['2026-11'],[[np.nan]])['requested']=='2025-11'
def test_national_and_municipal_gaps():
    assert initial(['2024-11-10','2025-11-10'],[[2,np.nan],[np.nan,np.nan]],True)['effective']=='2024-11-10'
    assert initial(['2024-11-10','2025-11-10'],[[2,1],[np.nan,3]],True)['effective']=='2025-11-10'
def test_no_nearest_day_substitution():
    assert initial(['2024-11-09','2024-11-11'],[[1],[2]],True)['effective'] is None
def test_leap_and_variant_shorter_coverage():
    assert initial(['2024-02-29','2024-11-10'],[[0],[1]],True)['effective']=='2024-11-10'
    assert initial(['2023-11','2024-11'],[[1],[np.nan]])['requested']=='2025-11'
def test_lod_gap_boundaries_extrema_and_original_indices():
    x=np.array([0,1,80,2,np.nan,np.nan,0,-40,2,0]*100,dtype=float);ix=lod_indices(x,20)
    assert np.nanmax(x[ix])==80 and np.nanmin(x[ix])==-40
    for i in np.flatnonzero(np.isfinite(x[1:])!=np.isfinite(x[:-1]))+1:assert i in ix and i-1 in ix
    assert len(lod_indices(np.full(100,np.nan),10))==0

def test_updated_snapshot_and_constant_zero():
    assert initial(['2025-11-10','2026-11-10'],[[2],[0]],True)['effective']=='2025-11-10'
    x=np.zeros(100);ix=lod_indices(x,10);assert len(ix)>0 and np.all(x[ix]==0)
