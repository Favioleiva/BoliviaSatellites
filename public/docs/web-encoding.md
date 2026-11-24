# Exact web encoding / Codificación exacta

Black Marble: gzip → header `C05SHF02` (8 ASCII bytes) → row count and column
count (two little-endian uint32 values) → byte-shuffled Float64 payload.
Columns are stored consecutively; byte lanes 0 through 7 are grouped before
compression. Decoding reverses byte order grouping and column layout using
integer bit copies. No rounding, quantisation or numerical transformation.
Python implementation: `code/webcodec.py`. Browser implementation: `src/worker.js`.

Monthly **transport** blocks contain the original daily rows for 339 municipalities,
including source missing values. The catalogue lists daily periods, and the
application selects the precise daily slice. This is not monthly aggregation.
Municipal series contain all 23 fields plus QA, coverage and source pixel count,
loaded only for the selected municipality. Distribution/LOD chunks remain
separate by variable and territorial group. The other six products retain
the original exact Float64 gzip representation.

Las cápsulas `Offline` codifican los mismos gzip en base64 para permitir acceso
por archivo local. El script verifica la igualdad de bytes originales tras
decodificarlas. No se cargan todos los archivos en memoria. Los bloques mensuales
de Black Marble conservan observaciones diarias; no son promedios mensuales.

Revision 11: el supervisor autoriza **300 MiB** para el total de dist. El
candidato con 23 campos (~287 MiB) cabe sin modificar sus datos. Los ZIP conservan
el limite de 250 MiB por asset, distinto del presupuesto total. / Revision 11
authorizes a **300 MiB** total dist budget; the ~287 MiB candidate retains all
original fields and bytes. ZIP assets remain below 250 MiB each.
