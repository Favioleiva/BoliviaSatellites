# Diseño visual / Visual design

## Ancho adaptable y rankings / Fluid width and rankings — revisión 08

Se sustituye el límite de 1280 px por un contenedor de ancho completo, con
márgenes laterales de 16–40 px. El panel derecho ocupa aproximadamente el 35 %
del viewport, entre 380 y 960 px; mapa, serie y rankings aprovechan el ancho
adicional. Se preservan proporciones y geometría de Bolivia; el mapa crece
con el espacio disponible, sin estirar los polígonos. Esto sustituye la
exigencia anterior de dimensiones idénticas a Agriculture C04, por instrucción
posterior del supervisor de aprovechar las pantallas horizontales.

En cada fila de ambos rankings, nombre y valor aparecen uno al lado del otro,
con números alineados a la derecha. Cifras de más de 12 caracteres se presentan
en notación científica abreviada; descripción accesible y tooltip conservan
los valores fuente completos. Por debajo de 1100 px, mapa y panel se apilan;
por debajo de 540 px, Top y Bottom se apilan también, manteniendo siempre
nombre y valor en la misma fila. Orden, selección y observaciones no cambian.

The 1280 px cap is replaced by a full-width container with 16–40 px gutters.
The right panel takes approximately 35% of the viewport, bounded by 380–960 px.
Map, series and rankings use the extra space while preserving Bolivia's
geometry and proportions. This supersedes the earlier Agriculture C04 pixel
dimensions following the supervisor's explicit request for a wider workspace.
Municipality names and right-aligned values share each ranking row. Numbers
longer than 12 characters use abbreviated scientific notation; accessible
descriptions and tooltips retain full source values. Below 1100 px, map and
panel stack; below 540 px, Top and Bottom also stack, while names and values
remain side by side within every row. Data, ordering and selection are unchanged.

## Anotaciones y centro de color / Annotations and colour centre — revisión 07

Las cuatro cifras se distribuyen sin cajas en los espacios libres alrededor
de Bolivia, dentro del lienzo del mapa. En móvil y con zoom, se habilita espacio
libre superior e inferior dentro del área cartográfica para evitar solapamientos
con municipios. La geometría, proporciones y tamaño del lienzo se conservan.
Las tres medias informativas siguen en valores originales y se distinguen del
centro de color transformado. La media cruda del pool se identifica como tal.

The four figures sit unboxed in the whitespace around Bolivia inside the map
canvas. On mobile and when zoomed, free space above and below the geographic
canvas prevents overlap with municipalities. Geometry, proportions and canvas
size are preserved. The three informational means retain original values;
the raw pool mean is explicitly distinguished from the transformed colour centre.

Para cada variable y transformación monotónica `f`, el centro es
`f⁻¹(mean(f(x)))`, sobre todo el pool histórico elegible, con igual peso por
observación. Las dos mitades de color interpolan linealmente en el espacio
transformado, ancladas en mínimo, media transformada y máximo transformado.
La leyenda presenta los tres anclajes en unidades originales:

| Escala / Scale | Centro en unidades originales / Original-unit centre |
|---|---|
| Lineal / Linear | `mean(x)` |
| `ln(1+x)` | `expm1(mean(log1p(x)))` |
| `ln(1+1000x)` | `expm1(mean(log1p(1000*x)))/1000` |

El centro cambia con la escala; permanece fijo entre fechas, municipios,
grupos y ventanas. Extremos originales de toda la historia. Una transformación
fuera del dominio de cualquier observación válida se deshabilita completa,
sin descartar valores silenciosamente. Temperatura conserva escala lineal.
Los degradados existentes de series de luces nocturnas utilizan el mismo anclaje.

The centre changes with the scale and remains fixed across dates, municipalities,
groups and windows. Endpoints retain the full historical minimum and maximum.
A transform outside the domain of any eligible observation is entirely disabled,
without silently discarding values. Temperature remains linear. Existing night-light
series gradients share the same colour anchor. Summaries are precomputed;
no full-pool browser download is required. Original downloads are unchanged.

Ejemplo / Example, GPM media / mean: centro lineal 76.753132; `ln(1+x)`
33.985990; `ln(1+1000x)` 29.162130 mm/mes / mm/month.
Reproducir / Reproduce: `python -B scripts/update_context_pools.py` y / and
`python -B tests/ui/transformed_centres.py`.

