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
| Netlify | Solo sitio compilado `dist`; descargas pesadas en Releases / Built `dist` only; large downloads in Releases | Presupuesto autorizado 300 MiB; Release y pruebas remotas pendientes / Authorized 300 MiB budget; data Release and remote checks pending |
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

El supervisor autorizo ampliar el presupuesto total de dist a **300 MiB**
(314.572.800 bytes) en la revision 11. El sitio de ~287 MiB cabe en ese limite.
Se mantienen 15.000 archivos y 250 MiB por ZIP. / The supervisor explicitly
authorized a **300 MiB** total build budget in revision 11. The ~287 MiB site fits.
The 15,000-file limit and 250 MiB per ZIP remain unchanged.

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
5. Verificar el presupuesto autorizado de 300 MiB antes del despliegue Netlify.
   Revisar caché, descarga inicial, memoria y respuesta en el artefacto exacto.
   No conectar automáticamente un checkout sin datos ni ignorar el error del build.
   / Verify the authorized 300 MiB web budget before deployment; do not bypass the build
   failure or connect a source-only checkout without restoring its data.

No se incluye automatización que publique o despliegue. No hay URL Netlify inventada.
Las advertencias científicas y criterios pendientes acompañan la entrega; una
prueba técnica PASS no equivale a aceptación humana. / No automatic publishing or
deployment is configured, and no Netlify URL is claimed. Scientific limitations
remain visible; technical PASS does not constitute human acceptance.

## Revision 10: arranque Netlify / Netlify bootstrap

La configuracion ahora restaura los datos antes del build mediante
`python3 scripts/build_netlify.py`. Se requiere `BOLIVIA_DATA_RELEASE_TAG` en el
entorno de build y una Release publicada con los 12 assets exactos del manifiesto.
El script comprueba el inventario remoto, restaura ambos ZIP webdata con SHA-256
y genera las URL de descargas en `dist`; reemplaza el paso manual de sustitucion
antes descrito. Las fuentes conservan sus rutas locales. No sube archivos.

The build now restores the exact webdata before compilation. Set
`BOLIVIA_DATA_RELEASE_TAG` to a published tag containing all 12 matching download
assets. Release metadata is validated (including SHA-256 when GitHub supplies it);
restoration independently checks both archive hashes and every webdata member.
Scientific ZIPs retain their recorded hashes without being downloaded into the
site. The script generates pinned Release download links only in `dist`.

La consulta del remoto durante esta correccion no encontro Releases. La subida
de datos debe completarse por separado. La revision 11 autoriza 300 MiB para dist. La restauracion y el cumplimiento
del tamano no certifican por si solos un despliegue remoto.

No Release existed at the read-only check for this correction. Asset uploading is
a separate step. Revision 11 authorizes a 300 MiB dist budget. Restoration and size compliance
alone do not certify remote deployment.

Referencia tecnica / Technical reference:
[Netlify build environment variables](https://docs.netlify.com/build/configure-builds/environment-variables/).
