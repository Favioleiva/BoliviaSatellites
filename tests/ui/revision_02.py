"""Direct-file regression, Agriculture comparison and current-build visual QA."""
from pathlib import Path
import json,hashlib,time,urllib.parse,subprocess,sys,urllib.request
from playwright.sync_api import sync_playwright
import pyarrow.parquet as pq
R=Path(__file__).resolve().parents[2];O=R.parent.parent;E=O/'Evidence/revision_02';W=O.parents[1]
E.mkdir(parents=True,exist_ok=True)
result={'checks':{},'errors':[],'external_requests':[],'screenshots':[],'measurements':{}}
def shot(p,name,full=False):
    p.screenshot(path=str(E/name),full_page=full);result['screenshots'].append(name)
def check(name,value=True):
    assert value,name;result['checks'][name]='PASS'
def path_url(url):
    return Path(urllib.request.url2pathname(urllib.parse.urlparse(url).path))

with sync_playwright() as pw:
    b=pw.chromium.launch(headless=True);ctx=b.new_context(viewport={'width':1440,'height':1000},accept_downloads=True,reduced_motion='reduce')
    def route(r):
        if r.request.url.startswith(('http:','https:')):result['external_requests'].append(r.request.url);r.abort()
        else:r.continue_()
    ctx.route('**/*',route);p=ctx.new_page();p.on('pageerror',lambda err:result['errors'].append(str(err)))
    p.goto((R.parent/'ABRIR_BOLIVIA_SATELLITES.html').as_uri());p.wait_for_function('window.__ready');p.wait_for_function('document.querySelectorAll("#downloadList a").length>=11')
    check('double_click_entry_loads_339_without_server',p.locator('.municipal').count()==339)
    check('unique_element_ids',p.evaluate('(()=>{const a=[...document.querySelectorAll("[id]")].map(e=>e.id);return a.length===new Set(a).size})()'))
    check('illustrated_hero_loaded',p.locator('.heroVisual img').evaluate('(e)=>e.complete&&e.naturalWidth===1536'))
    shot(p,'final_desktop_es.png')
    p.locator('#language').click();check('visible_English_link',p.locator('html').get_attribute('lang')=='en' and 'One landscape.' in p.locator('#heroTitle').inner_text());shot(p,'final_desktop_en.png')
    p.locator('#spanish').click();check('visible_Espanol_link',p.locator('html').get_attribute('lang')=='es')
    links=p.locator('#downloadList a').evaluate_all('(es)=>es.map(e=>({url:e.href,name:e.download}))')
    check('all_local_package_links_exist',all(path_url(x['url']).is_file() for x in links))
    p.locator('[data-i18n="heroData"]').click();check('hero_data_opens_downloads',p.locator('#downloadSection').get_attribute('open') is not None)
    p.locator('[data-i18n="heroExplore"]').click();p.wait_for_timeout(300)
    # Real map click opens a complete municipal time series, not just an API call.
    p.locator('#map').scroll_into_view_if_needed()
    hit=p.locator('[data-geo="254"]').evaluate('''e=>{let b=e.getBBox(),m=e.getScreenCTM();for(let y=b.y;y<b.y+b.height;y+=.3)for(let x=b.x;x<b.x+b.width;x+=.3){let q=new DOMPoint(x,y);if(e.isPointInFill(q)){let s=q.matrixTransform(m);if(document.elementFromPoint(s.x,s.y)===e)return {x:s.x,y:s.y}}}}''')
    p.mouse.click(hit['x'],hit['y']);p.wait_for_function('window.__detailReady && BoliviaSatellites.state.geo===254')
    check('map_click_opens_sidebar_and_history',p.locator('#municipalDetail').is_visible() and '437' in p.locator('#historyMeta').inner_text())
    p.locator('#mapWorkspace').scroll_into_view_if_needed();shot(p,'final_temperature_map_panel.png')
    check('right_panel_chart_then_ranking_only',p.locator('#detail #municipalQA').count()==0 and p.locator('#detail #downloadSeries').count()==0 and p.locator('#spark').bounding_box()['y']<p.locator('#rankingList').bounding_box()['y'])
    shot(p,'final_chart_top10.png')
    result['measurements']['satellites_map_1440']=p.locator('#map').bounding_box()
    ref=ctx.new_page();ref.goto((W/'Outputs/Contract_04/Deliverables/BoliviaAgriculturalCensus2013/Agro2013/index.html').as_uri());ref.wait_for_function('document.querySelectorAll(".municipality").length===339')
    result['measurements']['agriculture_c04_map_1440']=ref.locator('.mapsvg').bounding_box()
    a=result['measurements']['satellites_map_1440'];c=result['measurements']['agriculture_c04_map_1440']
    check('map_dimensions_match_Agriculture_C04',abs(a['width']-c['width'])<1 and abs(a['height']-c['height'])<1)
    ref.locator('.workspace').scroll_into_view_if_needed();shot(ref,'reference_agriculture_c04_map.png');ref.close()
    ref=ctx.new_page();ref.goto((W/'Outputs/Contract_02/Deliverables/Agro2013/index.html').as_uri());ref.wait_for_timeout(500);shot(ref,'reference_agriculture_c02.png');ref.close()
    expected={'era5':'2025-11','gpm':'2025-11','hku':'2024-11','fire':'2025-11','vegetation':'2025-11','pm25':'2024-11','blackmarble':'2025-11-10'}
    palettes={}
    for pid,date in expected.items():
        p.evaluate('async id=>await BoliviaSatellites.product(id)',pid)
        if pid in ('fire','blackmarble'):
            check(pid+'_warning_visible_without_gate',p.locator('#blocked').is_visible() and p.evaluate('BoliviaSatellites.state.explore'))
        check(pid+'_initial_date',p.locator('#date').input_value()==date)
        check(pid+'_339_observations',p.locator('#coverage').inner_text()=='339 / 339')
        check(pid+'_fixed_2025_requested',p.evaluate('BoliviaSatellites.state.requested')==('2025-11-10' if pid=='blackmarble' else '2025-11'))
        check(pid+'_top10_available',p.locator('#rankingList button').count()==10)
        native=p.evaluate('BoliviaSatellites.state.variable').split('__',1)[1]
        frame=pq.read_table(R.parent/'ScientificData/master'/pid/'base'/(date[:4]+'.parquet'),columns=['geo_id','period_id','qa_flags',native]).to_pandas()
        expected_ids=frame.loc[(frame.period_id==date)&frame[native].notna()&((frame.qa_flags.astype(int)&8)==0)].sort_values([native,'geo_id'],ascending=[False,True]).head(10).geo_id.astype(int).tolist()
        check(pid+'_top10_matches_original',p.locator('#rankingList button').evaluate_all('(es)=>es.map(e=>+e.dataset.rankGeo)')==expected_ids)
        rank_id=expected_ids[0];p.locator('#rankingList button').first.click();p.wait_for_function('(id)=>BoliviaSatellites.state.geo===id',arg=rank_id)
        check(pid+'_ranking_selects_map',p.locator('.municipal.selected').get_attribute('data-geo')==str(rank_id))
        p.evaluate('async()=>await BoliviaSatellites.selectGeo(254)')
        palettes[pid]=p.evaluate('({key:BoliviaSatellites.paletteKey(),gradient:document.querySelector(".ramp").style.background,mid:document.getElementById("legendMid").textContent})')
        p.locator('#mapWorkspace').scroll_into_view_if_needed();shot(p,'palette_'+pid+'.png')
    check('product_palettes_and_requested_shared_nightlights',palettes['hku']['gradient']==palettes['blackmarble']['gradient']==palettes['era5']['gradient'] and len({v['gradient'] for v in palettes.values()})==5);result['palettes']=palettes
    check('blackmarble_sum_is_primary_indicator',p.locator('#variable').input_value()=='base__sum')
    check('blackmarble_all_23_original_numeric_fields',p.locator('#variable option').count()==23)
    check('nightlights_default_ln1000',p.locator('#mapTransform').input_value()=='log1p1000')
    axes=p.evaluate('window.__chartScales.spark')
    import math
    expected_min=math.log1p(1000*axes['sourceMin']);expected_max=math.log1p(1000*axes['sourceMax']);padding=(expected_max-expected_min)*.07 or 1
    check('spark_actual_axis_uses_ln1000',abs(axes['min']-(expected_min-padding))<1e-9 and abs(axes['max']-(expected_max+padding))<1e-9)
    check('spark_formula_disclosed','ln(1000x + 1)' in p.locator('#sparkScale').inner_text())
    check('blackmarble_six_variable_groups',p.locator('#variable optgroup').count()==6)
    p.locator('#variable').select_option('base__sum');p.wait_for_function("BoliviaSatellites.state.variable==='base__sum' && window.__detailReady")
    p.evaluate('async()=>await BoliviaSatellites.selectGeo(254)');check('blackmarble_sum_renders',p.locator('#coverage').inner_text()=='339 / 339')
    p.locator('#mapWorkspace').scroll_into_view_if_needed();shot(p,'blackmarble_sum.png')
    with p.expect_download() as download:p.locator('#downloadSeries').click()
    target=E/'blackmarble_sum.csv';download.value.save_as(target)
    import csv,pyarrow.parquet as pq
    csvrows=list(csv.DictReader(target.open(encoding='utf-8')))
    source=pq.read_table(R.parent/'ScientificData/master/blackmarble/base/2025.parquet',columns=['geo_id','period_id','sum']).to_pandas()
    expected_sum=float(source.loc[(source.geo_id==254)&(source.period_id=='2025-11-10'),'sum'].iloc[0])
    check('blackmarble_sum_csv_matches_original_master',float(next(x['value'] for x in csvrows if x['period']=='2025-11-10'))==expected_sum)
    p.locator('#variable').select_option('base__sum');p.wait_for_function("BoliviaSatellites.state.variable==='base__sum'")
    # Thousands of daily observations; progressive access all 339 series.
    p.evaluate('async()=>await BoliviaSatellites.comparison()')
    check('spaghetti_formula_synchronized','ln(1000x + 1)' in p.locator('#comparisonScale').inner_text())
    for i in range(10):
        if p.locator('#moreLines').is_disabled():break
        before=p.evaluate('BoliviaSatellites.diagnostics.lines');p.locator('#moreLines').click();p.wait_for_function('(n)=>BoliviaSatellites.diagnostics.lines>n',arg=before)
    check('daily_spaghetti_progressive_339',p.evaluate('BoliviaSatellites.diagnostics.lines')==339)
    p.locator('#comparison').scroll_into_view_if_needed();shot(p,'daily_339_spaghetti.png')
    p.locator('#language').click();check('visual_reduction_notice_English','Visual reduction' in p.locator('#sparkLODNotice').inner_text());shot(p,'daily_339_spaghetti_en.png')
    p.evaluate("async()=>await BoliviaSatellites.setDate('2025-11-11')");check('missing_daily_date_not_imputed',p.locator('#coverage').inner_text()=='0 / 339')
    p.evaluate("async()=>await BoliviaSatellites.product('gpm')");hashes=[]
    for scale in ['linear','log1p','log1p1000']:
        p.locator('#mapTransform').select_option(scale)
        with p.expect_download() as d:p.locator('#downloadSeries').click()
        f=E/('gpm_'+scale+'.csv');d.value.save_as(f);hashes.append(hashlib.sha256(f.read_bytes()).hexdigest())
    check('three_map_scales_download_identical_raw_csv',len(set(hashes))==1);result['raw_csv_sha256']=hashes[0]
    p.evaluate("async()=>await BoliviaSatellites.product('era5')");p.locator('#variable').select_option('base__temperature_stddev');p.wait_for_function("BoliviaSatellites.state.variable==='base__temperature_stddev'")
    check('temperature_dispersion_not_cold_hot',p.evaluate('BoliviaSatellites.paletteKey()')=='dispersion')
    p.evaluate("async()=>await BoliviaSatellites.product('vegetation')");p.locator('#variable').select_option('base__evi_mean');p.wait_for_function("BoliviaSatellites.state.variable==='base__evi_mean'");check('distinct_EVI_palette',p.evaluate('BoliviaSatellites.paletteKey()')=='evi')
    p.evaluate("async()=>await BoliviaSatellites.product('era5')")
    for width,height in [(360,800),(390,844),(768,1024),(1440,1000),(1920,1080)]:
        p.set_viewport_size({'width':width,'height':height})
        for lang,selector in [('es','#spanish'),('en','#language')]:
            p.locator(selector).click();p.evaluate('scrollTo(0,0)');p.wait_for_timeout(150)
            check(f'no_horizontal_overflow_{width}_{lang}',p.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            if width==390:shot(p,f'final_mobile_{lang}.png');p.locator('#mapWorkspace').scroll_into_view_if_needed();shot(p,f'final_mobile_map_{lang}.png')
    # Open the actual English entry from scratch, including launcher query forwarding.
    p.goto((R.parent/'ABRIR_BOLIVIA_SATELLITES.html').as_uri()+'?lang=en');p.wait_for_function('window.__ready');check('English_entry_direct',p.locator('html').get_attribute('lang')=='en')
    result['browser']=b.version;check('no_page_errors',not result['errors']);check('no_external_requests',not result['external_requests']);b.close()
result['status']='PASS';(E/'ui_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'status':result['status'],'checks':len(result['checks']),'measurements':result['measurements']},indent=2))
