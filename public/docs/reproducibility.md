# Reproducción / Reproduction

## Checkout limpio / Clean checkout

Restaurar los arrays exactos con `python -B scripts/restore_webdata.py --packages ../Packages`, antes de construir la web. El manifiesto versionado verifica los ZIP y cada archivo por SHA-256. Ver [publicacion / publication](publication.md) para los cuatro destinos y el bloqueo de presupuesto. / Restore exact web arrays from the versioned, hash-verified local assets before building. See the publication guide for distribution and the outstanding web budget.

## Nivel A / Level A

Reconstrucción local desde agregados municipales suministrados; no requiere nuevas extracciones satelitales. Los paquetes de cada producto contienen `sources/Inputs/Satellites/...` y `master/<product>/base/<year>.parquet` más CSV gzip. Las descargas conservan los datos fuente sin filtros y su precisión. Unir `sources/` de todas las partes en una carpeta `Sources`.

Extraer todas las partes de datos en una misma carpeta `ExtractedData`. El siguiente comando copia los agregados y la geografía originales a una carpeta nueva y prepara el espejo de auditoría Black Marble como copia idéntica, sin añadir observaciones. / Extract every data part into `ExtractedData`. Prepare a new isolated input tree with the supplied aggregates, original geography and a byte-identical audit mirror:

```
python -B scripts/prepare_sources.py --data ExtractedData --destination Sources
```

Run from a clean working directory using the supplied Python dependencies:

```
python -B code/run.py build-data --input-root Sources --output-root Rebuilt
python -B code/run.py build-webdata --output-root Rebuilt
```

No code path calls GEE, Earthdata, GitHub publishing or Netlify. Existing upstream workflows are reference code and are not launched automatically. A reference input may have provider-modelled values or original diagnostic columns; unfiltered does not mean an unprocessed sensor raster.

## Nivel B / Level B

Reproducción del procesamiento científico original desde rasters: incompleta donde faltan extractor, revisión, escala o QA. En particular, el descargador Black Marble no reemplaza HDF→máscaras→estadísticos. No se certifica ese nivel ni se ejecutan extracciones nuevas. / Original raster-level reproduction remains blocked where extractor, revision, applied scale or QA are missing. The Black Marble downloader is not an extraction pipeline.

## Formatos / Formats

Maestros anchos Parquet Zstandard y CSV gzip conservan columnas nativas, códigos, metadatos y referencia de fila fuente. `geo_id` es `asdf_id` de la geografía `bolivia339_2015`; el código municipal normalizado está separado del código original. Los duplicados equivalentes de prueba se colapsan solo en el maestro, manteniendo sus referencias en auditoría.

En los CSV gzip maestros, `\N` representa nulo y una celda vacía de texto conserva la cadena vacía original; esto evita confundir ausencia con metadatos vacíos. Leer con `keep_default_na=False, na_values=[r'\N'], float_precision='round_trip'` y tipos de identificadores string. Los CSV fuente incluidos se conservan byte por byte en su formato original. La descarga interactiva de una serie usa celda vacía para valor numérico faltante, acompañada por flags. / Master CSV gzip uses `\N` for null, preserving empty strings separately; supplied native CSVs remain byte-identical. Interactive numeric-series CSV uses blank missing values and explicit flags.

Los arrays web conservan Float64 IEEE-754 little-endian exacto, comprimido con gzip. Mapas y series municipales contienen todas las variables y tres columnas de QA (flags, cobertura, conteo); Black Marble incluye 23 variables, 26 columnas en total. Los bloques diarios se transportan agrupados por mes sin agregar observaciones. Black Marble usa C05SHF02, byte-shuffle por columna antes de gzip; el Worker reconstruye los bytes originales. NaN es faltante, no cero. Orden y dimensiones en catalogos; especificacion en web-encoding.md. LOD conserva indices y valores originales para representacion, sin sustituir la serie completa. / Exact Float64 arrays retain all variables and three QA fields; Black Marble has 26 columns. Daily observations are transported in monthly blocks without temporal aggregation. C05SHF02 reversibly shuffles column bytes before gzip. LOD preserves original indices and values.

Las transformaciones visuales se sincronizan en mapa, sparkline y spaghetti; las descargas y maestros conservan valores originales. Centro de color = inversa de la media del pool transformado; temperatura lineal. / Visual transforms synchronize the map, sparkline and spaghetti; masters and downloads retain original values. Colour centre is the inverse transformed-pool mean; temperature remains linear.

## Verificación / Verification

SHA-256 y tamaños en el manifiesto; comparación exacta de Parquet tras reapertura; verificación de todas las series/snapshots; bandas cotejadas con una implementación independiente; huecos preservados. Los reportes externos de ejecución y validación documentan PASS/FAIL/BLOCKED/NOT_RUN. No confundir controles estructurales con aceptación científica humana.
