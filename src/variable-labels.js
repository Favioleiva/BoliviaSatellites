window.C05_VARIABLE_LABELS={
  sum:['Suma de luces por municipio','Municipal sum of night lights'],sumsq:['Diagnóstico: suma de cuadrados (no es sum)','Diagnostic: sum of squares (not sum)'],mean0:['Diagnóstico: mean0 · definición pendiente','Diagnostic: mean0 · definition unverified'],
  count:['Conteo fuente','Source count'],nan:['Píxeles NaN · fuente','NaN pixels · source'],total_pixels:['Total de píxeles','Total pixels'],
  count_valid:['Píxeles válidos','Valid pixels'],count_invalid:['Píxeles inválidos','Invalid pixels'],count_zeros:['Píxeles con cero','Zero-valued pixels'],count_positive:['Píxeles positivos','Positive pixels'],
  prop_non_na_pixels:['Proporción de píxeles no nulos','Non-null pixel share'],zero_share:['Proporción de ceros','Zero share'],positive_share:['Proporción positiva','Positive share'],
  tile_count:['Teselas del municipio','Municipal tiles'],available_tile_count_day:['Teselas disponibles en el día','Available daily tiles'],missing_tile_count_day:['Teselas faltantes en el día','Missing daily tiles'],
  is_observed:['Indicador fuente: is_observed','Source flag: is_observed'],is_missing_due_to_tile:['Indicador fuente: falta de tesela','Source flag: missing tile']
};
window.C05_GROUP_LABELS={statistics:['Estadísticas fuente','Source statistics'],auxiliary:['Diagnósticos auxiliares · no son suma de luces','Auxiliary diagnostics · not the light sum'],pixels:['Diagnóstico: píxeles','Diagnostics: pixels'],coverage:['Diagnóstico: proporciones','Diagnostics: proportions'],tiles:['Diagnóstico: teselas','Diagnostics: tiles'],flags:['Indicadores de origen','Source flags']};
window.C05_UNITS_ES={
  'source radiance':'radiancia fuente','source radiance · scale unverified':'radiancia fuente · escala sin verificar',
  'sum of source pixel radiances · scale unverified':'suma de radiancias fuente · escala sin verificar',
  'sum of squared source radiances · scale unverified':'suma de radiancias fuente al cuadrado · escala sin verificar',
  'source mean0 · definition unverified':'mean0 fuente · definición sin verificar',pixels:'píxeles',tiles:'teselas',proportion:'proporción','source flag (0/1)':'indicador fuente (0/1)',dimensionless:'adimensional','mm/month':'mm/mes'
};
window.C05_VARIABLE_WARNINGS={
  sum:['Suma fuente: depende del área, la resolución y los píxeles válidos; no es energía total.','Source sum: depends on area, resolution and valid pixels; not total energy.'],
  sumsq:['Suma de cuadrados fuente conservada; no se recalcula ni certifica su escala.','Source sum of squares retained; its scale is neither recalculated nor certified.'],
  mean0:['mean0: definición pendiente; no equivale automáticamente a la media.','mean0: definition unresolved; not automatically equivalent to the mean.'],
  is_observed:['Indicador del archivo fuente; no certifica una observación directa sin relleno NASA.','Source-file flag; does not certify a direct observation without NASA filling.']
};
