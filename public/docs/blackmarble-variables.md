# Indicador principal / Primary indicator

**sum = suma de luces por municipio / municipal sum of night lights.**
Es el indicador inicial de Black Marble. La representacion visual usa ln(1000*sum+1); el CSV conserva sum. **sumsq no es sum**: es la suma de cuadrados y se muestra solo en el grupo de diagnosticos auxiliares, junto a mean0. Ambos siguen presentes sin cambios en la fuente.

Black Marble opens on the original municipal sum, not sumsq. Its map and time series show ln(1000*sum+1); CSV downloads retain the raw sum. sumsq and mean0 are separate auxiliary diagnostics.

# Black Marble: variables fuente / Source variables

La revisión incorpora 23 campos numéricos originales: ocho estadísticas y
quince diagnósticos. No se calculan nuevas observaciones. Los maestros descargables
ya preservaban estas columnas; el selector anterior omitía 19 de ellas.

| Grupo / Group | Campos originales / Original fields |
|---|---|
| Estadísticas / Statistics | mean, median, min, max, sum, std, mean0, sumsq |
| Píxeles / Pixels | count, nan, total_pixels, count_valid, count_invalid, count_zeros, count_positive |
| Proporciones / Proportions | prop_non_na_pixels, zero_share, positive_share |
| Teselas / Tiles | tile_count, available_tile_count_day, missing_tile_count_day |
| Indicadores fuente / Source flags | is_observed, is_missing_due_to_tile |

`sum` es la suma fuente de valores de píxel: depende del tamaño del municipio,
la resolución y los píxeles válidos; no es energía total ni una intensidad
comparable automáticamente entre áreas distintas. `sumsq` conserva la suma de
cuadrados fuente, sin recalcularla. `mean0` se expone por su nombre original:
su definición exacta sigue sin verificar y no sustituye a `mean`. La escala
física de radiancia aplicada por el extractor permanece pendiente.

`is_observed` es un indicador del archivo fuente, no evidencia de observación
directa libre de relleno: la banda NASA utilizada es gap-filled. Conteos,
proporciones e indicadores son diagnósticos; no son intensidad luminosa.
No se crean p10, p25, p75 o p90, porque no existen como estadísticas distritales
en esta fuente. Los percentiles entre municipios del spaghetti son otra cosa.

Los campos `log_*` originales siguen disponibles en las descargas completas
como evidencia de origen, pero no se ofrecen como observaciones nuevas ni se
aplican a la descarga cruda. Las transformaciones elegibles del mapa siguen
siendo exclusivamente visuales. Identificadores, nombres, fechas y listas de
teselas se conservan en el maestro, sin tratarlos como indicadores numéricos.

## English

The selector now exposes 23 original numeric fields, grouped as eight source
statistics and fifteen diagnostics. The complete masters already retained these
columns. No new observations or district percentiles are invented.

`sum` is the source sum across pixels, sensitive to area, resolution and valid
pixel count; it is not total energy. `sumsq` retains the source sum of squares.
`mean0` remains explicitly unverified. The physical radiance scaling and original
extractor remain unresolved. Source flag `is_observed` must not be interpreted
as proof of direct observation: the NASA band is gap-filled. Counts and shares
are diagnostics, not light intensity. Original `log_*` fields remain in complete
source downloads, while logarithmic map options never replace raw downloads.
