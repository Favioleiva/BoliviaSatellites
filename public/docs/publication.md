# Preparación de publicación / Publication preparation

**Candidato local, sin publicar. / Local candidate, not published.**
La autorización actual comprende preparación y validación local. No incluye push,
Releases, Netlify, gastos ni aceptación del contrato. / Current authorization covers
local preparation and validation, not uploads, deployment, spending or acceptance.

## Destinos / Destinations

| Destino / Destination | Contenido / Contents | Estado / Status |
|---|---|---|
| GitHub `Favioleiva/BoliviaSatellites` | Código, pruebas, documentación ES/EN, geometría exacta, diccionarios y manifiestos / Code, tests, bilingual docs, exact geography, dictionaries and manifests | Copia local con allowlist; repositorio remoto vacío en la consulta del 24-11-2026 / Local allowlisted copy; remote empty when inspected on 2026-11-24 |
| Releases | Maestros completos, fuentes suministradas, código y arrays web; ZIP versionados y SHA-256 / Full masters, supplied sources, code and exact web arrays; versioned ZIPs and SHA-256 | Archivos locales; ningún asset subido / Local assets only |
| Netlify | Solo sitio compilado `dist`; descargas pesadas en Releases / Built `dist` only; large downloads in Releases | Bloqueado por presupuesto de 250 MiB / Blocked by the 250 MiB budget |
| Portable | Sitio, cápsulas Offline, código y paquetes científicos / Site, Offline capsules, code and scientific packages | Extraer todas las partes en una carpeta / Extract all parts together |

Git excluye `public/data`, maestros, fuentes pesadas, `dist`, `Offline`, paquetes,
evidencia interna, credenciales y cachés. `publication_allowlist.json` identifica
cada archivo seleccionado y su SHA-256; los metadatos Git y el propio manifiesto
quedan fuera de su lista para evitar hashes circulares. / Git excludes large data,
builds, packages, internal evidence, credentials and caches. The allowlist records
each selected file and hash, excluding itself and Git metadata.

Los notebooks publicables conservan exactamente las celdas fuente. Se retiraron
metadatos de widgets y sesiones de las copias derivadas; las fuentes originales
no cambiaron. Véase `provenance/notebook_sanitization.json`. / Publishable notebooks
retain their exact source cells; session metadata was removed from derived copies.

## Restauración verificable / Verified restoration

Desde un checkout limpio, colocar los dos ZIP `BoliviaSatellites_webdata_partNN.zip`
en una carpeta local `Packages` y ejecutar desde la raíz del repositorio:
/ From a clean checkout, place both webdata ZIP parts in a local Packages folder:

```sh
python -B scripts/restore_webdata.py --packages ../Packages
node scripts/build.mjs
python -B scripts/serve_local.py --root dist --packages ../Packages --port 8768
```

El restaurador verifica tamaño, SHA-256 de los ZIP y de los 6.394 archivos,
integridad del conjunto y rutas antes de restaurar los arrays exactos. Rechaza
datos existentes diferentes; no extrae datos satelitales nuevos. / The restorer
checks archive and member hashes, completeness and paths. It refuses differing
existing data and never performs satellite extraction.

**El build genera la vista local pero termina con código 1 mientras se exceda
el presupuesto.** El sitio ocupa aproximadamente 287 MiB; no se aumenta el
límite contractual ni se declara listo para Netlify. La evaluación de compresión
sin pérdida disponible no resuelve esa diferencia. / The build creates the local
preview but returns exit code 1 while over budget. The approximately 287 MiB site
is not declared ready for Netlify; the contractual limit remains unchanged.

## Pasos posteriores a autorización / Steps after authorization

1. El supervisor selecciona la licencia del código nuevo y confirma la
   redistribución de los archivos concretos. Se conservan las licencias de terceros;
   no se presume una licencia global. / Select the project code license and confirm
   redistribution of the selected assets; existing third-party terms remain.
2. Revisar el commit y manifiesto local; autorizar por separado su push al repositorio
   y la subida de los assets aprobados. / Review the exact local commit and manifests;
   authorize source push and selected asset uploads explicitly.
3. Elegir una etiqueta inmutable. `v0.1.0-c05-review.1` es solo una propuesta;
   no existe una Release publicada por este trabajo. / Choose an immutable tag;
   the suggested tag is not a published Release.
4. Tras subir, verificar las URL reales y hashes. Sustituir las rutas locales
   `downloads/packages/...` del manifiesto web por URL verificadas de esa Release;
   probar los enlaces ES/EN. Nunca usar `latest` para reproducibilidad. / Verify
   actual URLs and hashes, replace local package routes with verified Release URLs,
   and test bilingual download links. Never use `latest` for reproducibility.
5. Resolver y medir el presupuesto web antes de solicitar despliegue Netlify.
   Revisar caché, descarga inicial, memoria y respuesta en el artefacto exacto.
   No conectar automáticamente un checkout sin datos ni ignorar el error del build.
   / Resolve and measure the web budget before deployment; do not bypass the build
   failure or connect a source-only checkout without restoring its data.

No se incluye automatización que publique o despliegue. No hay URL Netlify inventada.
Las advertencias científicas y criterios pendientes acompañan la entrega; una
prueba técnica PASS no equivale a aceptación humana. / No automatic publishing or
deployment is configured, and no Netlify URL is claimed. Scientific limitations
remain visible; technical PASS does not constitute human acceptance.
