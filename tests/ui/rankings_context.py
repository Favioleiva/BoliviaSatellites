"""Independent source checks for both rankings and original-value context means."""
from pathlib import Path
import json
import math
import numpy as np
import pyarrow.parquet as pq
from playwright.sync_api import sync_playwright

R=Path(__file__).resolve().parents[2]
E=R.parent.parent/'Evidence/revision_08_wide_rankings/regression_rankings'
E.mkdir(parents=True,exist_ok=True)
result={'checks':[],'errors':[],'variables':[]}
def check(name,condition):
    assert condition,name
    result['checks'].append(name)
def close(actual,expected):
    return math.isclose(float(actual),float(expected),rel_tol=1e-12,abs_tol=1e-12)

with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True)
    p=browser.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce',accept_downloads=True)
    p.on('pageerror',lambda e:result['errors'].append(str(e)))
    p.goto((R/'dist/index.html').as_uri());p.wait_for_function('window.__ready')
    for pid in ['era5','gpm','hku','fire','vegetation','pm25','blackmarble']:
        card=json.loads((R/'public/catalog'/f'{pid}.json').read_text(encoding='utf-8'))
        natives=[v['native'] for v in card['variables']]
        pooled={n:[] for n in natives};history={n:[] for n in natives};snapshots={}
        # Independent annual reads, using source flags; only totals retained.
        for source in sorted((R.parent/'ScientificData/master'/pid/'base').glob('*.parquet')):
            frame=pq.read_table(source,columns=['geo_id','period_id','qa_flags']+natives).to_pandas()
            eligible=(frame.qa_flags.astype(int)&8)==0
            if source.stem in {v['initial']['effective'][:4] for v in card['variables'] if v['initial']['effective']}:
                snapshots[source.stem]=frame
            for n in natives:
                values=frame.loc[eligible & np.isfinite(frame[n]),n].to_numpy(dtype=np.longdouble)
                pooled[n].append((values.sum(dtype=np.longdouble),len(values)))
                values=frame.loc[eligible & (frame.geo_id==254) & np.isfinite(frame[n]),n].to_numpy(dtype=np.longdouble)
                history[n].append((values.sum(dtype=np.longdouble),len(values)))
        p.evaluate('async id=>await BoliviaSatellites.product(id)',pid)
        p.evaluate('async()=>await BoliviaSatellites.selectGeo(254)')
        for var in card['variables']:
            p.evaluate('async id=>await BoliviaSatellites.variable(id)',var['id'])
            date=p.locator('#date').input_value();frame=snapshots[date[:4]];n=var['native'];tag=pid+'/'+n
            valid=frame.loc[(frame.period_id==date)&np.isfinite(frame[n])&((frame.qa_flags.astype(int)&8)==0)]
            for list_id,ascending in [('rankingList',False),('bottomRankingList',True)]:
                expected=valid.sort_values([n,'geo_id'],ascending=[ascending,True]).head(10).geo_id.astype(int).tolist()
                actual=p.locator('#'+list_id+' button').evaluate_all('(es)=>es.map(e=>+e.dataset.rankGeo)')
                check(tag+'/'+list_id,actual==expected)
            totals=pooled[n];pool=sum(x[0] for x in totals)/sum(x[1] for x in totals)
            totals=history[n];municipality=sum(x[0] for x in totals)/sum(x[1] for x in totals)
            period=valid[n].to_numpy(dtype=np.longdouble).mean()
            selected=valid.loc[valid.geo_id==254,n]
            expected_values={'contextPool':pool,'contextPeriod':period,'contextMunicipality':municipality}
            if len(selected):expected_values['contextObservation']=selected.iloc[0]
            for element,expected in expected_values.items():
                check(tag+'/'+element,close(p.locator('#'+element).get_attribute('data-value'),expected))
            result['variables'].append({'product':pid,'variable':n,'date':date,'status':'PASS'})
        p.evaluate('async id=>await BoliviaSatellites.variable(id)',card['default'])
        bottom=p.locator('#bottomRankingList button').first
        selected=int(bottom.get_attribute('data-rank-geo'));bottom.click()
        p.wait_for_function('id=>BoliviaSatellites.state.geo===id && document.getElementById("contextMunicipality").dataset.value!==""',arg=selected)
        check(pid+'/bottom_click_sync',p.locator('.municipal.selected').get_attribute('data-geo')==str(selected) and p.locator('#bottomRankingList button[aria-pressed=true]').count()>=1)
        before=p.locator('#contextPool').get_attribute('data-value')
        p.evaluate('async()=>await BoliviaSatellites.setDate("1900-01")')
        check(pid+'/missing_date',p.locator('#rankingList button').count()==0 and p.locator('#bottomRankingList button').count()==0 and p.locator('#contextPeriod').get_attribute('data-value')=='' and p.locator('#contextObservation').get_attribute('data-value')=='' and p.locator('#contextPool').get_attribute('data-value')==before)
    p.evaluate('async()=>await BoliviaSatellites.product("blackmarble")')
    p.evaluate('async()=>await BoliviaSatellites.selectGeo(254)')
    original=p.locator('.context-grid dd').evaluate_all('(es)=>es.map(e=>e.dataset.value)')
    p.locator('#mapTransform').select_option('linear')
    check('scale_changes_leave_all_context_values_original',p.locator('.context-grid dd').evaluate_all('(es)=>es.map(e=>e.dataset.value)')==original)
    p.locator('#mapTransform').select_option('log1p1000')
    p.locator('#mapWorkspace').scroll_into_view_if_needed();p.locator('#mapWorkspace').screenshot(path=str(E/'blackmarble_context.png'))
    p.evaluate('async()=>await BoliviaSatellites.product("era5")')
    p.locator('#mapWorkspace').scroll_into_view_if_needed();p.locator('#mapWorkspace').screenshot(path=str(E/'context_es.png'))
    check('rankings_side_by_side',p.locator('#bottomRankingList').bounding_box()['x']>p.locator('#rankingList').bounding_box()['x'])
    check('fluid_workspace_and_map',p.locator('#mapWorkspace').bounding_box()['width']>=0.95*1440 and p.locator('#map').bounding_box()['height']>=600)
    p.locator('#language').click()
    check('English_context_labels','Raw pool mean' in p.locator('.map-context').inner_text() and 'Lowest values' in p.locator('.ranking').inner_text())
    p.locator('#mapWorkspace').scroll_into_view_if_needed();p.locator('#mapWorkspace').screenshot(path=str(E/'context_en.png'))
    p.set_viewport_size({'width':390,'height':844});p.locator('.map-context').scroll_into_view_if_needed();p.screenshot(path=str(E/'context_mobile.png'))
    p.locator('.ranking').scroll_into_view_if_needed();p.screenshot(path=str(E/'rankings_mobile.png'))
    check('mobile_no_overflow',p.evaluate('document.documentElement.scrollWidth<=innerWidth'))
    check('no_javascript_errors',not result['errors'])
    browser.close()
result['status']='PASS'
(E/'validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'status':'PASS','checks':len(result['checks']),'variables':len(result['variables'])}))
