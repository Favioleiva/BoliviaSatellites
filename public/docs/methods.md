# Bolivia Satellites — Métodos / Methods

Esta versión local está pendiente de revisión humana. No certifica los productos científicamente bloqueados. / This local version awaits human review. Scientifically blocked products remain uncertified.

## Geografía / Geography

Se reutilizan exactamente los 339 polígonos y las correspondencias de Bolivia Agriculture, referencia 2015. `asdf_id` identifica el polígono. Los códigos fuente de Santa Rosa, San Javier y El Puente en HKU/Black Marble se preservan; seis correspondencias derivadas utilizan el diccionario original de Agriculture. No se transfieren valores entre homónimos ni a 343 municipios. / The exact Agriculture 339 polygons and original crosswalk are reused. Original discrepant codes remain preserved; six derived mappings use `asdf_id`. No geographic redistribution.

## Productos / Products

| Producto | Serie | Unidad | Método y limitación / Method and limitation |
|---|---|---|---|
| ERA5-Land | 1990-01–2026-05, mensual/monthly | °C | ECMWF monthly hourly reanalysis aggregate; K−273.15; zonal statistics at 11,132 m. Not a municipal thermometer. |
| GPM IMERG V07 | 2000-06–2026-05, mensual/monthly | mm/month | Half-hourly mm/h summed ×0.5 h. Corrected reducer property names. 339 complete municipal rows/month; global image count does not certify per-pixel temporal coverage or upstream status. |
| HKU NTL | 1992-04–2024-12, mensual/monthly | Source radiance | VIIRS-like reconstructed history, ~500 m. Rasterstats `all_touched=False`. Unfiltered municipal source series. Early history is reconstructed by the provider; it is not direct VIIRS observation since 1992. |
| MCD64A1 | 2000-11–2026-05, mensual/monthly | km²; shares dimensionless | BurnDate>0, land/valid QA bits, area sum at 500 m. Counts/QA inconsistent with supplied code; source values render directly with persistent warnings; scientific certification remains blocked. Five zero-area/zero-valid-area rows appear missing, while downloads retain raw zeros and flags. |
| MOD13Q1 | 2000-03–2026-05, mensual/monthly | NDVI/EVI dimensionless | 250 m, factor 0.0001; SummaryQA≤1; median of 16-day composites starting in month. No daily weighting. Coverage can be as low as 0.415%; no arbitrary threshold or clipping. |
| SatPM V6.GL.03 | 1998-01–2024-12, mensual/monthly | µg/m³ | Modelled concentration using satellite, atmospheric modelling and monitors. Strict/published means and fallback diagnostics retained. Extreme monthly values and mutable upstream map revision need provenance verification. Sum of concentrations is not emission mass. |
| Black Marble VNP46A2 | 2012-01-19–2026-05-31, diario/daily | Source radiance; applied physical scale unverified | Gap_Filled_DNB_BRDF-Corrected_NTL, collection 5200; NASA provider filling is not direct observation. Original extractor unavailable. 27,718 missing municipality-days retained; no imputation. Source values render directly with persistent warnings; scientific certification remains blocked. |

## Cobertura espacial / Spatial coverage

ERA5 y GPM tienen idénticos numeradores, denominadores y proporciones por municipio. En 27 municipios el ratio supera 1; Tacachi alcanza 1.100329954. Esta variable NO está certificada como fracción física. Las magnitudes se muestran con advertencias por autorización humana explícita. No se trunca a 1 ni se corrige lluvia/temperatura usando el ratio. La hipótesis de grilla, proyección y fracciones de frontera no constituye una causa demostrada. No se ejecutaron nuevas extracciones. / ERA5 and GPM share 27 area ratios above one. Raw ratios remain uncertified; values are displayed with explicitly authorized warnings. No clipping, rescaling or new extraction.

## Tiempo, faltantes y distribuciones / Time, gaps and distributions

