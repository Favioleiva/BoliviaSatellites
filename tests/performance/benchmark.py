"""20 cold + 20 warm browser traversals per profile, on local immutable web data."""
from pathlib import Path
import json,time,statistics,psutil,os
from playwright.sync_api import sync_playwright
REPO=Path(__file__).resolve().parents[2];OUT=REPO.parent.parent;E=OUT/'Evidence/benchmarks';E.mkdir(parents=True,exist_ok=True)
def percentile(a,p=.95):
    a=sorted(a);x=(len(a)-1)*p;i=int(x);return a[i]+(a[min(i+1,len(a)-1)]-a[i])*(x-i)
def renderer_memory():
    total=0
    for p in psutil.process_iter(['name','cmdline','memory_info']):
        try:
            cmd=p.info['cmdline'] or []
            if p.info['name'] in ['chrome.exe','headless_shell.exe','chrome-headless-shell.exe'] and '--type=renderer' in cmd and any('playwright' in x.lower() for x in cmd):total+=p.info['memory_info'].rss
        except (psutil.NoSuchProcess,psutil.AccessDenied):pass
    return total
def main():
    records=[];failures=[]
    profiles=[('desktop',1440,900,10_000_000/8,100,1),('mobile',390,844,4_000_000/8,150,4)]
    with sync_playwright() as pw:
        for profile,w,h,speed,latency,cpu in profiles:
            b=pw.chromium.launch(headless=True,args=['--enable-precise-memory-info']);ctx=b.new_context(viewport={'width':w,'height':h});page=ctx.new_page();cdp=ctx.new_cdp_session(page);cdp.send('Network.enable');cdp.send('Performance.enable');cdp.send('Network.emulateNetworkConditions',{'offline':False,'latency':latency,'downloadThroughput':speed,'uploadThroughput':speed});cdp.send('Emulation.setCPUThrottlingRate',{'rate':cpu});network=[];cdp.on('Network.loadingFinished',lambda ev:network.append(ev['encodedDataLength']))
            for mode in ['cold','warm']:
                for run in range(20):
                    if mode=='cold':cdp.send('Network.clearBrowserCache');cdp.send('Network.setCacheDisabled',{'cacheDisabled':True})
                    else:cdp.send('Network.setCacheDisabled',{'cacheDisabled':False})
                    network.clear();start=time.perf_counter();page.goto('http://127.0.0.1:8768/?product=blackmarble&source=1&lang=es',wait_until='domcontentloaded');page.wait_for_function('window.__ready',timeout=60000);initial_ms=(time.perf_counter()-start)*1000;initial_bytes=sum(network);n=len(network)
                    start=time.perf_counter();page.locator('#municipality').select_option('254');visible=page.locator('#municipalDetail').is_visible();panel_ms=(time.perf_counter()-start)*1000;page.wait_for_function('window.__detailReady');spark_ms=(time.perf_counter()-start)*1000;spark_bytes=sum(network[n:]);n=len(network)
                    start=time.perf_counter();page.locator('#loadComparison').click();page.wait_for_function('window.__comparisonReady');spaghetti_ms=(time.perf_counter()-start)*1000;spaghetti_bytes=sum(network[n:])
                    start=time.perf_counter();page.evaluate("async()=>await BoliviaSatellites.setDate('2025-11-09')");date_cold=(time.perf_counter()-start)*1000;start=time.perf_counter();page.evaluate("async()=>await BoliviaSatellites.setDate('2025-11-10')");date_warm=(time.perf_counter()-start)*1000
                    start=time.perf_counter();page.evaluate('async()=>await BoliviaSatellites.selectGeo(254)');panel_warm=(time.perf_counter()-start)*1000
                    metrics=cdp.send('Runtime.getHeapUsage');cache=page.evaluate('BoliviaSatellites.diagnostics.cacheBytes');memory=renderer_memory()
                    # Real 10s interaction trace, animation frames and canvas redraw.
                    frames=page.evaluate("""async()=>{let times=[],last=performance.now(),start=last;while(performance.now()-start<10000){await new Promise(requestAnimationFrame);let now=performance.now();times.push(now-last);last=now;document.getElementById('spaghetti').dispatchEvent(new PointerEvent('pointermove',{clientX:100+times.length%300,clientY:100}));if(times.length%30===0){document.getElementById(times.length%60?'zoomIn':'zoomOut').click()}}return times}""")
                    row=dict(profile=profile,mode=mode,run=run,initial_ms=initial_ms,initial_bytes=initial_bytes,panel_visible_ms=page.evaluate('window.__panelVisibleMs'),automation_panel_action_ms=panel_ms,panel_visible=visible,spark_ms=spark_ms,spark_bytes=spark_bytes,spaghetti_ms=spaghetti_ms,spaghetti_bytes=spaghetti_bytes,date_network_ms=date_cold,date_cached_ms=date_warm,panel_cached_ms=panel_warm,heap_used=metrics['usedSize'],backing_storage=metrics.get('backingStorageSize'),cache_bytes=cache,renderer_rss=memory,frame_p95=percentile(frames),frame_max=max(frames),frame_count=len(frames),browser=b.version);records.append(row)
                    (E/'performance_raw.json').write_text(json.dumps(records,indent=2),encoding='utf-8');print(profile,mode,run,round(initial_ms),round(spark_ms),round(spaghetti_ms),flush=True)
            # Retained memory after repeated use of the same prewarmed set.
            for _ in range(2):
                for i in range(50):page.evaluate('async id=>await BoliviaSatellites.selectGeo(id)',i)
                cdp.send('HeapProfiler.collectGarbage');time.sleep(.2)
                if _==0:baseline=cdp.send('Runtime.getHeapUsage')['usedSize']
            final=cdp.send('Runtime.getHeapUsage')['usedSize'];(E/f'memory_cycles_{profile}.json').write_text(json.dumps({'baseline':baseline,'final':final,'growth_ratio':final/baseline-1,'cycles':50,'prewarmed_pool':50}),encoding='utf-8');ctx.close();b.close()
    summary={}
    for profile,*_ in profiles:
        rows=[x for x in records if x['profile']==profile];summary[profile]={}
        for key in ['initial_ms','initial_bytes','panel_visible_ms','spark_ms','spark_bytes','spaghetti_ms','spaghetti_bytes','date_network_ms','date_cached_ms','panel_cached_ms','heap_used','renderer_rss','frame_p95']:
            vals=[x[key] for x in rows];summary[profile][key]={'median':statistics.median(vals),'p95':percentile(vals),'worst':max(vals)}
    summary['limitations']=['Worker JS heap is not separately exposed by Runtime.getHeapUsage; renderer RSS includes worker backing allocations.','Renderer RSS scan may include unrelated Playwright renderers; process attribution must be reviewed.','DuckDB-Wasm acquisition failed with sandbox EACCES; no runtime comparison or architecture freeze claimed.','Mobile CPU throttle is emulation, not a physical handset.']
    (E/'performance_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
