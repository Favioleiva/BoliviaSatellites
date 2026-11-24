"""Assemble review evidence; technical PASS never means human acceptance."""
from pathlib import Path
import json,csv,statistics,hashlib,datetime,shutil
repo=Path(__file__).resolve().parents[1];out=repo.parent.parent;e=out/'Evidence';review=repo.parent/'Review'
def read(name):return json.loads((e/name).read_text(encoding='utf-8-sig'))
def write(p,obj):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def percentile(a,p=.95):
    a=sorted(a);x=(len(a)-1)*p;i=int(x);return a[i]+(a[min(i+1,len(a)-1)]-a[i])*(x-i)
integrity=read('audit/integrity_validation.json');csvcheck=read('csv_roundtrip.json');reproduction=read('reproduction/result.json');portable=read('portable_validation.json');raw=read('raw_scope_ui_validation.json');supp=read('supplemental_ui.json');dist=read('distribution_audit.json')
assert csvcheck['status']==reproduction['status']==portable['status']==supp['status']=='PASS'
records=read('benchmarks/performance_raw.json');panel=read('benchmarks/first_panel.json');advanced=read('benchmarks/advanced_metrics.json');renderer=read('benchmarks/renderer_stress.json');assert len(records)==len(panel)==80
criteria=[
('T01','Integridad y alcance','PASS','1.448 fuentes + bases, hashes sin cambios; siete productos, EDGAR excluido.','baseline_manifest.json;hash_diff.json'),
('T02','Claves y conservación','PASS','2.486.565 claves únicas; 339 por período; duplicados equivalentes trazados, checkpoints/espejos cotejados.','audit/integrity_validation.json;reconciliation'),
('T03','Diccionario y método','BLOCKED','326 columnas clasificadas, siete recetas y códigos disponibles; definición mean0 y escala/QA Black Marble siguen sin resolver; procedencia HKU pendiente.','../Deliverables/BoliviaSatellites/data/dictionaries/columns.json;audit/blackmarble_diagnostics.json'),
('T04','Controles numéricos y faltantes','FAIL','Copia exacta y faltantes verificados. Black Marble conserva 34 min>mean a tolerancia 1e-10, máximo 1.298e-9; no se cambia la tolerancia ni el original.','audit;csv_roundtrip.json'),
('T05','Disponibilidad y defectos','BLOCKED','GPM numérico resuelto. Ratios ERA/GPM conservados bajo política autorizada. Fire QA, extremos PM y extracción/escala BM pendientes.','audit/area_comparison.json;audit/fire_base.json'),
('T06','Geografía','PASS','339 geometrías exactas Agriculture; asdf_id, seis discrepancias preservadas y correspondencias verificadas.','audit/geography.json'),
('T07','Referencia inicial','PASS','Ocho pruebas unitarias; siete productos E2E; tres timezone/reloj; noviembre/día 10 exacto o año anterior explícito; huecos sin imputación.','ui_validation.json;supplemental_ui.json'),
('T08','Mapa y panel','PASS','339 selecciones por interfaz, teclado/foco y clics reales en nueve departamentos; panel con historia y QA.','ui_validation.json;supplemental_ui.json;raw_scope_ui_validation.json'),
('T09','Series y reducción visual','PASS','Todos los arrays y LOD verificados; 193 CSV roundtrip; descarga idéntica bajo tres escalas de mapa; avisos ES/EN.','audit/integrity_validation.json;csv_roundtrip.json;raw_scope_ui_validation.json'),
('T10','Spaghetti y bandas','PASS','339 series progresivas; bandas nacionales/departamentales cotejadas independientemente; Worker ad hoc y provincia probados; fallback sin WebGL.','audit/integrity_validation.json;ui_validation.json;supplemental_ui.json;benchmarks/advanced_metrics.json'),
('T11','Estado sincronizado','PASS','Producto/variable/fecha/municipio/grupo/escala en estado y URL; respuestas obsoletas protegidas, datos descargados sin escala de mapa.','ui_validation.json;supplemental_ui.json;raw_scope_ui_validation.json'),
('T12','Diseño, accesibilidad y móvil','BLOCKED','Chromium ES/EN, responsive y teclado comprobados. Falta smoke Firefox/WebKit; no se declara auditoría exhaustiva de accesibilidad.','ui_validation.json;screenshots'),
('T13','Rendimiento','BLOCKED','80 recorridos, panel corregido, Worker/RSS, ciclos y stress medidos; alternativa DuckDB-Wasm y comparación integral de tres arquitecturas no ejecutadas.','benchmarks;distribution_audit.json'),
('T14','Descargas y reproducción','PASS','193 maestros y 12.067 datos web reconstruidos; ZIP/CRC/hash/links/portable offline verificados. Nivel B con bloqueo explícito por producto, sin certificar extractor ausente.','reproduction/result.json;reproduction/csv_determinism.json;portable_validation.json;package_validation.json'),
('T15','Preparación/publicación','BLOCKED','Allowlist y separación de destinos preparadas; arquitectura no congelada, licencias/selección pendientes. Remoto NOT_RUN por falta de autorización.','distribution_audit.json;package_validation.json')]
products=list(integrity);matrix=[]
for code,title,status,reason,evidence in criteria:
    product_status={p:status for p in products}
    if code=='T03':product_status.update({p:'PASS' for p in ['era5','gpm','fire','vegetation','pm25']})
    if code=='T04':product_status.update({p:'PASS' for p in products if p!='blackmarble'})
    if code=='T05':product_status.update({p:'PASS' for p in ['era5','gpm','hku','vegetation']})
    matrix.append(dict(criterion=code,title=title,status=status,products=product_status,reason=reason,evidence=evidence,human_acceptance='PENDING'))
