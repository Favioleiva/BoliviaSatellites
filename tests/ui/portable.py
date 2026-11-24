"""Test local release hashes, archives and isolated offline-browser exploration."""
from pathlib import Path
import json,hashlib,zipfile,subprocess,sys,time,urllib.request
from playwright.sync_api import sync_playwright
repo=Path(__file__).resolve().parents[2];out=repo.parent.parent;pack=repo.parent/'Packages';work=out/'Evidence/revision_02/portable_final_smoke';work.mkdir(parents=True,exist_ok=False)
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    return h.hexdigest()
manifest=json.loads((pack/'download_manifest.json').read_text());portable=json.loads((pack/'portable_manifest.json').read_text());checked=[]
for row in manifest['files']+portable['parts']:
    p=pack/row['name'];assert p.stat().st_size==row['bytes'];assert sha(p)==row['sha256']
    with zipfile.ZipFile(p) as z:
        assert z.testzip() is None
        if row in portable['parts']:
            for n in z.namelist():assert (work/n).resolve().is_relative_to(work.resolve())
            z.extractall(work)
    checked.append(row['name'])
for row in manifest['files']:assert sha(work/'packages'/row['name'])==row['sha256']
server=subprocess.Popen([sys.executable,'-B',str(work/'code/scripts/serve_local.py'),'--root',str(work/'site'),'--packages',str(work/'packages'),'--port','8769'],stdout=subprocess.DEVNULL)
result={'archives_crc_hash_size':'PASS','checked':checked,'external_requests':[],'products':[]}
try:
    for attempt in range(40):
        try:
            urllib.request.urlopen('http://127.0.0.1:8769/',timeout=1).close();break
        except OSError:time.sleep(.1)
    for row in manifest['files']:
        req=urllib.request.Request('http://127.0.0.1:8769/'+row['url'],method='HEAD')
        with urllib.request.urlopen(req) as response:assert int(response.headers['Content-Length'])==row['bytes']
    with sync_playwright() as pw:
        b=pw.chromium.launch(headless=True);ctx=b.new_context();p=ctx.new_page()
        def route(r):
            if not r.request.url.startswith(('http://127.0.0.1:8769/','file:')):
                result['external_requests'].append(r.request.url);r.abort()
            else:r.continue_()
        ctx.route('**/*',route);p.goto((work/'ABRIR_BOLIVIA_SATELLITES.html').as_uri()+'?lang=en');p.wait_for_function('window.__ready');assert p.locator('html').get_attribute('lang')=='en';p.wait_for_function('document.querySelectorAll("#downloadList a").length>=11');assert p.locator('.municipal').count()==339;result['file_entry_English_339']='PASS';assert p.locator('#rankingList button').count()==10;assert p.evaluate('BoliviaSatellites.state.requested')=='2025-11';result['top10_fixed_2025']='PASS'
        import urllib.parse
        for url in p.locator('#downloadList a').evaluate_all('(es)=>es.map(e=>e.href)'):assert Path(urllib.request.url2pathname(urllib.parse.urlparse(url).path)).is_file()
        result['file_download_links']='PASS'
        for pid in ['era5','gpm','hku','fire','vegetation','pm25','blackmarble']:
            p.evaluate('async id=>await BoliviaSatellites.product(id,{explore:true})',pid);p.evaluate('async()=>await BoliviaSatellites.selectGeo(254)');p.evaluate('async()=>await BoliviaSatellites.comparison()');assert p.locator('.municipal').count()==339;result['products'].append(pid)
        p.goto('http://127.0.0.1:8769/');p.wait_for_function('window.__ready');assert p.locator('.municipal').count()==339;result['http_entry_339']='PASS'
        b.close()
    assert not result['external_requests'];result['status']='PASS'
finally:server.terminate();server.wait(timeout=10)
(out/'Evidence/revision_02/portable_validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
