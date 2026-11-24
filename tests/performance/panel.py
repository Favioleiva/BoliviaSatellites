"""Capture the first opening RAF before any cached re-selection overwrites it."""
from pathlib import Path
import json,time
from playwright.sync_api import sync_playwright
repo=Path(__file__).resolve().parents[2];e=repo.parent.parent/'Evidence/benchmarks';rows=[]
with sync_playwright() as pw:
    for profile,w,h,speed,latency,cpu in [('desktop',1440,900,1250000,100,1),('mobile',390,844,500000,150,4)]:
        b=pw.chromium.launch(headless=True);p=b.new_page(viewport={'width':w,'height':h});cdp=p.context.new_cdp_session(p);cdp.send('Network.enable');cdp.send('Network.emulateNetworkConditions',{'offline':False,'latency':latency,'downloadThroughput':speed,'uploadThroughput':speed});cdp.send('Emulation.setCPUThrottlingRate',{'rate':cpu})
        for mode in ['cold','warm']:
            for run in range(20):
                cdp.send('Network.setCacheDisabled',{'cacheDisabled':mode=='cold'})
                if mode=='cold':cdp.send('Network.clearBrowserCache')
                p.goto('http://127.0.0.1:8768/?product=blackmarble&source=1');p.wait_for_function('window.__ready');p.locator('#municipality').select_option('254');p.wait_for_function('window.__detailReady && window.__panelVisibleMs!==undefined');rows.append({'profile':profile,'mode':mode,'run':run,'first_panel_visible_ms':p.evaluate('window.__panelVisibleMs')})
        b.close()
(e/'first_panel.json').write_text(json.dumps(rows,indent=2));print('FIRST_PANEL_TRIALS',len(rows),max(x['first_panel_visible_ms'] for x in rows))
