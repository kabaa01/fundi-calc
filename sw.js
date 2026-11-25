// Lets the app open with no signal after the first visit.
// Pages and the app: show the saved copy at once, refresh it in the background.
// rules.json and config.json: try the network for 4 seconds, then use the saved copy.
const V='fundi-calc-v2';
self.addEventListener('install',e=>{e.waitUntil(caches.open(V).then(c=>Promise.allSettled(['./','index.html','rules.json','config.json'].map(u=>c.add(new Request(u,{cache:'reload'}))))).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==V).map(x=>caches.delete(x)))).then(()=>self.clients.claim()))});
const net=r=>fetch(r).then(res=>{if(res.ok){const cp=res.clone();caches.open(V).then(c=>c.put(r,cp))}return res});
self.addEventListener('fetch',e=>{const r=e.request,u=new URL(r.url);
 if(r.method!=='GET'||u.origin!==location.origin)return;
 if(/\.json$/.test(u.pathname)){
  e.respondWith(Promise.race([net(r),new Promise((_,no)=>setTimeout(no,4000))]).catch(()=>caches.match(r,{ignoreSearch:true})).then(m=>m||net(r)));
 }else{
  e.respondWith(caches.match(r,{ignoreSearch:true}).then(m=>{const n=net(r).catch(()=>m);if(m){e.waitUntil(n.catch(()=>0));return m}return n}));
 }});
