"""Worker attribution, mixed-product retained memory and interaction long tasks."""
from pathlib import Path
import json,time
from playwright.sync_api import sync_playwright
repo=Path(__file__).resolve().parents[2];out=repo.parent.parent/'Evidence/benchmarks';reports={}
with sync_playwright() as pw:
    for profile,width,height,cpu in [('desktop',1440,900,1),('mobile',390,844,4)]:
        b=pw.chromium.launch(headless=True,args=['--enable-precise-memory-info']);p=b.new_page(viewport={'width':width,'height':height});cdp=p.context.new_cdp_session(p);cdp.send('Emulation.setCPUThrottlingRate',{'rate':cpu})
        p.add_init_script("window.longTasks=[];new PerformanceObserver(l=>{for(let e of l.getEntries())longTasks.push({start:e.startTime,duration:e.duration})}).observe({type:'longtask',buffered:true})")
        p.goto('http://127.0.0.1:8768/?product=blackmarble&source=1&geo=254');p.wait_for_function('window.__ready');p.evaluate('async()=>await BoliviaSatellites.comparison()')
        start=p.evaluate('performance.now()');measurements=[]
        for i in range(20):
            row=p.evaluate("""async i=>{let t=performance.now();await BoliviaSatellites.selectGeo(i%3);let selection=performance.now()-t;t=performance.now();await BoliviaSatellites.setDate(i%2?'2025-11-09':'2025-11-10');let date=performance.now()-t;let r=document.getElementById('spaghetti').getBoundingClientRect();t=performance.now();document.getElementById('spaghetti').dispatchEvent(new PointerEvent('pointermove',{clientX:r.x+150,clientY:r.y+70}));return {selection_ms:selection,date_ms:date,hover_ms:performance.now()-t}}""",i);measurements.append(row)
        p.locator('#group').select_option(label='Chuquisaca / Oropeza');t=time.perf_counter();p.wait_for_function("BoliviaSatellites.state.group.endsWith('Oropeza')");p.wait_for_timeout(300);adhoc_upper_ms=(time.perf_counter()-t)*1000
        p.locator('#group').select_option('national');p.wait_for_timeout(150)
        while not p.locator('#moreLines').is_disabled():p.locator('#moreLines').click();p.wait_for_timeout(80)
        assert p.evaluate('BoliviaSatellites.diagnostics.lines')==339
        browser_cdp=b.new_browser_cdp_session();worker_heap={'status':'NOT_MEASURED'}
        try:
            target=next(x for x in browser_cdp.send('Target.getTargets')['targetInfos'] if x['type']=='worker' and x['url'].endswith('/worker.js'))
            sid=browser_cdp.send('Target.attachToTarget',{'targetId':target['targetId'],'flatten':False})['sessionId'];messages=[];browser_cdp.on('Target.receivedMessageFromTarget',lambda x:messages.append(x));browser_cdp.send('Target.sendMessageToTarget',{'sessionId':sid,'message':json.dumps({'id':1,'method':'Runtime.getHeapUsage'})})
            for _ in range(20):
                p.wait_for_timeout(50)
                matches=[json.loads(m['message']) for m in messages if m['sessionId']==sid and json.loads(m['message']).get('id')==1]
                if matches:worker_heap=matches[0];break
            browser_cdp.send('Target.detachFromTarget',{'sessionId':sid})
        except Exception as exc:worker_heap={'status':'NOT_MEASURED','reason':str(exc)[:300]}
        full_main=cdp.send('Runtime.getHeapUsage');tasks=p.evaluate('(t)=>longTasks.filter(x=>x.start>=t)',start)
        # Same prewarmed pool and same final state on each side of the memory comparison.
        async_loop="""async n=>{let products=['era5','gpm','hku','fire','vegetation','pm25','blackmarble'];for(let i=0;i<n;i++){await BoliviaSatellites.product(products[i%7],{explore:true});await BoliviaSatellites.selectGeo(i%7)}await BoliviaSatellites.product('era5');await BoliviaSatellites.selectGeo(0)}"""
        p.evaluate(async_loop,50);cdp.send('HeapProfiler.collectGarbage');baseline=cdp.send('Runtime.getHeapUsage');p.evaluate(async_loop,50);cdp.send('HeapProfiler.collectGarbage');final=cdp.send('Runtime.getHeapUsage')
        reports[profile]={'interaction_trials':measurements,'all_339_accessible':True,'worker_heap_at_339':worker_heap,'main_heap_at_339':full_main,'interaction_longtasks':tasks,'max_longtask_ms':max([x['duration'] for x in tasks],default=0),'mixed_product_cycles':50,'prewarmed_baseline':baseline,'retained_final':final,'retained_heap_growth':final['usedSize']/baseline['usedSize']-1,'ad_hoc_note':'Province selection exercised; completion instrumentation remains separate from selector latency.','gpu_memory':'NOT_MEASURED','limits':'Worker heap is a single peak-candidate state, not a continuous per-frame peak trace.'}
        b.close()
(out/'advanced_metrics.json').write_text(json.dumps(reports,indent=2),encoding='utf-8');print(json.dumps(reports,indent=2))