La referencia solicitada es noviembre del año más reciente con valores (día 10 en series diarias). Si no está disponible, se busca exclusivamente noviembre/día 10 de años anteriores. Se muestran ambas referencias. Sin ningún noviembre elegible, no hay sustitución automática. Las selecciones manuales nunca cambian silenciosamente. Los extremos de cobertura parciales no son defectos. / Requested and effective references remain distinct. Only previous November / November 10 can be the initial fallback. Manual dates remain unchanged.

Las bandas y referencias se calculan entre todos los municipios válidos del grupo, en cada fecha, con cuantiles lineales y `n_valid` explícito; no a partir del subconjunto de trayectorias. No son percentiles espaciales internos, intervalos de confianza ni valores ponderados por población. / Bands describe the municipal distribution, not within-municipality pixel percentiles, confidence intervals or population-weighted estimates.

Los gráficos Canvas pueden mostrar menos puntos que la serie completa para adaptarse a la pantalla. Esta reducción es exclusivamente visual: conserva índices, extremos de cada intervalo y fronteras de huecos; no interpola ni cambia los valores descargables. La advertencia se muestra junto a cada gráfico y la serie original completa está disponible mediante descarga. / Canvas charts may show fewer points than the complete series to fit the screen. This reduction is visual only: it preserves original indices, interval extrema and gap boundaries; it does not interpolate or change downloadable values. Each chart shows this notice and offers the complete original series.

## Escala del mapa / Map scale

El selector ofrece escala lineal, `ln(1+x)` y `ln(1+1000·x)`. Las dos últimas solo están disponibles cuando todo el dominio del indicador cumple `1+k·x>0`. Temperaturas y NDVI/EVI parten en escala lineal; lluvia, fuego y PM2.5 en `ln(1+x)`; luces en `ln(1+1000·x)`. Son elecciones de contraste visual, no conversiones físicas ni filtros. La leyenda informa la fórmula. Las series temporales, tooltips y descargas conservan los valores crudos; multiplicar por mil no cambia la unidad científica del archivo. / The selector offers linear, `ln(1+x)` and `ln(1+1000·x)` colour scales, with an explicit domain guard. These are display choices, not physical corrections. Time series, tooltips and downloads preserve the original observations and units.

## Fuentes primarias / Primary sources

- [ERA5-Land](https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_MONTHLY_AGGR)
- [GPM IMERG V07](https://developers.google.com/earth-engine/datasets/catalog/NASA_GPM_L3_IMERG_V07)
- [MCD64A1](https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD64A1)
- [MOD13Q1](https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD13Q1)
- [HKU DOI](https://doi.org/10.25442/hku.31321315.v2)
- [SatPM](https://www.satpm.org/v6-gl-03)
- [NASA Black Marble](https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/VNP46A2)

## Frecuencias diarias futuras / Future daily feasibility

Black Marble es el único agregado diario local. ERA5-Land tiene fuentes diarias/horarias y GPM de 30 minutos, pero no se derivan días desde los meses locales. MODIS BurnDate permite estudiar fechas estimadas de eventos, no una nueva observación diaria. MOD13Q1 no permite recuperar índices diarios desde compuestos de 16 días. No se identificó equivalente diario de toda la historia HKU ni de SatPM V6.GL.03. Cualquier nueva extracción queda fuera de esta ejecución. / Daily alternatives require separate scientific definitions and authorization; no monthly-to-daily interpolation is used.


## Actualizacion / Update: escala sincronizada

Por instruccion posterior del supervisor, la escala visual elegida se aplica al mapa, sparkline y spaghetti. Para luces nocturnas: ln(1000x+1), con paleta azul-amarillo-rojo. Las consultas conservan x e y; las descargas conservan x. Esta revision supersede las menciones anteriores a transformaciones solo del mapa. Ver nightlights-colours.md para fuentes NASA y detalles.

The selected visual transform now applies to the map, sparkline and spaghetti. Night lights default to ln(1000x+1), with blue/yellow/red colours. Readouts retain x and y; downloads retain original x. This supersedes earlier map-only display descriptions.
