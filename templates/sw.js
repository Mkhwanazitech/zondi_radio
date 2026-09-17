self.addEventListener('install', e=>self.skipWaiting());
self.addEventListener('activate', e=>self.clients.claim());

// Keep syncing every 2 sec in background
let lastPos = null;
self.addEventListener('message', e=>{
  if(e.data.type==='LOCATION'){
    lastPos = e.data.pos;
    // store for when app opens
    self.clients.matchAll().then(clients=>{
      clients.forEach(c=>c.postMessage({type:'BG_LOCATION', pos:lastPos}));
    });
  }
});

setInterval(()=>{
  if(lastPos){
    fetch('/api/bg-ping', {
      method:'POST',
      body: JSON.stringify(lastPos),
      headers:{'Content-Type':'application/json'}
    }).catch(()=>{});
  }
}, 2000);
