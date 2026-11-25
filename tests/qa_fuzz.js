// Throws nothing, whatever you feed it. Garbage in, a clear message (or finite numbers) out.
const fs=require('fs'),path=require('path');
const h=fs.readFileSync(path.join(__dirname,'..','index.html'),'utf8');
const E=new Function(h.split('/*ENGINE*/')[1].split('/*END*/')[0]+';return{cable,solar,pump,kit,order,parseMpesa,parseOrder,checkPayment,verifyAccess,validRules,refCode,commission,applyCallback,daysOld}')();
const junk=[undefined,null,NaN,Infinity,-Infinity,0,-0,-1,1e308,1e-308,'','abc','1','<b>',{},[],[1],()=>1,true,false,'9'.repeat(5000),Symbol.iterator&&'x',BigInt?1:0].filter(x=>typeof x!=='bigint');
const R=()=>junk[Math.floor(Math.random()*junk.length)];
let fails=0;const ok=(c,m)=>{if(!c){fails++;console.log('FAIL',m)}};
const finiteOrErr=(r,n)=>{if(r==null||typeof r!=='object')return ok(false,n+' returned non-object');if(r.err)return;for(const[k,v]of Object.entries(r))if(typeof v==='number')ok(Number.isFinite(v)||v===Infinity&&k==='pay',n+' non-finite '+k)};
(async()=>{
for(let i=0;i<20000;i++){
 for(const[n,f]of[['cable',()=>E.cable({watts:R(),len:R(),phase:R(),lighting:R(),pf:R(),derate:R()})],['solar',()=>E.solar({dailyWh:R(),peakW:R(),surgeW:R(),city:R(),goal:R(),li:R(),tariff:R()})],
  ['pump',()=>E.pump({county:R(),depth:R(),stat:R(),dyn:R(),yld:R(),elev:R(),run:R(),pipe:R(),need:R(),win:R(),vkwp:R()})],['kit',()=>E.kit({panelW:R(),batWh:R(),invW:R(),city:R(),dailyWh:R(),peakW:R(),surgeW:R(),li:R()})],
  ['order',()=>E.order({role:R(),plan:R(),name:R(),town:R(),phone:R(),lic:R(),mode:R(),code:R(),date:R()})],['parseMpesa',()=>({n:E.parseMpesa(R()).length})],['parseOrder',()=>({n:E.parseOrder(R())})],
  ['checkPayment',()=>E.checkPayment(R(),R(),R())],['validRules',()=>({n:E.validRules(R())})],['refCode',()=>({n:E.refCode(R())})],['commission',()=>({n:E.commission(R(),R(),R())})],['applyCallback',()=>({n:E.applyCallback(R(),R())})]]){
  try{const r=f();if(['cable','solar','pump','kit'].includes(n))finiteOrErr(r,n)}catch(e){ok(false,n+' threw: '+String(e).slice(0,80));if(fails>20)process.exit(1)}}}
for(let i=0;i<500;i++)for(const a of[[R(),R(),R()],['FC1.'+R()+'.'+R(),{kty:'EC'},'2026-11-23'],[R(),null,R()]])try{const r=await E.verifyAccess(...a);ok(r&&typeof r==='object'&&(r.err||r.ok),'verify bad result')}catch(e){ok(false,'verifyAccess threw '+String(e).slice(0,80))}
const big='SGL7ABC123 Confirmed. Ksh1.00 from A B 0712345678. '.repeat(20000);let t=Date.now();E.parseMpesa(big);ok(Date.now()-t<3000,'parseMpesa 1 MB under 3 s: '+(Date.now()-t)+'ms');
console.log(fails?fails+' FAILS (fuzz)':'FUZZ ALL PASS');process.exit(fails?1:0)})();
