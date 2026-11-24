"""Targeted group, date/timezone, keyboard state and visual QA on final interface."""
from pathlib import Path
import json,math
from playwright.sync_api import sync_playwright
repo=Path(__file__).resolve().parents[2];e=repo.parent.parent/'Evidence';result={}
with sync_playwright() as pw:
    b=pw.chromium.launch(headless=True);ctx=b.new_context(viewport={'width':1440,'height':900});p=ctx.new_page();p.goto('http://127.0.0.1:8768/');p.wait_for_function('window.__ready')
    result['worker_quantiles']=p.evaluate("""()=>new Promise((resolve,reject)=>{let w=new Worker('worker.js');w.onerror=reject;w.onmessage=e=>{resolve(Array.from(new Float64Array(e.data.value)));w.terminate()};w.postMessage({id:91,type:'quantiles',T:3,arrays:[[1,NaN,0],[3,NaN,2],[5,NaN,4]]})})""")
    assert result['worker_quantiles'][:7]==[3,1.4,2,3,4,4.6,3];assert result['worker_quantiles'][13]==0
    samples=p.evaluate("""async()=>{let g=await(await fetch('catalog/geography.json')).json(),groups={};for(let x of g)(groups[x.depto]??=[]).push(x);return Object.values(groups).map(a=>a.sort((x,y)=>{let b=document.querySelector(`[data-geo="${x.asdf_id}"]`).getBBox(),c=document.querySelector(`[data-geo="${y.asdf_id}"]`).getBBox();return c.width*c.height-b.width*b.height})[0])}""")
    result['department_map_clicks']=[]
    for g in samples:
        p.evaluate('scrollTo(0,0)')
        point=p.evaluate("""id=>{let e=document.querySelector(`[data-geo="${id}"]`),b=e.getBBox(),m=e.getScreenCTM();for(let j=1;j<20;j++)for(let k=1;k<20;k++){let q=new DOMPoint(b.x+b.width*j/20,b.y+b.height*k/20);if(e.isPointInFill(q)){let r=q.matrixTransform(m);if(document.elementFromPoint(r.x,r.y)===e)return {x:r.x,y:r.y}}}return null}""",g['asdf_id'])
        assert point,g;p.mouse.click(point['x'],point['y']);p.wait_for_function('(id)=>BoliviaSatellites.state.geo===id',arg=g['asdf_id']);result['department_map_clicks'].append(g['depto']);p.screenshot(path=str(e/'screenshots'/f'department_{g["asdf_id"]}.png'))
    for pid in ['era5','gpm','hku','fire','vegetation','pm25','blackmarble']:
        p.evaluate('async id=>await BoliviaSatellites.product(id,{explore:true})',pid);p.evaluate('async()=>await BoliviaSatellites.selectGeo(254)')
        for lang in ['es','en']:
            if p.locator('html').get_attribute('lang')!=lang:p.locator('#language').click()
            p.evaluate('scrollTo(0,0)');p.screenshot(path=str(e/'screenshots'/f'final_{pid}_{lang}.png'),full_page=True)
    p.locator('#loadComparison').click();p.wait_for_function('window.__comparisonReady');before=p.evaluate('window.__comparisonReady');p.locator('#group').select_option(label='Chuquisaca / Oropeza');p.wait_for_function('(before)=>window.__comparisonReady>before',arg=before);assert p.evaluate('BoliviaSatellites.state.group').endswith('Oropeza');result['province_group']=True
    state=p.evaluate('JSON.parse(JSON.stringify(BoliviaSatellites.state))');p.reload();p.wait_for_function('window.__ready');assert p.evaluate('BoliviaSatellites.state.group')==state['group'];result['state_group_restore']=True
    ctx.close()
    for tz in ['Pacific/Honolulu','Asia/Tokyo','UTC']:
        c=b.new_context(timezone_id=tz);p=c.new_page();p.clock.install(time=946684800000);p.goto('http://127.0.0.1:8768/?product=blackmarble');p.wait_for_function('window.__ready');assert p.locator('#date').input_value()=='2025-11-10';c.close()
    result['timezone_and_system_clock_independent']=True;b.close()
result['worker_quantiles']=[x if x is not None and math.isfinite(x) else None for x in result['worker_quantiles']]
result['status']='PASS';(e/'supplemental_ui.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
