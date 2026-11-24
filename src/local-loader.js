/* Local file capsules: loaded selectively, with the same gzip bytes as HTTP. */
(()=>{
  const requests=new Map();
  window.BoliviaSatellitesData={receive(key,value){const pending=requests.get(key);if(!pending)return;requests.delete(key);clearTimeout(pending.timer);pending.element.remove();pending.resolve(value)}};
  window.loadLocalCapsule=key=>{
    if(requests.has(key))return requests.get(key).promise;
    const element=document.createElement('script');element.async=true;
    let resolve,reject;const promise=new Promise((yes,no)=>{resolve=yes;reject=no});
    const fail=()=>{requests.delete(key);element.remove();reject(Error('Archivo local no disponible / Local file unavailable: '+key))};
    const timer=setTimeout(fail,30000);element.onerror=()=>{clearTimeout(timer);fail()};
    requests.set(key,{resolve,reject,promise,element,timer});
    element.src='../Offline/'+key+'.js';document.head.append(element);return promise;
  };
  window.addEventListener('error',()=>{const e=document.getElementById('startupStatus');if(e&&!window.__ready){e.hidden=false;e.textContent='No se pudo iniciar. Conserve juntas las carpetas dist y Offline. / Unable to start. Keep the dist and Offline folders together.'}});
})();
