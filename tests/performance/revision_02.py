"""Current-build smoke measurements; does not replace the contract's full benchmark."""
from pathlib import Path
import json,subprocess,sys,time,urllib.request
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[2];E=R.parent.parent/'Evidence/revision_02';rows=[]
server=subprocess.Popen([sys.executable,'-B',str(R/'scripts/serve_local.py'),'--root',str(R/'dist'),'--port','8768'],stdout=subprocess.DEVNULL)
try:
    for n in range(50):
        try:urllib.request.urlopen('http://127.0.0.1:8768/',timeout=1).close();break
        except OSError:time.sleep(.1)
    subprocess.run([sys.executable,'-B',str(R/'tests/ui/check.py')],check=True)
    subprocess.run([sys.executable,'-B',str(R/'tests/ui/raw_scope.py')],check=True)
    with sync_playwright() as pw:
        b=pw.chromium.launch()
        for profile,w,h,mbps,latency,cpu in [('desktop',1440,1000,10,100,1),('mobile',390,844,4,150,4)]:
            for protocol in ['http','file']:
                for trial in range(3):
                    ctx=b.new_context(viewport={'width':w,'height':h});p=ctx.new_page();cdp=ctx.new_cdp_session(p);cdp.send('Network.enable');cdp.send('Network.setCacheDisabled',{'cacheDisabled':True});cdp.send('Emulation.setCPUThrottlingRate',{'rate':cpu})
                    if protocol=='http':cdp.send('Network.emulateNetworkConditions',{'offline':False,'latency':latency,'downloadThroughput':mbps*1e6/8,'uploadThroughput':mbps*1e6/8})
                    url='http://127.0.0.1:8768/' if protocol=='http' else (R/'dist/index.html').as_uri()
                    p.goto(url+'?product=blackmarble&lang=en');p.wait_for_function('window.__ready');p.wait_for_function('document.querySelector(".heroVisual img").complete && document.querySelectorAll("#downloadList a").length>=11')
                    initial=p.evaluate('({ready:window.__ready,bytes:performance.getEntriesByType("resource").reduce((a,e)=>a+e.transferSize,0)+performance.getEntriesByType("navigation")[0].transferSize,loaded:performance.now()})')
                    spark=p.evaluate('async()=>{let t=performance.now();await BoliviaSatellites.selectGeo(254);return performance.now()-t}')
                    spaghetti=p.evaluate('async()=>{let t=performance.now();await BoliviaSatellites.comparison();return performance.now()-t}')
                    row={'profile':profile,'protocol':protocol,'trial':trial,'initial_ms':initial['ready'],'hero_and_manifest_ms':initial['loaded'],'http_transferred_bytes':initial['bytes'] if protocol=='http' else None,'spark_ms':spark,'spaghetti_ms':spaghetti,'main_heap':cdp.send('Runtime.getHeapUsage'),'cache':p.evaluate('BoliviaSatellites.diagnostics')}
                    row['smoke_budget_pass']=initial['ready']<(4000 if profile=='desktop' else 6000) and spark<(1500 if profile=='desktop' else 2000) and spaghetti<(3000 if profile=='desktop' else 5000)
                    if protocol=='http':row['smoke_budget_pass'] &= initial['bytes']<(2 if profile=='desktop' else 1.5)*2**20
                    rows.append(row);ctx.close()
        b.close()
finally:server.terminate();server.wait(timeout=10)
result={'dist_budget_status':'PASS' if sum(p.stat().st_size for p in (R/'dist').rglob('*') if p.is_file())<=250*2**20 else 'FAIL','status':'PASS' if all(x['smoke_budget_pass'] for x in rows) else 'FAIL','trials':rows,'limits':'3 cold trials per profile and access mode; no final p95 certification; main heap is not renderer RSS or Worker/GPU memory','dist_bytes':sum(p.stat().st_size for p in (R/'dist').rglob('*') if p.is_file()),'dist_files':sum(1 for p in (R/'dist').rglob('*') if p.is_file())}
(E/'performance_smoke.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({'status':result['status'],'trials':len(rows),'max_initial_ms':max(x['initial_ms'] for x in rows),'max_http_bytes':max(x['http_transferred_bytes'] or 0 for x in rows)}));assert result['status']=='PASS'
