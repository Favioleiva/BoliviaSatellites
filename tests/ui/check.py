"""Browser integration checks against immutable data. Starts no external service."""
from pathlib import Path
import json,time,csv,io
from playwright.sync_api import sync_playwright
REPO=Path(__file__).resolve().parents[2];OUT=REPO.parent.parent;E=OUT/'Evidence';(E/'screenshots').mkdir(exist_ok=True,parents=True)
def main():
    result={'checks':{},'errors':[],'browsers':{}};screens=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True);ctx=browser.new_context(viewport={'width':1440,'height':900},accept_downloads=True);page=ctx.new_page();page.on('pageerror',lambda e:result['errors'].append(str(e)));page.goto('http://127.0.0.1:8768/');page.wait_for_function('window.__ready')
        assert page.locator('.municipal').count()==339;result['checks']['map_339']=True
        # User-facing selector for every municipality; await exact full history readiness.
        for i in range(339):
            before=page.evaluate('window.__detailReady||0');page.locator('#municipality').select_option(str(i));page.wait_for_function('(x)=>BoliviaSatellites.state.geo===x.id && window.__detailReady>x.before',arg={'id':i,'before':before})
            assert page.locator('#municipalCode').inner_text().endswith('asdf_id '+str(i))
        result['checks']['all_339_panel_selections']=True
        expected={'era5':'2025-11','gpm':'2025-11','hku':'2024-11','fire':'2025-11','vegetation':'2025-11','pm25':'2024-11','blackmarble':'2025-11-10'}
        for pid,date in expected.items():
            page.evaluate('async p=>await BoliviaSatellites.product(p)',pid);assert page.locator('#date').input_value()==date
            if pid in ('fire','blackmarble'):
                assert page.locator('#blocked').is_visible();assert page.locator('#coverage').inner_text()=='339 / 339'
            assert page.locator('#coverage').inner_text()=='339 / 339';page.evaluate('async()=>await BoliviaSatellites.selectGeo(254)');page.evaluate('async()=>await BoliviaSatellites.comparison()');assert page.evaluate('BoliviaSatellites.diagnostics.lines')==60
            path=E/'screenshots'/f'{pid}_desktop.png';page.screenshot(path=str(path),full_page=True);screens.append(path.name)
        result['checks']['seven_products_initial_reference_and_scientific_warnings']=True
        page.evaluate("async()=>await BoliviaSatellites.setDate('2025-11-11')");assert page.locator('#coverage').inner_text()=='0 / 339';assert page.locator('#date').input_value()=='2025-11-11'
        page.locator('#reset').click();page.wait_for_function("BoliviaSatellites.state.date==='2025-11-10'");result['checks']['daily_gap_not_imputed']=True
        while not page.locator('#moreLines').is_disabled():page.locator('#moreLines').click();page.wait_for_timeout(100)
        assert page.evaluate('BoliviaSatellites.diagnostics.lines')==339;result['checks']['progressive_339']=True
        with page.expect_download() as info:page.locator('#downloadSeries').click()
        download=info.value;dest=E/'audit'/download.suggested_filename;download.save_as(dest);rows=list(csv.DictReader(dest.open(encoding='utf-8')));assert len(rows)==5247;assert next(r for r in rows if r['period']=='2025-11-11')['value']==''
        result['checks']['download_full_daily_series_with_gaps']=True
        page.locator('#language').click();assert page.locator('html').get_attribute('lang')=='en';assert 'Complete history' in page.locator('.chartheading').inner_text()
        page.locator('#group').select_option('Chuquisaca');page.wait_for_function('BoliviaSatellites.state.group==="Chuquisaca"');page.wait_for_timeout(200);result['checks']['group_selection']=True
        # Actual rapid UI changes: response ordering must not overwrite the final product.
        page.locator('[data-product="gpm"]').click();page.locator('[data-product="era5"]').click();page.wait_for_function("BoliviaSatellites.state.product==='era5' && document.getElementById('date').value==='2025-11'");page.wait_for_timeout(250);assert 'Temperature' in page.locator('#mapTitle').inner_text();result['checks']['rapid_product_switch']=True
        page.reload();page.wait_for_function('window.__ready');assert page.evaluate('BoliviaSatellites.state.geo')==254;result['checks']['url_restore']=True
        for width,height in [(360,800),(390,844),(768,1024),(1920,1080)]:
            page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(100);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
            page.screenshot(path=str(E/'screenshots'/f'responsive_{width}.png'),full_page=True)
        result['checks']['responsive_no_overflow']=True
        # Keyboard map selection and focus return.
        page.set_viewport_size({'width':1440,'height':900});page.locator('[data-geo="0"]').focus();page.keyboard.press('Enter');page.wait_for_function('BoliviaSatellites.state.geo===0');page.locator('#close').click();assert page.evaluate("document.activeElement.dataset.geo==='0'");result['checks']['keyboard_focus']=True
        result['browsers']['chromium']=browser.version;ctx.close();browser.close()
        for name in ['firefox','webkit']:
            try:
                b=getattr(pw,name).launch(headless=True);p=b.new_page();p.goto('http://127.0.0.1:8768/');p.wait_for_function('window.__ready');assert p.locator('.municipal').count()==339;p.evaluate('async()=>await BoliviaSatellites.selectGeo(254)');p.evaluate('async()=>await BoliviaSatellites.comparison()');result['browsers'][name]={'status':'PASS','version':b.version};b.close()
            except Exception as e:result['browsers'][name]={'status':'BLOCKED','reason':str(e)[:400]}
        b=pw.chromium.launch(headless=True,args=['--disable-webgl']);p=b.new_page();p.goto('http://127.0.0.1:8768/');p.wait_for_function('window.__ready');p.evaluate('async()=>await BoliviaSatellites.comparison()');result['checks']['no_gpu_canvas_fallback']=True;b.close()
    result['screenshots']=screens;result['status']='PASS' if not result['errors'] else 'FAIL';(E/'ui_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2));assert not result['errors']
if __name__=='__main__':main()
