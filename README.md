# Bolivia Satellites

[English](README.en.md) | [Metodos](public/docs/methods.md) | [Preparacion de publicacion](public/docs/publication.md)

Plataforma cientifica bilingue para siete productos ambientales y satelitales,
sobre las **339 geometrias originales de Bolivia Agriculture**, enlazadas por
`asdf_id`. Candidato para revision humana; la preparacion de este repositorio
no implica publicacion, aceptacion cientifica ni cierre del contrato.

## Aplicacion actual

- Una pagina, siete productos y referencia inicial fija del 10 de noviembre de
  2025 (noviembre de 2025 para mensuales); fecha efectiva y faltantes explicitos.
- Mapa de ancho adaptable; cifras sin recuadros en sus espacios libres.
- Historia municipal, Top 10 y Bottom 10 sincronizados; nombre y valor en cada fila.
- Media cruda del pool, media municipal del periodo y media historica del municipio.
- Centro de color: inversa de la media del pool en la escala visual elegida.
  Temperatura lineal; luces nocturnas por defecto `ln(1000*x+1)`.
- Spaghetti progresivo hasta 339 series, bandas y reduccion visual advertida ES/EN.
- Observaciones originales completas y descargas sin filtros ni sustituciones.

Productos: ERA5-Land, GPM IMERG V07, HKU NTL, MODIS MCD64A1,
MODIS MOD13Q1, SatPM PM2.5 y NASA Black Marble. EDGAR esta excluido.
Black Marble conserva 23 campos numericos, incluida la suma municipal.

## Desde un checkout limpio

El repositorio **no contiene los datos web grandes**, maestros, ZIP, `dist`
ni `Offline`. Requiere Node >=22 y Python >=3.10 (biblioteca estandar para
restaurar datos). No hay dependencias npm ni CDN.

1. Obtenga las dos partes `BoliviaSatellites_webdata_partNN.zip` del conjunto
   versionado aprobado y coloquelas juntas en una carpeta `Packages`.
2. Desde esta carpeta del repositorio:

```powershell
python -B scripts/restore_webdata.py --packages ../Packages
node scripts/build.mjs
python -B scripts/serve_local.py --root dist --packages ../Packages --port 8768
```

Abra `http://127.0.0.1:8768/`. El restaurador verifica SHA-256, tamanos y cada
miembro contra `distribution/webdata-manifest.json`, y rechaza partes mezcladas.
Las descargas cientificas necesitan tambien sus ZIP correspondientes en `Packages`.

**Estado actual del build:** genera `dist`, pero termina con codigo 1 porque el
sitio completo supera el presupuesto contractual de 250 MiB. Ese fallo permanece
visible; no se aumenta el limite. El sitio local se puede revisar despues del
build. Netlify permanece bloqueado hasta resolver ese presupuesto y sus otras
verificaciones pendientes. No conectar un checkout sin datos a un deploy automatico.

El tag propuesto y los assets todavia no son enlaces publicados. Tras su publicacion
expresamente autorizada, puede restaurarse desde un tag concreto mediante:

```powershell
python -B scripts/restore_webdata.py --release-base-url https://github.com/Favioleiva/BoliviaSatellites/releases/download/TAG_APROBADO
```

Este comando no es una extraccion satelital; descarga un snapshot ya generado.
No utiliza `latest` ni claves en el navegador.

## Portable y HTML sin servidor

Extraiga todas las partes `BoliviaSatellites_portable_partNN.zip` en una misma
carpeta y abra `ABRIR_BOLIVIA_SATELLITES.html`. Conserve `site`, `Offline` y
`packages` juntos. Incluye codigo, datos y descargas completas; no necesita internet.
Para generar el companion local desde un checkout restaurado:
`python -B scripts/build_offline.py`, seguido de `node scripts/build.mjs`.

## Ciencia, datos y reproduccion

Los maestros Parquet y CSV gzip por producto/ano conservan las columnas fuente,
precision e identificadores. Las escalas visuales se aplican al mapa y graficos;
**las descargas conservan x original**. Las medias informativas siguen siendo
aritmeticas de valores originales. Los centros de color cambian con la escala,
no con la fecha o el municipio. [Definiciones](public/docs/visual-design.md).

`code/run.py` reconstruye desde agregados suministrados, sin nuevas extracciones.
[Guia completa](public/docs/reproducibility.md). `requirements.lock` registra el
entorno cientifico. `code/source_workflows` conserva codigo upstream de referencia;
no se ejecuta automaticamente. Los notebooks publicables no contienen outputs,
widgets o metadatos de sesion; sus celdas fuente permanecen intactas y la
sanitizacion se registra en `provenance/notebook_sanitization.json`.

Limites: cobertura espacial >1 en ERA5/GPM conservada con advertencias;
reconstruccion upstream de HKU; QA de area quemada; trazabilidad/extremos de
SatPM; escala/extractor/QA y discrepancias numericas de Black Marble pendientes.
No se declara certificacion cientifica global. Las seis discrepancias de codigos
HKU/Black Marble se conservan y no se usa cartografia de 343 municipios.

## Distribucion y licencia

Git: codigo, pruebas, documentacion, geografia, catalogos y manifiestos pequenos.
Releases: datos, fuentes agregadas, webdata, codigo y portable por partes.
Netlify: solo el `dist` validado; nunca maestros, Evidence, paquetes ni credenciales.
Los archivos privados de auditoria y contratos no se incluyen en Git.

La licencia del codigo nuevo y la seleccion de archivos redistribuibles estan
pendientes de decision humana. Se preservan las atribuciones y licencias de
terceros en `LICENSES` y `THIRD_PARTY_NOTICES.txt`; no se aplica una licencia
abierta general a todos los datos. Nada se publica automaticamente.

## Correccion del arranque Netlify

`netlify.toml` ejecuta ahora `python3 scripts/build_netlify.py`. Antes del build,
restaura los arrays desde una Release publicada cuyo tag exacto se indica en
`BOLIVIA_DATA_RELEASE_TAG` (variable del entorno de build de Netlify). Deben estar
subidos los 12 assets del manifiesto de descargas, con los tamanos/hashes previstos.
Los 10 ZIP portable son independientes del arranque web. El script valida los
assets, restaura los dos webdata ZIP con SHA-256 y escribe las URL versionadas
solo en el manifiesto de `dist`. No modifica el manifiesto fuente ni publica.

Sin Release/tag emite `C05_RELEASE_REQUIRED` o `C05_RELEASE_UNAVAILABLE`.
Con los datos presentes, el candidato actual sigue fallando `C05_BUDGET_EXCEEDED`
(~287 MiB >250 MiB). Este cambio resuelve la dependencia ausente, no autoriza
ignorar ese limite. No reintentar el despliegue hasta resolver ambos requisitos.
Prueba offline: `python -B scripts/build_netlify.py --release-tag TAG --packages ../Packages`;
verifica paquetes locales y produce enlaces de prueba, sin comprobar una Release remota.
