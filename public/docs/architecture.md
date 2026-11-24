# Arquitectura local candidata / Local candidate architecture

Estado: implementación local revisable, **arquitectura no congelada**. / Status: reviewable local implementation, **architecture not frozen**.

## Decisión implementada / Implemented choice

Una página estática con scripts JavaScript clásicos, geometría SVG de exactamente 339 municipios, gráficos Canvas y un Worker de descompresión/cálculo. No hay dependencia de CDN, clave, API analítica ni servidor remoto. La geometría original conserva todas sus partes y coordenadas; SVG se limita al mapa; el hero es una ilustración WebP local, nunca a miles de trayectorias. / One static page uses classic JavaScript scripts, the exact 339-unit SVG map, Canvas charts and a decoding/computation Worker. SVG does not render thousands of temporal lines.

La alternativa A del contrato se concreta sin Vite/TypeScript porque no se necesita un empaquetador para estos módulos y se evita su cadena de dependencias. No se presenta esta elección como ganadora definitiva: falta completar la comparación obligatoria con DuckDB-Wasm y navegadores adicionales. / The lightweight A candidate uses classic scripts without a bundler. The required comparison with DuckDB-Wasm and additional browsers remains incomplete.

Maestros: Parquet Zstandard y CSV gzip por producto/año, todas las columnas originales más claves y trazabilidad separadas. Web: Float64 little-endian gzip exacto, dividido en snapshots por fecha, series municipales y grupos. Las series diarias incluyen todas las variables municipales y usan bloques mensuales de transporte, sin agregacion temporal. El mapa nunca descarga el maestro nacional. LRU de datos decodificados: 64 MiB escritorio, 32 MiB móvil; cuatro peticiones concurrentes. / Masters preserve original precision and fields. Exact web arrays are divided by date and municipality; daily transport blocks retain all variables and original daily observations. Initial map loading never fetches a national master.

La vista spaghetti empieza con 60 municipios en escritorio y 30 en móvil, seleccionados reproduciblemente por ID dentro del grupo; informa la cantidad y permite llegar progresivamente a 339. Las bandas se calculan sobre el grupo completo, independientemente de las líneas visibles. La serie seleccionada siempre usa valores exactos. LOD conserva índices, extremos por intervalo y transiciones entre ausente/presente. Al ampliar el intervalo se carga progresivamente más resolución. / Spaghetti starts with an explicit, reproducible subset and can progressively reach all 339 series. Bands use the full group, independently of displayed trajectories.

## Alternativas y evidencia / Alternatives and evidence

| Alternativa | Evaluación | Límite de conclusión |
|---|---|---|
| A: Canvas, SVG limitado y arrays estáticos | Aplicación completa; recorridos automatizados fríos/calientes; integridad de todos los arrays | Candidata operativa, pendiente de todos los presupuestos e instrumentos |
| B: WebGL para trayectorias | Microbenchmark reproducible Canvas/WebGL con fixture lógico 3.000 × 10.000, carga visible acotada | No equivale a una implementación integral MapLibre/deck.gl; no demuestra superioridad de plataforma |
| C: DuckDB-Wasm/Arrow/Parquet en navegador | Inspección de documentación; adquisición de dependencia bloqueada por EACCES del entorno | Sin benchmark ejecutado; criterio comparativo BLOCKED |

El primer candidato de distribución excedía 250 MiB. Se sustituyó JSON redundante por arrays exactos comprimidos y se retiró un nivel de LOD precalculado redundante. No se perdió ninguna observación: comparación exacta de todas las series y reconstrucción independiente verificadas. Posteriormente el supervisor restringió el producto a series fuente sin filtros. / Distribution was reduced by exact binary encoding and removal of redundant precomputed visual levels, with no observation loss.

Los números finales, resultados crudos, restricciones de memoria y ensayos están en los reportes de revisión externos. Una prueba de API Canvas no mide lo mismo que la finalización GPU de WebGL; se informa esa limitación. La emulación móvil no es un teléfono físico. No se declara medido el heap de Workers cuando el instrumento no lo expone. / Final review reports distinguish browser heap, process RSS, GPU and unmeasured Worker allocations.

## Cuatro destinos separados / Four separate destinations

