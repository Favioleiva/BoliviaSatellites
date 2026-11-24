# Bolivia Satellites

[English](README.en.md) | [Metodos](public/docs/methods.md) | [Preparacion de publicacion](public/docs/publication.md)

Plataforma cientifica bilingue para siete productos ambientales y satelitales,
sobre las **339 geometrias originales de Bolivia Agriculture**, enlazadas por
`asdf_id`. Las limitaciones cientificas y tecnicas de cada producto se
documentan explicitamente en [Metodos](public/docs/methods.md).

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

**Presupuesto vigente:** 300 MiB (314.572.800 bytes), autorizado por el supervisor
en la revision 11; se conserva el limite de 15.000 archivos. El build verifica
ambos limites. El sitio actual ocupa aproximadamente 287 MiB. La Release de datos
y las verificaciones remotas siguen pendientes.

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

## Distribucion, licencia y cita

Git: codigo, pruebas, documentacion, geografia, catalogos y manifiestos pequenos.
Releases: datos, fuentes agregadas, webdata, codigo y portable por partes.
Netlify: solo el `dist` validado; nunca maestros, Evidence, paquetes ni credenciales.
Los archivos privados de auditoria y contratos no se incluyen en Git.

El codigo fuente y la documentacion originales de este repositorio se distribuyen
bajo la **Licencia MIT** ([LICENSE](LICENSE), Copyright (c) 2026 Favio Leiva).
Se preservan las atribuciones y licencias de terceros en `LICENSES` y
`THIRD_PARTY_NOTICES.txt`; la licencia MIT no reemplaza las licencias ni los
terminos originales de los productos satelitales, datos ambientales ni cartografia
de terceros.

### Como citar

> Leiva, F. (2026). *BoliviaSatellites: Bilingual Municipal Satellite and Environmental Data Platform for Bolivia (339 Municipalities)* [Software]. GitHub. https://github.com/Favioleiva/BoliviaSatellites

```bibtex
@software{leiva2026boliviasatellites,
  author       = {Leiva, Favio},
  title        = {{BoliviaSatellites: Bilingual Municipal Satellite and Environmental Data Platform for Bolivia (339 Municipalities)}},
  year         = {2026},
  publisher    = {GitHub},
  url          = {https://github.com/Favioleiva/BoliviaSatellites},
  note         = {MIT License (newly authored code and documentation); third-party satellite datasets (ECMWF ERA5-Land, NASA GPM/MODIS/Black Marble, HKU, SatPM) and cartography retain their respective licenses}
}
```

Metadatos de cita estructurados disponibles en [CITATION.cff](CITATION.cff).

## Correccion del arranque Netlify

`netlify.toml` ejecuta ahora `python3 scripts/build_netlify.py`. Antes del build,
restaura los arrays desde una Release publicada cuyo tag exacto se indica en
`BOLIVIA_DATA_RELEASE_TAG` (variable del entorno de build de Netlify). Deben estar
subidos los 12 assets del manifiesto de descargas, con los tamanos/hashes previstos.
Los 10 ZIP portable son independientes del arranque web. El script valida los
assets, restaura los dos webdata ZIP con SHA-256 y escribe las URL versionadas
solo en el manifiesto de `dist`. No modifica el manifiesto fuente ni publica.

Sin Release/tag emite `C05_RELEASE_REQUIRED` o `C05_RELEASE_UNAVAILABLE`.
Con los datos restaurados, el sitio de ~287 MiB cabe en el presupuesto autorizado
de 300 MiB. `C05_BUDGET_EXCEEDED` sigue protegiendo ese limite. Antes del despliegue
deben existir la Release de datos y su tag configurado.
Prueba offline: `python -B scripts/build_netlify.py --release-tag TAG --packages ../Packages`;
verifica paquetes locales y produce enlaces de prueba, sin comprobar una Release remota.
