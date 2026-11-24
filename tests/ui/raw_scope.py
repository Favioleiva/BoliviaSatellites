"""Regression: map scales cannot change any downloaded observation."""
from pathlib import Path
import hashlib,json
from playwright.sync_api import sync_playwright
repo=Path(__file__).resolve().parents[2];e=repo.parent.parent/'Evidence'
result={}
with sync_playwright() as pw:
    b=pw.chromium.launch(headless=True);p=b.new_page(viewport={'width':1440,'height':900},accept_downloads=True,reduced_motion="reduce")
    p.goto('http://127.0.0.1:8768/?product=gpm&geo=254');p.wait_for_function('window.__ready');hashes=[]
    for scale in ['linear','log1p','log1p1000']:
        p.locator('#mapTransform').select_option(scale)
        with p.expect_download() as info:p.locator('#downloadSeries').click()
        dest=e/'audit'/f'raw_gpm_{scale}.csv';info.value.save_as(dest);hashes.append(hashlib.sha256(dest.read_bytes()).hexdigest())
    assert len(set(hashes))==1;result['map_scales_keep_download_byte_identical']=hashes[0]
    p.evaluate("async()=>await BoliviaSatellites.product('era5')")
    assert p.locator('#mapTransform option[value="log1p"]').is_disabled();assert p.locator('#mapTransform option[value="log1p1000"]').is_disabled();result['temperature_log_domain_guard']=True
    p.evaluate("async()=>await BoliviaSatellites.product('hku')");assert p.locator('#variable option').count()==5;assert p.locator('#mapTransform').input_value()=='log1p1000';result['hku_raw_only']=True
    for lang in ['es','en']:
        if p.locator('html').get_attribute('lang')!=lang:p.locator('#spanish' if lang=='es' else '#language').click()
        assert p.locator('.heroVisual img').evaluate('(e)=>e.complete && e.naturalWidth===1536')
        phrase='Reducción visual' if lang=='es' else 'Visual reduction'
        assert phrase in p.locator('#sparkLODNotice').inner_text()
        assert phrase in p.locator('#spaghettiLODNotice').inner_text()
        for width,height in [(1440,900),(390,844),(360,800)]:
            p.set_viewport_size({'width':width,'height':height});p.evaluate('window.scrollTo(0,0)');p.wait_for_timeout(80)
            assert p.evaluate('document.documentElement.scrollWidth<=innerWidth');box=p.locator('#map').bounding_box();assert 0<=box['y']<height;result[f'map_box_{width}_{lang}']=box
            p.screenshot(path=str(e/'screenshots'/f'final_hero_mapscale_{width}_{lang}.png'),full_page=True)
    result['bilingual_hero_and_notices']=True;b.close()
(e/'raw_scope_ui_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