| Destino | Contenido previsto | Situación local |
|---|---|---|
| GitHub `Favioleiva/BoliviaSatellites` | Allowlist de código, tests, documentación, diccionarios, geografía y manifiestos pequeños | Preparado localmente; no push, sin credenciales ni maestros |
| Netlify | Solo `dist`, con datos web exactos y recursos locales | No deploy; presupuesto 250 MiB / 15.000 archivos |
| GitHub Releases | Maestros completos, fuentes municipales, código y datos web por partes versionadas | Assets ZIP locales <250 MiB, SHA-256; sin URLs remotas inventadas |
| Portable | Sitio completo, cápsulas Offline, fuente y paquetes científicos; HTML directo y servidor opcional | Extraer todas las partes; explorar sin conexión externa |

El checkout de Git no lleva `public/data`: se reconstruye o se extraen **todas** las partes `BoliviaSatellites_webdata_partNN.zip` en la raíz antes de `node scripts/build.mjs`. El build falla si falta un producto. Por tanto, no se propone conectar automáticamente un checkout vacío a Netlify. Tras autorización habrá que preparar este artefacto, resolver los enlaces a Releases reales y verificar cabeceras/caché/hash remotos. / A source-only Git checkout requires reconstruction or all versioned web-data parts before building. Deployment preparation and remote checks require separate authorization.

`downloads/packages/...` son rutas locales del servidor incluido, no enlaces Netlify existentes. Los datos pesados no se duplican dentro de `dist`. El futuro despliegue deberá sustituir esas rutas por URLs verificadas de los assets aprobados. El portable conserva resolución local. / Package paths are local routes, not existing Netlify endpoints. Future deployment needs verified approved Release URLs.

## Reutilización de referencias / Reuse

Agriculture aporta el universo territorial exacto, crosswalk, jerarquía cartográfica y navegación municipal. El observatorio poblacional aporta panel compacto, persistencia de selección y patrones de interacción; BoliviaQuarcs, jerarquía visual y exploración. Panel Plots aporta el patrón de trayectorias y referencias grupales; se conserva su atribución MIT. El renderer web es una implementación propia adaptada al volumen diario: los cuantiles y medias utilizan todo el grupo, nunca solo las líneas muestreadas. Los proyectos congelados se consultan y copian como referencias, sin modificarlos. / Existing projects supply geography and interaction/design patterns; the browser renderer is adapted to daily volume and full-group statistics.

Fuentes técnicas: [WebGL, MDN](https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API), [DecompressionStream, MDN](https://developer.mozilla.org/en-US/docs/Web/API/DecompressionStream), [DuckDB-Wasm](https://duckdb.org/docs/stable/clients/wasm/instantiation.html).


## Revision 02: direct file access / apertura directa

Double-click index.html; no server required. The Offline companion contains selective classic-script capsules of the exact gzip bytes. It is excluded from Git and Netlify, and included only in portable packages. HTTP keeps the original fetch path. Dist/package relative links are configured separately for the workspace and portable layouts.

El mapa conserva el lenguaje visual Agriculture C04 con ancho fluido autorizado en revision 08; paletas por magnitud en visual-design.md. Fuego y Black Marble muestran datos fuente con avisos persistentes, sin desbloquear su certificación. El hero ilustrado no reduce el tamaño del mapa.


## Actualizacion / Update: escala sincronizada

Por instruccion posterior del supervisor, la escala visual elegida se aplica al mapa, sparkline y spaghetti. Para luces nocturnas: ln(1000x+1), con paleta azul-amarillo-rojo. Las consultas conservan x e y; las descargas conservan x. Esta revision supersede las menciones anteriores a transformaciones solo del mapa. Ver nightlights-colours.md para fuentes NASA y detalles.

The selected visual transform now applies to the map, sparkline and spaghetti. Night lights default to ln(1000x+1), with blue/yellow/red colours. Readouts retain x and y; downloads retain original x. This supersedes earlier map-only display descriptions.

## Preparacion GitHub / GitHub preparation

El checkout fuente se restaura con `scripts/restore_webdata.py`, que verifica todos los hashes. El manifiesto y el procedimiento estan en [publication.md](publication.md). La evaluacion adicional de compresion sin perdida no resuelve el presupuesto web: sigue BLOCKED para Netlify. / The source checkout can restore all exact web arrays using the hash-verified restorer. Additional lossless-compression estimates do not meet the web budget; Netlify remains blocked.