## Contexto y extremos / Context and extremes

Dentro de la tarjeta del mapa aparecen la observación original del municipio
y período seleccionados y tres medias aprobadas por el supervisor:

- **Pool histórico:** media de todas las observaciones municipio-período válidas
  de toda la historia de la variable, con igual peso por observación.
- **Entre municipios:** media de los municipios con valor válido en el período
  seleccionado. La selección de un municipio no cambia esta referencia.
- **Historia del municipio:** media de todos los períodos válidos del municipio
  seleccionado: meses para productos mensuales y días para Black Marble.

Se calculan antes de logaritmos u otras escalas visuales, en unidades originales.
Se indican los tamaños de muestra; faltantes y filas sin superficie válida (QA
bit 8) no se imputan ni entran en la media. Se conservan coberturas >1 con sus
advertencias. Cada variable conserva su propia definición y advertencias fuente.
Los grupos y ventanas del spaghetti no redefinen estas tres medias. El pool
va precalculado en el catálogo; las otras medias utilizan únicamente el mapa
actual (339 observaciones) y la serie completa del municipio ya cargada.

Top 10 y Bottom 10 aparecen lado a lado debajo de la gráfica temporal en
pantallas amplias; en móviles estrechos se apilan. Ambos ordenan observaciones originales válidas, descendente/ascendente,
con desempate por `asdf_id` ascendente. Los valores visibles siguen la escala
visual elegida; la descripción accesible conserva el valor original. No son
juicios de calidad territorial. Ceros válidos entran en Bottom 10. Sin datos
se muestran listas vacías; con menos de 20 observaciones puede haber solapamiento.
Seleccionar cualquier entrada actualiza mapa, serie y anotaciones de contexto.

The map card shows the selected municipality-period observation and three
supervisor-approved means: the full historical municipality-period pool, all
valid municipalities in the selected period, and all valid periods of the
selected municipality (months, or days for Black Marble). All use original
values before visual transforms, with equal observation weights and explicit
sample counts. Nonfinite observations and QA bit 8 are excluded without
imputation; coverage >1 remains with warnings. Each variable retains its source
definition and limitations. Spaghetti windows/groups do not redefine these
references. Pool metadata is precomputed; the browser reuses the current map
and the selected municipality's series, avoiding a complete-pool download.

Top 10 and Bottom 10 sit side by side beneath the time series on wide
screens and stack on narrow phones. They sort valid source values in descending/ascending order, resolving
ties by ascending `asdf_id`. Visible values follow the selected display scale;
accessible descriptions retain original values. Valid zeros are included.
There are no rankings without data; lists can overlap when fewer than 20
observations exist. Clicking either list synchronizes map, series and context.

Reproducción / Reproduction: `python -B scripts/update_context_pools.py`;
`python -B tests/ui/rankings_context.py`. The complete `code/run.py` pipeline
also generates historical pool metadata for all seven products.

## ES

El mapa conserva el lenguaje visual de Agriculture C04, con dimensiones
adaptables según la revisión 08: tarjetas de 14 px y área cartográfica de
hasta 1040 px de alto en pantallas grandes. En móvil se
apilan mapa y panel; el mapa conserva su proporción y alcanza 520 px de alto.
La altura no se reduce para acomodar el hero. La geometría fuente de 339
municipios no cambia. El lienzo utiliza un viewBox 700 × 800 como Agriculture.

Cada magnitud tiene una paleta explícita en `src/palettes.js`: temperatura
azul–amarillo–rojo; precipitación marrón–ocre–amarillo–verde azulado (poca a mucha lluvia,
sin blanco); HKU azul–amarillo–rojo; área quemada
crema–naranja–rojo; NDVI ocre–verde; EVI crema–verde azulado; PM2.5 crema–violeta;
Black Marble azul–amarillo–rojo. Desviación estándar e IQR usan violeta secuencial:
dispersión de temperatura no significa frío/calor. Las familias comparten el
mismo sistema de leyendas, tipografía, selección y valores faltantes.

