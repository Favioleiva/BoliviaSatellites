"""Independent historical log-centre audit plus map-whitespace collision checks."""
from pathlib import Path
import json
import math
import numpy as np
import pyarrow.parquet as pq
from playwright.sync_api import sync_playwright

R=Path(__file__).resolve().parents[2]
E=R.parent.parent/'Evidence/revision_08_wide_rankings/regression_centres'
E.mkdir(parents=True,exist_ok=True)
result={'checks':[],'errors':[],'centres':[]}
def check(name,condition):
    assert condition,name
    result['checks'].append(name)
def close(a,b):return math.isclose(float(a),float(b),rel_tol=2e-12,abs_tol=2e-12)
collision_js='''()=>{
 const paths=[...document.querySelectorAll('.municipal')].map(e=>({e,b:e.getBBox()})),inv=document.getElementById('polygons').getScreenCTM().inverse();
 for(const box of document.querySelectorAll('.context-grid>div')){
  const r=box.getBoundingClientRect();
  for(let y=r.top;y<=r.bottom;y+=3)for(let x=r.left;x<=r.right;x+=3){
   const q=new DOMPoint(x,y).matrixTransform(inv);
   for(const {e,b} of paths)if(q.x>=b.x&&q.x<=b.x+b.width&&q.y>=b.y&&q.y<=b.y+b.height&&e.isPointInFill(q)){
    const svg=document.getElementById('map').getBoundingClientRect();
    if(x>=svg.left&&x<=svg.right&&y>=svg.top&&y<=svg.bottom)return {collision:true,id:e.dataset.geo,box:box.className,x,y};
   }
  }
 }
 return {collision:false};
}'''
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True)
    p=browser.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce',accept_downloads=True)
    p.on('pageerror',lambda e:result['errors'].append(str(e)))
    p.goto((R/'dist/index.html').as_uri());p.wait_for_function('window.__ready')
    for pid in ['era5','gpm','hku','fire','vegetation','pm25','blackmarble']:
        card=json.loads((R/'public/catalog'/f'{pid}.json').read_text(encoding='utf-8'))
        stats={v['native']:{k:dict(total=np.longdouble(0),count=0,invalid=0) for k in [0,1,1000]} for v in card['variables']}
        for source in sorted((R.parent/'ScientificData/master'/pid/'base').glob('*.parquet')):
            table=pq.read_table(source,columns=['qa_flags']+list(stats));flags=table['qa_flags'].to_numpy().astype(int)
            for n in stats:
                values=table[n].to_numpy().astype(np.longdouble);values=values[np.isfinite(values)&((flags&8)==0)]
                for k,d in stats[n].items():
                    valid=values if k==0 else values[1+k*values>0]
                    d['invalid']+=len(values)-len(valid);d['count']+=len(values)
                    d['total']+=np.sum(valid if k==0 else np.log1p(k*valid),dtype=np.longdouble)
        p.evaluate('async id=>await BoliviaSatellites.product(id)',pid)
        p.evaluate('async()=>await BoliviaSatellites.selectGeo(254)')
        for var in card['variables']:
            p.evaluate('async id=>await BoliviaSatellites.variable(id)',var['id'])
            raw=p.locator('.context-grid dd').evaluate_all('(es)=>es.map(e=>e.dataset.value)')
            for key,k in [('linear',0),('log1p',1),('log1p1000',1000)]:
                d=stats[var['native']][k];tag=pid+'/'+var['native']+'/'+key
                disabled=d['invalid']>0 or (pid=='era5' and k!=0)
                check(tag+'/domain_guard',p.locator('#mapTransform option[value="'+key+'"]').is_disabled()==disabled)
                if disabled:continue
                p.locator('#mapTransform').select_option(key)
                ref=p.evaluate('BoliviaSatellites.colourReference()');expected=float(d['total']/d['count']);original=expected if not k else math.expm1(expected)/k
                check(tag+'/mean_in_selected_space',close(ref['displayMean'],expected))
                check(tag+'/inverse_to_original_units',close(ref['mean'],original))
                check(tag+'/legend_original_centre',close(p.locator('#legendMid').get_attribute('data-value'),original))
                check(tag+'/midpoint_colour',p.evaluate('()=>BoliviaSatellites.color(BoliviaSatellites.colourReference().mean)===C05_colourAt(BoliviaSatellites.paletteKey(),.5)'))
                check(tag+'/original_context_unchanged',p.locator('.context-grid dd').evaluate_all('(es)=>es.map(e=>e.dataset.value)')==raw)
                result['centres'].append({'product':pid,'variable':var['native'],'transform':key,'original_center':ref['mean'],'display_mean':ref['displayMean'],'count':ref['count']})
        p.evaluate('async id=>await BoliviaSatellites.variable(id)',card['default'])
        ref=p.evaluate('BoliviaSatellites.colourReference()')
        p.evaluate('async()=>await BoliviaSatellites.setDate("1900-01")')
        p.evaluate('async()=>await BoliviaSatellites.selectGeo(0)')
        check(pid+'/centre_fixed_across_dates_and_selection',p.evaluate('BoliviaSatellites.colourReference()')==ref)
    for pid in ['era5','gpm','blackmarble']:
        p.evaluate('async id=>await BoliviaSatellites.product(id)',pid)
        p.evaluate('async()=>await BoliviaSatellites.selectGeo(254)')
        for lang,selector in [('es','#spanish'),('en','#language')]:
            p.locator(selector).click()
            for width,height in [(1440,1000),(1024,900),(390,844)]:
                p.set_viewport_size({'width':width,'height':height});p.wait_for_timeout(80)
                collision=p.evaluate(collision_js)
                check(f'{pid}/{lang}/{width}/no_annotation_land_overlap',not collision['collision'])
                check(f'{pid}/{lang}/{width}/no_overflow',p.evaluate('document.documentElement.scrollWidth<=innerWidth'))
                check(f'{pid}/{lang}/{width}/unboxed',p.locator('.map-context').evaluate('e=>getComputedStyle(e).backgroundColor==="rgba(0, 0, 0, 0)"&&getComputedStyle(e).borderTopWidth==="0px"'))
                if width in [1440,390]:p.locator('.mapcard').screenshot(path=str(E/f'{pid}_{lang}_{width}.png'))
        p.set_viewport_size({'width':1440,'height':1000});p.locator('#zoomIn').click();p.wait_for_timeout(80)
        check(pid+'/zoom_keeps_annotation_space_clear',not p.evaluate(collision_js)['collision'])
        p.locator('#fit').click();p.wait_for_timeout(80)
        check(pid+'/desktop_fluid_workspace',p.locator('#mapWorkspace').bounding_box()['width']>=0.95*1440 and p.locator('#map').bounding_box()['height']>=600)
    check('no_javascript_errors',not result['errors']);browser.close()
result['status']='PASS'
(E/'validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'status':'PASS','checks':len(result['checks']),'valid_centres':len(result['centres'])}))
