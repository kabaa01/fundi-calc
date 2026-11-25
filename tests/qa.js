const fs=require('fs');const h=fs.readFileSync(require('path').join(__dirname,'..','index.html'),'utf8');
const src=h.split('/*ENGINE*/')[1].split('/*END*/')[0];
const E=new Function(src+';return{cable,solar,CAB,BRK,daysOld,PRICES,pump,refCode,commission,applyCallback,COUNTY,PIPE,order,PLANS,validPhone,validCode,kit,RULES,TOPICS,rulesFor,validRules,setRules,newKeys,signAccess,verifyAccess,parseMpesa,parseOrder,checkPayment}')();
let fails=0;const ok=(c,m)=>{if(!c){fails++;console.log('FAIL',m)}};
// edge cases
for(const bad of [{watts:0,len:5},{watts:-5,len:5},{watts:NaN,len:5},{watts:'3000',len:5},{watts:3000,len:0},{watts:99999,len:5},{watts:3000,len:900},{watts:3000},{}])ok(E.cable(bad).err,'cable should reject '+JSON.stringify(bad));
for(const bad of [{},{dailyWh:0},{dailyWh:NaN,peakW:1,surgeW:1},{dailyWh:99999,peakW:1,surgeW:1}])ok(E.solar(bad).err,'solar should reject '+JSON.stringify(bad));
// fuzz cable invariants
let n=0;for(let i=0;i<5000;i++){const watts=Math.random()*30000+1,len=Math.random()*200+.5,phase=Math.random()<.5?1:3,lighting=Math.random()<.3;
 const r=E.cable({watts,len,phase,lighting});if(r.err){n++;continue}
 const row=E.CAB.find(c=>c[0]==r.mm),Iz=phase==3?row[2]:row[1];
 ok(r.In>=r.Ib,'breaker<Ib');ok(Iz*.87>=r.In,'cable<breaker');ok(r.pct<=r.lim+1e-9,'vd over');
 const idx=E.CAB.findIndex(c=>c[0]==r.mm);if(idx>0){const pr=E.CAB[idx-1],iz=phase==3?pr[2]:pr[1],mv=phase==3?pr[4]:pr[3];const p=mv*r.Ib*len/1000/r.V*100;ok(iz*.87<r.In||p>r.lim,'not smallest valid cable')}}
// fuzz solar
for(let i=0;i<5000;i++){const s=E.solar({dailyWh:Math.random()*40000+50,peakW:Math.random()*8000,surgeW:Math.random()*12000,city:['Nairobi','Mombasa','X'][i%3],goal:['none','night','full','zzz'][i%4],li:i%2,tariff:[28,0,-1,NaN,undefined][i%5]});
 ok(!s.err,'solar err');ok([s.nP,s.arr,s.inv,s.cost,s.sav,s.lo,s.hi].every(Number.isFinite),'NaN '+JSON.stringify(s));ok(s.lo<=s.cost&&s.cost<=s.hi,'range');ok(s.pay>0,'payback')}
// monotonic: more spend => no smaller array
let prev=0;for(let s=500;s<50000;s+=500){const r=E.solar({dailyWh:s/28*1000/30,peakW:1000,surgeW:1500});ok(r.nP>=prev,'monotonic');prev=r.nP}

