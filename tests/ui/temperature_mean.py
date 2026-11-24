"""Regression: fixed whole-history pool reference; original Celsius preserved."""
from pathlib import Path
import csv
import json
import math
import pyarrow.parquet as pq
from playwright.sync_api import sync_playwright

R = Path(__file__).resolve().parents[2]
E = R.parent.parent / 'Evidence/revision_07_map_space_centres/regression_temperature'
E.mkdir(parents=True, exist_ok=True)
result = {'checks': [], 'errors': [], 'references': []}

def check(name, condition):
    assert condition, name
    result['checks'].append(name)

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce', accept_downloads=True)
    page.on('pageerror', lambda e: result['errors'].append(str(e)))
    page.goto((R / 'dist/index.html').as_uri() + '?product=era5&mapscale=log1p1000')
    page.wait_for_function('window.__ready')
    check('339 original municipal polygons', page.locator('.municipal').count() == 339)
    check('temperature log URL normalized to linear', page.locator('#mapTransform').input_value() == 'linear')
    catalog = json.loads((R / 'public/catalog/era5.json').read_text(encoding='utf-8'))
    source = pq.read_table(sorted((R.parent / 'ScientificData/master/era5/base').glob('*.parquet'))).to_pandas()
    for variable in catalog['variables']:
        page.evaluate('async id=>await BoliviaSatellites.variable(id)', variable['id'])
        baseline_ref = None
        for date in ['1990-01', '2025-11', '2025-01', '2026-05']:
            page.evaluate('async date=>await BoliviaSatellites.setDate(date)', date)
            ref = page.evaluate('BoliviaSatellites.colourReference()')
            check(variable['id'] + date + ' linear controls', page.evaluate('[...document.querySelectorAll("#mapTransform option")].every(o=>o.value==="linear"||o.disabled)'))
            if page.evaluate('BoliviaSatellites.paletteKey()') != 'temperature':
                check(variable['id'] + date + ' dispersion unchanged', ref is not None)
                continue
            values = source.loc[(source.qa_flags.astype(int) & 8) == 0, variable['native']].dropna()
            expected = math.fsum(values) / len(values)
            check(variable['id'] + date + ' pooled statistics match master', abs(ref['mean'] - expected) < 1e-12 and ref['count'] == len(values) and ref['low'] == float(values.min()) and ref['high'] == float(values.max()))
            if baseline_ref is None: baseline_ref = ref
            check(variable['id'] + date + ' fixed across dates', ref == baseline_ref)
            colours = page.evaluate('''()=>{let a=BoliviaSatellites,r=a.colourReference();return [a.color(r.mean),a.color(r.low),a.color(r.high),a.color((r.low+r.mean)/2),a.color((r.high+r.mean)/2)]}''')
            check(variable['id'] + date + ' mean yellow and correct halves', colours == ['rgb(255,243,161)', 'rgb(36,70,168)', 'rgb(184,36,53)', 'rgb(85,169,223)', 'rgb(245,154,82)'])
            result['references'].append(ref)
    primary = catalog['variables'][0]['id']
    native = catalog['variables'][0]['native']
    page.evaluate('async id=>await BoliviaSatellites.variable(id)', primary)
    page.evaluate('async()=>await BoliviaSatellites.setDate("2025-11")')
    page.evaluate('async()=>await BoliviaSatellites.selectGeo(254)')
    check('Spanish mean label', 'Centro:' in page.locator('#legendMid').inner_text())
    check('Spanish unweighted note', 'igual peso' in page.locator('#temperatureMeanNote').inner_text())
    axes = page.evaluate('window.__chartScales.spark')
    padding = (axes['sourceMax'] - axes['sourceMin']) * .07 or 1
    check('sparkline original linear Celsius', abs(axes['min'] - (axes['sourceMin'] - padding)) < 1e-12 and abs(axes['max'] - (axes['sourceMax'] + padding)) < 1e-12)
    page.locator('#mapWorkspace').scroll_into_view_if_needed()
    page.screenshot(path=str(E / 'temperature_mean_es.png'))
    page.locator('#language').click()
    check('English mean label and note', 'Centre:' in page.locator('#legendMid').inner_text() and 'equal weight' in page.locator('#temperatureMeanNote').inner_text())
    page.locator('#mapWorkspace').scroll_into_view_if_needed()
    page.screenshot(path=str(E / 'temperature_mean_en.png'))
    with page.expect_download() as download:
        page.locator('#downloadSeries').click()
    target = E / 'temperature_original.csv'
    download.value.save_as(target)
    rows = list(csv.DictReader(target.open(encoding='utf-8')))
    expected = source.loc[(source.geo_id == 254) & (source.period_id == '2025-11'), native].iloc[0]
    check('CSV raw Celsius exact to master', float(next(r['value'] for r in rows if r['period'] == '2025-11')) == expected)
    fixed = page.evaluate('BoliviaSatellites.colourReference()')
    page.evaluate('async()=>await BoliviaSatellites.selectGeo(0)')
    page.evaluate('()=>{BoliviaSatellites.state.group="1";BoliviaSatellites.state.start=50;BoliviaSatellites.state.end=60}')
    page.evaluate('async()=>await BoliviaSatellites.setDate("1900-01")')
    check('fixed despite missing date, selection, group and window', page.evaluate('BoliviaSatellites.colourReference()') == fixed)
    check('missing polygons unchanged', page.locator('#coverage').inner_text() == '0 / 339')
    for product in ['hku', 'blackmarble']:
        page.evaluate('async id=>await BoliviaSatellites.product(id)', product)
        check(product + ' unchanged logarithmic scale', page.locator('#mapTransform').input_value() == 'log1p1000' and page.evaluate("BoliviaSatellites.colourReference().transform==='log1p1000'"))
        check(product + ' scale definition visible', page.locator('#temperatureMeanNote').is_visible())
    page.evaluate('async()=>await BoliviaSatellites.product("era5")')
    page.set_viewport_size({'width': 390, 'height': 844})
    page.locator('#legendMid').scroll_into_view_if_needed()
    page.screenshot(path=str(E / 'temperature_mean_mobile.png'))
    check('mobile no horizontal overflow', page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
    check('no JavaScript errors', not result['errors'])
    browser.close()
result['status'] = 'PASS'
(E / 'validation.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({'status': 'PASS', 'checks': len(result['checks']), 'references': len(result['references'])}))
