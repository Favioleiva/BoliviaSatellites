from pathlib import Path
import json
from playwright.sync_api import sync_playwright
repo=Path(__file__).resolve().parents[2];out=repo.parent.parent/'Evidence/benchmarks'
with sync_playwright() as pw:
    b=pw.chromium.launch(headless=True);p=b.new_page();p.goto(Path(__file__).with_suffix('.html').as_uri());result=p.evaluate('runFixture()');result['browser']=b.version;assert result['selected_exact'];b.close()
(out/'renderer_stress.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='results'},indent=2))