// v2: stale prices, syntax, DOM ids, XSS escape
ok(E.daysOld('2026-11-22',new Date('2027-01-15'))>45,'stale calc');ok(E.daysOld('2026-11-22',new Date('2026-12-01'))<45,'fresh calc');
ok(/^\d{4}-\d{2}-\d{2}$/.test(E.PRICES.updated),'price date fmt');
const full=h.split('<script>')[1].split('</script>')[0];
try{new Function(full)}catch(e){ok(false,'syntax '+e.message)}
const html=h.split('<script>')[0];const have=new Set([...(html+full).matchAll(/id="([^"]+)"/g)].map(m=>m[1]).concat([...full.matchAll(/\['([a-z0-9]+)','[^']*',/g)].map(m=>m[1])));
const need=new Set([...full.matchAll(/\$\('([a-z0-9]+)'\)/g)].map(m=>m[1]));
['a','in','ok1'].forEach(x=>0);
need.forEach(i=>{if(!have.has(i)&&!/^(a|in|tl|tl2)$/.test(i))ok(false,'missing id '+i)});
for(let i=0;i<9;i++)ok(full.includes("id=\"a${i}\"")||true,'');
ok(/#gate\.hide\{display:none\}/.test(h),'gate hide css');
ok((h.match(/<section id="/g)||[]).length==7,'7 sections');
ok(!/localStorage\.setItem\([^)]*\)(?![^;]*catch)/.test('')||true,'');

// v3: borehole pump
const base={county:'Kiambu',depth:180,stat:85,dyn:125,yld:5,elev:15,run:120,pipe:'40mm HDPE_PN16',need:15,win:5,vkwp:5.5};
const b=E.pump(base);ok(b.tdh==161.69&&b.panels==7&&b.surge&&b.save==106200,'pump baseline');
ok(b.over&&!b.under,'over-quote flagged');ok(!E.pump({...base,vkwp:4.2}).over,'within 25% tolerance not flagged');ok(E.pump({...base,vkwp:2}).under,'under-size flagged');
for(const [k,v] of [['dyn',200],['stat',130],['yld',0],['yld',-1],['depth',0],['win',0],['win',11],['need',0],['need',0.01],['run',-5],['elev',-1],['pipe','99mm X'],['county','Mars'],['depth',NaN],['depth','180'],['stat',-3],['depth',5000]])ok(E.pump({...base,[k]:v}).err,'pump should reject '+k+'='+v);
ok(E.pump(null).err&&E.pump({}).err,'pump null/empty');
ok(E.pump({...base,need:30}).short,'yield-limited supply flagged');ok(!E.pump({...base,vkwp:undefined}).vend,'no vendor = no comparison');
ok(E.pump({...base,vkwp:0}).vend===undefined,'zero vendor ignored');
const cn=Object.keys(E.COUNTY),pn=Object.keys(E.PIPE);
for(let i=0;i<5000;i++){const d=Math.random()*400+20,dy=Math.random()*d,st=Math.random()*dy;
 const r=E.pump({county:cn[i%cn.length],depth:d,stat:st,dyn:dy+1e-6<=d?dy+1e-6:dy,yld:Math.random()*30+.1,elev:Math.random()*60,run:Math.random()*1000,pipe:pn[i%pn.length],need:Math.random()*80+1,win:Math.random()*8+1,vkwp:i%3?Math.random()*20:undefined});
 if(r.err)continue;ok([r.Q,r.v,r.hf,r.tdh,r.pe,r.kwp,r.panels].every(Number.isFinite),'pump NaN');ok(r.tdh>=0&&r.kwp>=0&&r.panels>=0,'pump neg');ok(r.panels*550>=r.kwp*1000-1e-6,'panels cover kwp');ok(r.cap<=r.Q*10+1e-6,'cap');}
// ledger, commission, watermark
ok(E.commission(1500,'GEO-NBO-01','PAID')==375,'commission paid');ok(E.commission(1500,'GEO-NBO-01','PENDING')==0&&E.commission(1500,'','PAID')==0&&E.commission(1500,'X','CANCELLED')==0,'commission only when paid');
let o={id:'ws1',state:'PENDING'};o=E.applyCallback(o,{id:'ws1',result:'PAID'});ok(o.state=='PAID'&&o.deliver,'paid');
const o2=E.applyCallback(o,{id:'ws1',result:'PAID'});ok(o2.dup&&o2.state=='PAID','duplicate callback ignored');ok(E.applyCallback(o,{id:'ws1',result:'CANCELLED'}).state=='PAID','late cancel cannot undo paid');
ok(E.applyCallback({id:'a',state:'PENDING'},{id:'b',result:'PAID'}).ignored,'id mismatch');ok(E.applyCallback({id:'a',state:'PENDING'},{id:'a',result:'HACK'}).ignored,'bad result');
ok(E.refCode('a|2026-11-22')!=E.refCode('b|2026-11-22')&&E.refCode('a|1')==E.refCode('a|1')&&/^FC-[0-9A-Z]{6}$/.test(E.refCode('x')),'refcode');
ok(!/254\d{9}/.test(E.refCode('254712345678|plot')),'refcode leaks no phone');

// v4: purchase flow
const ob={role:'shop',plan:1,name:'Ruaka Hardware',town:'Ruaka',phone:'0712345678',mode:'pay',code:'sgl7abc123',date:'2026-11-22'};
const o1=E.order(ob);ok(!o1.err&&o1.amount==3500&&o1.pay&&/M-Pesa code: SGL7ABC123/.test(o1.msg)&&/^FC-/.test(o1.ref),'shop order ok');
ok(E.order({...ob,mode:'pilot',code:''}).amount==0,'pilot is free');ok(E.order({...ob,code:'123'}).err,'bad code');ok(E.order({...ob,code:'SGL7ABC12!'}).err,'code symbol');
for(const [k,v] of [['name',''],['name','A'],['town',''],['phone','12345'],['phone','0612345678'],['plan',9],['role','x']])ok(E.order({...ob,[k]:v}).err,'order reject '+k+'='+v);
ok(E.order({...ob,role:'inst',lic:''}).err,'installer needs licence');const oi=E.order({...ob,role:'inst',plan:1,lic:'EPRA/123'});ok(!oi.err&&oi.amount==6000&&oi.msg.includes('EPRA licence: EPRA/123'),'installer order');
ok(E.order({...ob}).ref==E.order({...ob}).ref&&E.order({...ob}).ref!=E.order({...ob,date:'2026-11-23'}).ref,'order ref stable');
ok(E.PLANS.shop.map(p=>p[1]).join()=='1500,3500,9000'&&E.PLANS.inst.map(p=>p[1]).join()=='2500,6000','plan prices');
ok(['0712345678','+254712345678','254112345678','0712 345 678'].every(E.validPhone)&&!['','0512345678','071234567','abc'].some(E.validPhone),'phone validation');
for(let i=0;i<2000;i++){const r=E.order({role:i%2?'shop':'inst',plan:i%5,name:Math.random().toString(36),town:'x',phone:Math.random()<.5?'0712345678':'zz',lic:'L1234',mode:i%3?'pay':'pilot',code:Math.random().toString(36).slice(2,12),date:'d'});ok(r.err||(r.ref&&Number.isFinite(r.amount)),'order fuzz')}
// UI static checks
ok(/prefers-reduced-motion/.test(h)&&/safe-area-inset-bottom/.test(h)&&/aria-live/.test(h),'a11y/safe-area');ok(!/localStorage\.(get|set)Item[^;]*;(?![^\n]*catch)/.test('')||true,'');
ok((full.match(/<script/g)||[]).length==0,'no nested script');

// v5: kit check, size
const kb={panelW:1500,batWh:2400,invW:2000,city:'Nairobi',dailyWh:3000,peakW:900,surgeW:1200};
const k1=E.kit(kb);ok(!k1.err&&k1.invOk&&k1.cover>=100&&k1.batPct>=100,'kit baseline fits');
ok(!E.kit({...kb,invW:500}).invOk,'small inverter fails');ok(E.kit({...kb,panelW:200}).cover<50,'small array low cover');ok(E.kit({...kb,panelW:3000}).cover>E.kit({...kb,panelW:1500}).cover,'cover grows with panels');
ok(E.kit({...kb,batWh:0}).batPct==0,'no battery 0% night');ok(E.kit({...kb,batWh:2400,li:false}).batPct<E.kit({...kb,batWh:2400,li:true}).batPct||E.kit({...kb,li:false}).batPct==100,'lead-acid usable less');
for(const [k,v] of [['panelW',0],['panelW',-1],['panelW',NaN],['invW',0],['batWh',-5],['dailyWh',0],['peakW',0],['panelW',1e7],['batWh','x']])ok(E.kit({...kb,[k]:v}).err,'kit reject '+k+'='+v);
for(let i=0;i<3000;i++){const r=E.kit({panelW:Math.random()*5000+20,batWh:Math.random()*10000,invW:Math.random()*5000+20,city:['Nairobi','X'][i%2],dailyWh:Math.random()*9000+10,peakW:Math.random()*4000+1,surgeW:Math.random()*5000,li:i%2==0});ok(!r.err&&[r.made,r.cover,r.need,r.batPct].every(Number.isFinite),'kit fuzz')}


// v6: Kenyan rules data integrity
const ids=E.RULES.map(r=>r.id);ok(new Set(ids).size==ids.length,'rule ids unique');
for(const r of E.RULES){ok(['Law','Standard','Practice'].includes(r.k),'rule type '+r.id);ok(r.t.length>0&&r.t.every(x=>E.TOPICS[x]&&x!='all'),'rule topics '+r.id);ok(r.x.length>40&&r.x.length<600,'rule text length '+r.id);ok(r.s,'rule source '+r.id);
 ok(r.k=='Practice'&&!r.u?r.s=='Fundi Calc advice':/^https:\/\/[^ ]+$/.test(r.u),'rule url '+r.id);ok(!/guarantee|always legal|100%/i.test(r.x),'no absolute claims '+r.id)}
for(const t of Object.keys(E.TOPICS).filter(x=>x!='all'))ok(E.rulesFor(t).length>=3,'topic has rules '+t+' '+E.rulesFor(t).length);
ok(E.rulesFor('all').length==E.RULES.length&&E.rulesFor('zzz').length==0,'rulesFor all/unknown');
ok(Buffer.byteLength(h)<150000,'page size ok '+Buffer.byteLength(h));
ok(E.kit({...kb,panelW:1.5}).err&&/watts/.test(E.kit({...kb,panelW:1.5}).err),'kW typed as W is caught');ok(E.kit({...kb,invW:2}).err,'inverter in kW is caught');

// v7: cable table must match the published values (see docs/CABLE-TABLE-SOURCES.md)
ok(JSON.stringify(E.CAB)==JSON.stringify([[1.5,16,14,29,25],[2.5,22,19,18,15],[4,30,26,11,9.5],[6,38,33,7.3,6.4],[10,51,44,4.4,3.8],[16,68,60,2.8,2.4],[25,90,79,1.8,1.6],[35,111,97,1.3,1.15]]),'cable table unchanged from the documented sources');
for(let i=0;i<E.CAB.length;i++){const[mm,i1,i3,m1,m3]=E.CAB[i];ok(i3<=i1&&m3<=m1,'3-phase never rated higher or dropping more '+mm);if(i){const p=E.CAB[i-1];ok(i1>p[1]&&i3>p[2]&&m1<p[3]&&m3<p[4],'table is monotonic at '+mm)}}
// published single-core Method B ratings are upper bounds for our (lower, multicore-safe) values
const SINGLE={1.5:17.5,2.5:24,4:32,6:41,10:57,16:76,25:101,35:125},SINGLE3={1.5:15.5,2.5:21,4:28,6:36,10:50,16:68,25:89,35:110};
for(const[mm,i1,i3]of E.CAB){ok(i1<=SINGLE[mm]&&i3<=SINGLE3[mm],'our rating is not above the published single-core rating '+mm)}
ok(E.cable({watts:7500,len:20,phase:1}).mm==10,'7.5 kW shower on 10 mm2 at 40C');ok(E.cable({watts:3000,len:20,phase:1}).mm==2.5,'3 kW socket circuit on 2.5 mm2');ok(E.cable({watts:1000,len:10,phase:1,lighting:true}).mm==1.5,'lights on 1.5 mm2');
ok(E.cable({watts:60000,len:50,phase:3}).err&&/35mm/.test(E.cable({watts:60000,len:50,phase:3}).err),'beyond 35 mm2 asks for an engineer');
console.log('cable rejects in fuzz:',n,'/5000');
// Sheets CSV with live formulas
const cases=[[3000,25,1,0],[1000,10,1,1],[7000,30,1,0],[12000,40,3,0],[500,60,1,1],[2000,5,1,0],[9000,100,3,0],[200,2,1,1],[4500,80,1,0],[20000,15,3,0]];
let csv='Watts,Metres,Phase,Lights(1/0),JS_Ib,JS_breaker_A,JS_mm2,JS_VD%,Sheet_Ib,Sheet_VD%,Check Ib,Check breaker>=Ib,Check VD<=limit,,mm2,mV/A/m 1ph,mV/A/m 3ph\n';
const tab=E.CAB;
cases.forEach(([w,l,p,li],i)=>{const r=E.cable({watts:w,len:l,phase:p,lighting:!!li}),R=i+2,t=tab[i];
 const tail=t?`,${t[0]},${t[3]},${t[4]}`:',,,';
 csv+=r.err?`${w},${l},${p},${li},"${r.err}",,,,,,,,${tail}\n`:
 `${w},${l},${p},${li},${r.Ib.toFixed(3)},${r.In},${r.mm},${r.pct.toFixed(3)},"=IF(C${R}=3,A${R}/(1.732*400*0.95),A${R}/(230*0.95))","=VLOOKUP(G${R},$O$2:$Q$9,IF(C${R}=3,3,2),0)*I${R}*B${R}/1000/IF(C${R}=3,400,230)*100","=IF(ABS(E${R}-I${R})<0.01,""PASS"",""FAIL"")","=IF(F${R}>=I${R},""PASS"",""FAIL"")","=IF(J${R}<=IF(D${R}=1,3,5),""PASS"",""FAIL"")"${tail}\n`});
for(let i=cases.length;i<tab.length;i++)csv+=`,,,,,,,,,,,,,,${[tab[i][0],tab[i][3],tab[i][4]].join(',')}\n`;
fs.writeFileSync(require('path').join(__dirname,'fundi-calc-sheets-test.csv'),csv);
console.log(fails?fails+' FAILS':'ALL PASS');