El rango es el mínimo y máximo originales de toda la serie para cada variable,
constante entre fechas. Para temperatura, el amarillo central corresponde al
promedio aritmético de todas las observaciones municipio-mes válidas de toda la
historia de la variable, con igual peso por observación y sin ponderar por superficie.
Mínimo, media y máximo se calculan por variable sobre el conjunto histórico completo
y quedan fijos al cambiar fecha, municipio, grupo o ventana temporal, incluso en
fechas sin observaciones. Cada mitad de la paleta interpola linealmente entre la
media histórica y su extremo. No se imputan faltantes. No es una media territorial
ponderada ni una anomalía temporal. La temperatura se representa siempre en °C
lineales, sin logaritmos. Las otras magnitudes usan el centro histórico en el
espacio de la transformación elegida, sin implicar umbrales de salud o ambientales.
Las etiquetas de la leyenda muestran unidades originales incluso al elegir
ln(1+x) o ln(1+1000x); el punto central aplica la inversa de esa escala. Las
descargas y tooltips nunca cambian. PM2.5 no representa categorías AQI.

Se utilizan rampas ordenadas por magnitud, siguiendo la distinción entre
esquemas secuenciales y divergentes de
[ColorBrewer](https://colorbrewer2.org/learnmore/schemes.html). Los colores
concretos son definiciones locales; no se afirma certificación universal de
percepción o daltonismo. Valor numérico, tabla y selección delineada permiten
explorar sin depender exclusivamente del color.

## EN

The map follows Agriculture C04's visual language with revision 08's fluid
dimensions, 14 px card corners and a map up to 1040 px high on large screens.
Map and detail stack on mobile, with a proportional map up to 520 px high.
The hero does not shrink the map. The original 339 geometries remain unchanged.

Each magnitude has an explicit palette: blue–yellow–red temperature,
brown–ochre–yellow–teal rainfall (low to high, without white), blue–yellow–red HKU, cream–orange–red burned area, ochre–green NDVI,
cream–teal EVI, cream–purple PM2.5 and blue–yellow–red Black Marble. Standard deviation
and IQR use sequential purple; temperature dispersion is not cold or warmth.

Ranges retain the original full-series minimum and maximum for each variable,
fixed across dates. For temperature, the yellow midpoint is the arithmetic mean
of all valid municipality-month observations throughout the variable's complete
history. Every observation has equal weight, with no area weighting. Minimum,
mean and maximum are computed separately for each variable over this complete
historical pool and remain fixed across dates, municipalities, groups and time
windows, even on dates without observations. Each half interpolates linearly
between this historical mean and its endpoint. No missing values are imputed;
this is neither an area-weighted national temperature nor a temporal anomaly.
Temperature always uses linear °C without logarithms. Other colour midpoints
use the historical mean in the selected transformed space, without implying
physical or health thresholds. Legend labels show original units even under logarithmic map scales.
Tooltips and downloads preserve the original observations. PM2.5 colours are
not AQI categories. Numeric values, a table and outlined selection complement
colour. These local palettes follow ordered mapping principles; no universal
colour-vision certification is claimed.

## Referencia histórica fija / Fixed historical reference

Temperatura media / Mean temperature: enero de 1990–mayo de 2026 / January
1990–May 2026; 148,143 observaciones / observations (339 municipios × 437 meses).
Mínimo / minimum: −10.538874725985497 °C; media / mean: 14.229732420680195 °C;
máximo / maximum: 31.972680036095653 °C. Cada indicador tiene su propio conjunto,
sin mezclar medias, mínimos, máximos o percentiles / Each indicator has its own
pool; means, minima, maxima and percentiles are not mixed together.

Reproducir solo metadatos visuales / Reproduce display metadata only:
`python -B scripts/update_temperature_pool.py`.
`code/run.py` genera la misma referencia durante la reconstrucción completa /
generates the same reference during full reconstruction. Valores finitos, sin
bit 8 de `qa_flags`; coberturas >1 retenidas con advertencia / Finite values,
no `qa_flags` bit 8; coverage >1 retained with warnings. Los maestros y descargas
no se modifican / Masters and downloads are unchanged.


## Actualizacion / Update: escala sincronizada

Por instruccion posterior del supervisor, la escala visual elegida se aplica al mapa, sparkline y spaghetti. Para luces nocturnas: ln(1000x+1), con paleta azul-amarillo-rojo. Las consultas conservan x e y; las descargas conservan x. Esta revision supersede las menciones anteriores a transformaciones solo del mapa. Ver nightlights-colours.md para fuentes NASA y detalles.

The selected visual transform now applies to the map, sparkline and spaghetti. Night lights default to ln(1000x+1), with blue/yellow/red colours. Readouts retain x and y; downloads retain original x. This supersedes earlier map-only display descriptions.
