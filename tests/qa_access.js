const fs=require('fs'),path=require('path');
const h=fs.readFileSync(path.join(__dirname,'..','index.html'),'utf8');
const src=h.split('/*ENGINE*/')[1].split('/*END*/')[0];
const E=new Function(src+';return{order,PLANS,PILOT_DAYS,RULES,validRules,setRules,rulesFor,newKeys,signAccess,verifyAccess,parseMpesa,parseOrder,checkPayment,b64u}')();
let fails=0;const ok=(c,m)=>{if(!c){fails++;console.log('FAIL',m)}};
const syl=w=>{w=w.toLowerCase().replace(/[^a-z]/g,'');if(w.length<=3)return 1;w=w.replace(/(?:[^laeiouy]es|ed|[^laeiouy]e)$/,'').replace(/^y/,'');return(w.match(/[aeiouy]{1,2}/g)||[1]).length};
const grade=t=>{const s=t.split(/[.!?]+\s/).filter(x=>x.trim()).length||1,w=t.split(/\s+/).filter(Boolean),sy=w.reduce((a,x)=>a+syl(x),0);return .39*w.length/s+11.8*sy/w.length-15.59};
(async()=>{
const K=await E.newKeys(),K2=await E.newKeys(),T='2026-11-22';
const claims={r:'FC-ABC123',n:'Ruaka Hardware',w:'254712345678',p:'Shop',k:'shop',l:'',e:'2026-12-22',i:T};
const tok=await E.signAccess(claims,K.priv);
let r=await E.verifyAccess(tok,K.pub,T);ok(r.ok&&r.claims.n==='Ruaka Hardware','valid code accepted');
ok((await E.verifyAccess(tok,K2.pub,T)).err,'wrong key rejected');
const p=tok.split('.');const tam=[p[0],E.b64u.enc(new TextEncoder().encode(JSON.stringify({...claims,e:'2099-01-01'}))),p[2]].join('.');
ok((await E.verifyAccess(tam,K.pub,T)).err,'tampered claims rejected');
ok((await E.verifyAccess(tok+'x',K.pub,T)).err,'tampered signature rejected');
for(const bad of ['','abc','FC1.a.b','FC2.'+p[1]+'.'+p[2],null,undefined,'FC1..'])ok((await E.verifyAccess(bad,K.pub,T)).err,'malformed rejected: '+bad);
ok((await E.verifyAccess(tok,null,T)).err==='Access codes are not set up yet.','no public key');
const exp=await E.signAccess({...claims,e:'2026-11-01'},K.priv);r=await E.verifyAccess(exp,K.pub,T);ok(r.expired&&r.err&&/ran out/.test(r.err),'expired code flagged');
ok((await E.verifyAccess(await E.signAccess({...claims,e:'2026-11-22'},K.priv),K.pub,T)).ok,'valid on last day');
ok((await E.verifyAccess(await E.signAccess({...claims,k:'admin'},K.priv),K.pub,T)).err,'bad role rejected');
ok((await E.verifyAccess(await E.signAccess({...claims,e:'soon'},K.priv),K.pub,T)).err,'bad date rejected');
// M-Pesa parsing
const sms=`SGL7ABC123 Confirmed. You have received Ksh3,500.00 from JOHN KAMAU 254712345678 on 22/11/26 at 10:15 AM. Account balance is Ksh9,000.00.
QHA1XYZ999 Confirmed. Ksh1,500.00 received from MARY WANJIRU 0722111222 on 22/11/26 at 11:00 AM.
random text without a code`;
const pm=E.parseMpesa(sms);ok(pm.length==2&&pm[0].code=='SGL7ABC123'&&pm[0].amount==3500&&pm[1].amount==1500&&pm[0].from=='JOHN KAMAU','parse two messages');
ok(E.parseMpesa('hello').length==0&&E.parseMpesa('').length==0&&E.parseMpesa(null).length==0,'parse junk');
ok(E.parseMpesa('abc ABCDEFGH12 Confirmed. nothing').length==0,'no amount = ignored');
// order <-> check
const ob={role:'shop',plan:1,name:'Ruaka Hardware',town:'Ruaka',phone:'0712345678',mode:'pay',code:'sgl7abc123',date:T};
const om=E.order(ob).msg,po=E.parseOrder(om);ok(po&&po.role=='shop'&&po.plan=='Shop'&&po.name=='Ruaka Hardware'&&po.code=='SGL7ABC123'&&po.paid==3500,'order roundtrip');
let c=E.checkPayment(om,sms,[]);ok(c.ok,'payment ok: '+c.reasons);
ok(!E.checkPayment(om,sms.replace('3,500.00','2,000.00'),[]).ok,'short payment refused');
ok(!E.checkPayment(om,'QHA1XYZ999 Confirmed. Ksh9,999.00 received from A B 0722111222',[]).ok,'code not in till refused');
ok(!E.checkPayment(om,sms,['SGL7ABC123']).ok,'reused code refused');
ok(!E.checkPayment('hello',sms,[]).ok,'non-order refused');
const oi=E.order({...ob,role:'inst',plan:0,lic:'EPRA/T2/123',code:'QHA1XYZ999'}).msg;
c=E.checkPayment(oi,sms,[]);ok(!c.ok&&c.reasons.some(x=>/plan costs KES 2500/.test(x)),'installer plan needs KES 2500');
c=E.checkPayment(E.order({...ob,role:'inst',plan:0,lic:'EPRA/T2/123',code:'SGL7ABC123'}).msg,sms,[]);ok(c.ok,'installer paid ok (3500 >= 2500)');
const pil=E.checkPayment(E.order({...ob,mode:'pilot',code:''}).msg,'',[]);ok(pil.ok&&pil.pilot,'pilot needs no payment');
ok(!E.checkPayment(om.replace('Plan: Shop','Plan: Gold'),sms,[]).ok,'unknown plan refused');
const pms=E.order({role:'shop',plan:1,name:'Ruaka Hardware',town:'Ruaka',phone:'0712345678',mode:'pilot',date:'2026-11-24'}).msg,pi=E.order({role:'inst',plan:0,name:'Sunrise Ltd',town:'Nakuru',phone:'0722111222',lic:'EPRA/T2/5',mode:'pilot',date:'2026-11-24'}).msg;
ok(/Request: free 3-day pilot/.test(pms)&&E.parseOrder(pms).pilot,'shop pilot is 3 days');ok(/Request: free 30-day pilot/.test(pi)&&E.parseOrder(pi).pilot,'installer pilot stays 30 days');ok(E.PILOT_DAYS.shop===3&&E.PILOT_DAYS.inst===30,'pilot days table');
// live rules
ok(E.validRules(E.RULES),'built-in rules valid');
const good=E.RULES.map(x=>({...x}));ok(E.setRules(good)&&E.rulesFor('all').length==good.length,'live rules applied');
const badSets=[[],null,'x',good.map((x,i)=>i?x:{...x,u:'http://evil.example'}),good.map((x,i)=>i?x:{...x,u:'javascript:alert(1)'}),good.map((x,i)=>i?x:{...x,k:'Rumour'}),good.map((x,i)=>i?x:{...x,t:['nope']}),good.map((x,i)=>i?x:{...x,x:'short'})];
badSets.forEach((b,i)=>ok(!E.validRules(b),'bad rules set rejected #'+i));
ok(E.rulesFor('all').length==good.length,'bad set did not replace good');
// rules.json and the copy inside index.html must agree
const rj=JSON.parse(fs.readFileSync(path.join(__dirname,'..','rules.json'),'utf8'));ok(E.validRules(rj.rules)&&JSON.stringify(rj.rules)===JSON.stringify(E.RULES),'rules.json matches the copy inside index.html');ok(/^\d{4}-\d{2}-\d{2}$/.test(rj.checked),'rules.json has a checked date');
// plain language
const gs=E.RULES.map(x=>grade(x.x)),avg=gs.reduce((a,b)=>a+b,0)/gs.length;
console.log('reading grade: avg',avg.toFixed(1),'max',Math.max(...gs).toFixed(1));
ok(avg<=8.5,'rules average reading grade '+avg.toFixed(1)+' <= 8.5');
E.RULES.forEach((x,i)=>ok(gs[i]<=11.5,'rule too hard to read: '+x.id+' grade '+gs[i].toFixed(1)));
ok(!E.RULES.some(x=>/kWp|abstraction|hydrogeolog.*abstraction|Standardization Mark/i.test(x.x)),'no hard jargon in rules');
console.log(fails?fails+' FAILS (access)':'ACCESS TESTS ALL PASS');process.exit(fails?1:0)})();
