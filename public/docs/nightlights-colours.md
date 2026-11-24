# Decision vigente / Current decision

El supervisor rechazo la propuesta ambar inspirada en NASA y solicito expresamente la misma paleta de temperatura: azul para valores bajos, amarillo intermedio y rojo para valores altos, tanto para HKU como Black Marble. Esta decision sustituye la propuesta documentada debajo. La serie derecha conserva ln(1000x+1) y usa el mismo gradiente por valor; las descargas permanecen crudas.

The supervisor rejected the NASA-inspired amber proposal and explicitly selected the temperature palette: blue for low values, yellow in the middle, red for high values, for both HKU and Black Marble. This supersedes the proposal below. The right-hand series keeps ln(1000x+1), using the same value-based gradient. Downloads remain raw.

## Referencia de la propuesta descartada / Rejected proposal reference

# Luces nocturnas: color y escala / Night lights: colour and scale

Revisión solicitada por el supervisor: eliminar el morado y representar
`ln(1000x + 1)` tanto en el mapa como en la serie del panel derecho. Los
spaghetti plots comparten la misma escala visual. Las descargas permanecen crudas.

Se adopta una rampa oscura → ámbar → amarillo claro, inspirada en el tratamiento
amarillo de las luces de [NASA Earth at Night](https://www.nasa.gov/wp-content/uploads/2019/11/earth_at_night_508.pdf)
y sus [mapas Black Marble](https://science.nasa.gov/earth/earth-observatory/earth-at-night/maps/).
NASA explica el uso de luces teñidas de amarillo sobre un fondo nocturno.
Los hex concretos son una adaptación local para polígonos municipales; no se
presentan como una paleta cuantitativa oficial NASA ni como colores naturales.

Se evita confundir este mapa de una magnitud con el
[compuesto azul/amarillo DNB + M15](https://science.data.nasa.gov/disasters/data-gallery/black-marble-blue-yellow):
ese compuesto combina bandas y utiliza azul para nubes. Esta aplicación no
dispone de esa composición ni está representando nubosidad.

`y = ln(1000x + 1)` utiliza logaritmo natural. Es una transformación visual
monótona del valor fuente, no una nueva estimación ni corrección de escala física.
Los ejes de las series muestran `y`; consultas muestran `x` e `y`; las descargas
conservan `x`. La leyenda cartográfica conserva etiquetas en unidades originales
y señala la transformación. Ceros se representan en y=0 y faltantes siguen
siendo faltantes. Un dominio inválido impide habilitar esa transformación.

Las bandas del spaghetti son percentiles calculados en los valores fuente y
dibujados en la escala elegida; no se recalculan como percentiles interpolados
de logaritmos, ni se presentan como intervalos de confianza.

## English

Night lights use dark → amber → pale yellow, inspired by NASA's yellow-tinted
Black Marble presentation. The actual hex values are a local municipal-map
adaptation, not an official quantitative NASA palette or true-colour imagery.
The DNB + M15 blue/yellow cloud composite is a different product and is not
recreated here.

The default natural-log display is `y = ln(1000x + 1)` for both maps and time
series. Axes display y, readouts retain both x and y, and downloads retain the
original x. Missing values are preserved and zeros map to zero. Distribution
bands show original-data quantiles through the same visual transform. This
does not verify the pending source radiance scale or define mean0.