write(e/'validation.json',{'contract':'05','state':'LOCAL_CANDIDATE_WITH_OPEN_CRITERIA','human_acceptance':'PENDING','criteria':matrix,'publication':'NOT_RUN_NOT_AUTHORIZED'})
with (review/'MATRIZ_ACEPTACION.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['criterion','component','status',*products,'reason','evidence','human_acceptance'])
    for x in matrix:w.writerow([x['criterion'],x['title'],x['status'],*[x['products'][p] for p in products],x['reason'],x['evidence'],'PENDING'])
md='# Matriz de aceptación — Contract 05\n\nPASS significa comprobación técnica; no aceptación humana. BLOCKED y FAIL permanecen abiertos. Estado de certificación de origen separado de integridad local.\n\n| Criterio | Componente | Global | '+' | '.join(products)+' |\n|---|---|---|'+'---|'*len(products)+'\n'
for x in matrix:md+='| '+x['criterion']+' | '+x['title']+' | '+x['status']+' | '+' | '.join(x['products'][p] for p in products)+' |\n'
md+='\n## Evidencia y límites\n\n'
for x in matrix:md+=f"**{x['criterion']} — {x['status']}.** {x['reason']} Evidencia relativa a Evidence: `{x['evidence']}`.\n\n"
(review/'MATRIZ_ACEPTACION.md').write_text(md,encoding='utf-8')
budgets=[];perf='# Rendimiento y distribución — candidato local\n\n80 recorridos: 20 fríos +20 calientes por perfil, Black Marble, Chromium 147.0.7727.15. Escritorio 1440×900, 10 Mbps/100 ms; móvil 390×844, 4 Mbps/150 ms, CPU 4×. Duración de interacción por recorrido: 10 s. Emulación, no teléfono real.\n\n| Perfil/cache | Métrica | Mediana | p95 | Peor | Límite p95 | Estado |\n|---|---|---:|---:|---:|---:|---|\n'
limits={'desktop':{'initial_ms':4000,'initial_bytes':2*2**20,'spark_ms':1500,'spark_bytes':256*1024,'spaghetti_ms':3000,'spaghetti_bytes':2*2**20,'date_network_ms':1000,'date_cached_ms':150,'panel_cached_ms':150,'renderer_rss':400*2**20,'frame_p95':33},'mobile':{'initial_ms':6000,'initial_bytes':1.5*2**20,'spark_ms':2000,'spark_bytes':256*1024,'spaghetti_ms':5000,'spaghetti_bytes':2**20,'date_network_ms':1500,'date_cached_ms':150,'panel_cached_ms':150,'renderer_rss':250*2**20,'frame_p95':50}}
for profile in ['desktop','mobile']:
    for mode in ['cold','warm']:
        rows=[x for x in records if x['profile']==profile and x['mode']==mode]
        for key,limit in limits[profile].items():
            vals=[x[key] for x in rows];q=percentile(vals);status='PASS' if q<=limit else 'FAIL';budgets.append(dict(profile=profile,mode=mode,metric=key,p95=q,limit=limit,status=status));perf+=f'| {profile}/{mode} | {key} | {statistics.median(vals):.2f} | {q:.2f} | {max(vals):.2f} | {limit:.0f} | {status} |\n'
        vals=[x['first_panel_visible_ms'] for x in panel if x['profile']==profile and x['mode']==mode];q=percentile(vals);status='PASS' if q<=100 else 'FAIL';budgets.append(dict(profile=profile,mode=mode,metric='first_panel_visible_ms',p95=q,limit=100,status=status));perf+=f'| {profile}/{mode} | first_panel_visible_ms | {statistics.median(vals):.2f} | {q:.2f} | {max(vals):.2f} | 100 | {status} |\n'
perf+='\nLas magnitudes `_bytes`/`rss` son bytes; tiempos en ms. El primer script capturaba la marca del panel después de una reselección cacheada. Para la apertura inicial se usa exclusivamente `first_panel.json`, 80 ensayos corregidos; no la columna homónima del primer archivo.\n\n## Memoria e interacción\n\n'
for profile,a in advanced.items():
    wh=a['worker_heap_at_339'].get('result',{});mh=a['main_heap_at_339'];total=sum(x.get(k,0) for x in [wh,mh] for k in ['usedSize','backingStorageSize']);perf+=f"- {profile}: heap+buffers main/Worker en estado de 339 series {total/2**20:.2f} MiB; mayor long task observado {a['max_longtask_ms']} ms; crecimiento retenido tras 50 ciclos producto/municipio {100*a['retained_heap_growth']:.3f}%. GPU NOT_MEASURED.\n"
perf+='\nWorker medido por sesión CDP específica; es un estado exigente, no un máximo continuo. RSS del renderer cubre más que heap JS; memoria GPU no está atribuida. El benchmark principal se ejecutó sin otros browsers de QA concurrentes; coexistieron tareas locales de documentación/CSV. No se afirma un laboratorio de hardware aislado. Los retoques finales de control de respuesta provincial y altura móvil no alteraron los arrays; se probaron en ensayos posteriores.\n\n## Distribución\n\n'
for label,key in [('Allowlist fuente','source_bytes'),('Mayor archivo fuente','source_max_file_bytes'),('Dist','dist_bytes'),('Mayor chunk web','largest_web_chunk_bytes'),('JS/CSS gzip','compressed_JS_CSS_bytes'),('Catálogo inicial','initial_catalog_bytes')]:perf+=f'- {label}: {dist[key]:,} bytes.\n'
perf+=f"- Dist: {dist['dist_files']:,} archivos, límites 250 MiB /15.000.\n"
packages=json.loads((repo.parent/'Packages/download_manifest.json').read_text());port=json.loads((repo.parent/'Packages/portable_manifest.json').read_text());perf+=f"- Datos/código/web: {len(packages['files'])} ZIP; portable: {len(port['parts'])} partes, {port['expanded_bytes']:,} bytes expandido; cada asset <250 MiB.\n"
perf+='\n## Alternativas y límites\n\nCanvas/WebGL: fixture lógico 3.000×10.000, semilla 42, 60 líneas cargadas y una serie exacta de 10.000; casos vacío/constante/cero/pico/huecos. Es un microbenchmark de renderer, no una comparación integral de plataformas. Canvas mide envío de dibujo; WebGL fuerza finalización con `finish`, por lo que no se deduce una superioridad universal.\n\n'
for name in ['Canvas','WebGL']:
    rows=[r for r in renderer['results'] if r['name']==name and 'draw_ms' in r]
    if rows:perf+=f"- {name}: {len(rows)} ensayos; mediana {statistics.median(x['draw_ms'] for x in rows):.3f} ms; p95 {percentile([x['draw_ms'] for x in rows]):.3f} ms.\n"
perf+='\nDuckDB-Wasm no se adquirió por restricción EACCES; falta comparación ejecutada. Firefox/WebKit no disponibles. No hay prueba en móvil físico, ni atribución GPU, ni traza de pico Worker continua. La duración completa de grupos ad hoc requiere instrumentación adicional aunque su progreso/cancelación y resultado se probaron. Por estas categorías pendientes T13 permanece BLOCKED y la arquitectura no se congela.\n'
write(e/'benchmarks/budget_results.json',budgets);(review/'RENDIMIENTO.md').write_text(perf,encoding='utf-8')
if any(x['status']=='FAIL' for x in budgets):raise RuntimeError('Measured budget failure: inspect budget_results before final delivery')
report='# Contract 05 — Validación local\n\nPENDING HUMAN ACCEPTANCE. Los resultados no constituyen aprobación ni cierre.\n\n'+md[md.index('| Criterio'):]+ '\n## Reproducción y paquetes\n\n193 particiones Parquet reconstruidas con todas sus celdas exactas; 12.067 archivos web idénticos por SHA-256. CSV: 193 particiones, todas sus celdas iguales y hashes deterministas en reconstrucción. Paquetes: CRC, tamaños, SHA-256, rutas locales y exploración de siete productos con solicitudes externas bloqueadas. Nivel B no se certifica donde faltan código/QA/escala.\n\nVer [rendimiento](Deliverables/Review/RENDIMIENTO.md), [auditoría](Deliverables/Review/AUDITORIA_SIETE_PRODUCTOS.md), [pendientes](Deliverables/Review/DECISIONES_PENDIENTES.md) y [guía](Deliverables/Review/README.md).\n'
(out/'91_VALIDATION_REPORT.md').write_text(report,encoding='utf-8')
print('VALIDATION_REPORT_WRITTEN',len(matrix),'criteria; acceptance PENDING')
