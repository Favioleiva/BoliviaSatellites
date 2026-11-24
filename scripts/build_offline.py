"""Generate selective file:// capsules, without altering original gzip/data values."""
from pathlib import Path
import base64,json,hashlib,time
repo=Path(__file__).resolve().parents[1];public=repo/'public';offline=repo/'Offline';start=time.perf_counter();records=[]
report=repo/'.local/offline_integrity.json'
previous={x['key']:x for x in json.loads(report.read_text())['files']} if report.exists() else {}
paths=sorted((public/'data').rglob('*.gz'))+sorted((public/'catalog').glob('*.json'))+[public/'geo/bolivia339.geojson.gz',public/'downloads/download_manifest.json']
for source in paths:
    key=source.relative_to(public).as_posix();raw=source.read_bytes()
    original_sha=hashlib.sha256(raw).hexdigest();target=offline/(key+'.js');old=previous.get(key)
    if old and old['original_sha256']==original_sha and target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest()==old['capsule_sha256']:
        records.append(old);continue
    payload={'kind':'gzip','data':base64.b64encode(raw).decode('ascii')} if source.suffix=='.gz' else {'kind':'json','data':json.loads(raw)}
    target=offline/(key+'.js');target.parent.mkdir(parents=True,exist_ok=True)
    content='window.BoliviaSatellitesData.receive('+json.dumps(key)+','+json.dumps(payload,ensure_ascii=False,separators=(',',':'))+');\n';target.write_text(content,encoding='utf-8')
    # Verify encoded content, not just the original binary input.
    decoded=json.loads(content.split(',',1)[1][:-3]);restored=base64.b64decode(decoded['data']) if decoded['kind']=='gzip' else decoded['data']
    assert restored==raw if decoded['kind']=='gzip' else restored==json.loads(raw)
    records.append({'key':key,'original_sha256':hashlib.sha256(raw).hexdigest(),'capsule_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'bytes':target.stat().st_size})
worker=(repo/'src/worker.js').read_text(encoding='utf-8');(repo/'src/worker-source.js').write_text('window.C05_WORKER_SOURCE='+json.dumps(worker,ensure_ascii=False)+';\n',encoding='utf-8')
report.parent.mkdir(parents=True,exist_ok=True);report.write_text(json.dumps({'status':'PASS','files':records,'total_bytes':sum(x['bytes'] for x in records),'seconds':time.perf_counter()-start,'distribution':'Offline companion only; never included in Netlify dist'},indent=2),encoding='utf-8')
print('OFFLINE_EXACT_CAPSULES',len(records),sum(x['bytes'] for x in records),round(time.perf_counter()-start,2))
