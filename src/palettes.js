/* Local, explicit colour definitions. These affect map paint only, never data. */
window.C05_PALETTES = {
  temperature: {name:['Temperatura: frío → intermedio → calor','Temperature: cold → intermediate → warm'],stops:['#2446a8','#55a9df','#fff3a1','#f59a52','#b82435']},
  rain: {name:['Precipitación: marrón = poca lluvia → verde azulado = mucha lluvia','Precipitation: brown = low rainfall → teal = high rainfall'],stops:['#a65e2e','#d89b45','#e5d879','#62b6a3','#087e8b']},
  hku: {name:['Luces mensuales: azul bajo → rojo alto','Monthly lights: blue low → red high'],stops:['#2446a8','#55a9df','#fff3a1','#f59a52','#b82435']},
  fire: {name:['Área quemada: menor → mayor','Burned area: lower → higher'],stops:['#fff1d2','#ffc16b','#f27a3e','#c53d32','#761d30']},
  ndvi: {name:['NDVI: menor → mayor','NDVI: lower → higher'],stops:['#9d7044','#d5be83','#e4ecc0','#7cbb7b','#1e6f46']},
  evi: {name:['EVI: menor → mayor','EVI: lower → higher'],stops:['#f2efc5','#bcdfa7','#6ac2a1','#288c82','#155354']},
  pm25: {name:['PM2.5: menor → mayor · sin categorías sanitarias','PM2.5: lower → higher · no health categories'],stops:['#fff0d1','#e8b987','#c77a84','#925081','#512c71']},
  blackmarble: {name:['Luces diarias: azul bajo → rojo alto','Daily lights: blue low → red high'],stops:['#2446a8','#55a9df','#fff3a1','#f59a52','#b82435']},
  diagnostics: {name:['Diagnóstico fuente: menor → mayor','Source diagnostic: lower → higher'],stops:['#edf1ed','#b7c9c2','#7d9e96','#476e69','#234947']},
  dispersion: {name:['Dispersión espacial: menor → mayor','Spatial dispersion: lower → higher'],stops:['#eee8fa','#c4b2df','#967ebd','#6d4e9a','#45256e']}
};
window.C05_paletteFor = function(product,native) {
  if(['count','nan','total_pixels','count_valid','count_invalid','count_zeros','count_positive','prop_non_na_pixels','zero_share','positive_share','tile_count','available_tile_count_day','missing_tile_count_day','is_observed','is_missing_due_to_tile'].includes(native))return 'diagnostics';
  if(['hku','blackmarble'].includes(product))return product;
  if(/_(stddev|std|iqr)$/.test(native)||native==='std')return 'dispersion';
  if(product==='vegetation')return native.startsWith('evi')?'evi':'ndvi';
  return ({era5:'temperature',gpm:'rain'})[product]||product;
};
window.C05_colourAt = function(palette,t) {
  const stops=window.C05_PALETTES[palette].stops.map(h=>[1,3,5].map(i=>parseInt(h.slice(i,i+2),16)));
  const u=Math.max(0,Math.min(1,t))*(stops.length-1),i=Math.min(stops.length-2,Math.floor(u)),f=u-i;
  return `rgb(${stops[i].map((x,k)=>Math.round(x+(stops[i+1][k]-x)*f)).join(',')})`;
};
