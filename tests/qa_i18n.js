// Kiswahili data checks (no browser needed)
const fs=require('fs'),path=require('path');
const R=p=>fs.readFileSync(path.join(__dirname,'..',p),'utf8');
const h=R('index.html'),txt=R('i18n/sw.txt').split('\n');
let fails=0;const ok=(c,m)=>{if(!c){fails++;console.log('FAIL',m)}};
const e={},p=[];txt.forEach((l,i)=>{if(!l.trim()||l.startsWith('#'))return;const k=l.indexOf(' => ');ok(k>0,'line '+(i+1)+' has =>');if(k<0)return;const a=l.slice(0,k).trim(),b=l.slice(k+4).trim();ok(a&&b,'line '+(i+1)+' both sides filled');
 if(a.startsWith('re:')){try{new RegExp(a.slice(3).trim());p.push([a.slice(3).trim(),b])}catch(x){ok(false,'bad regex line '+(i+1))}}else{ok(!(a in e),'duplicate phrase '+a);e[a]=b}});
const emb=JSON.parse(h.slice(h.indexOf('/*SWD*/')+7,h.indexOf('/*ENDSWD*/')).replace(/<\\\//g,'</'));
ok(JSON.stringify(emb)===JSON.stringify({e,p}),'index.html holds exactly what i18n/sw.txt says (run node tools/sync-i18n.mjs)');
ok(JSON.stringify(JSON.parse(R('i18n/sw.json')))===JSON.stringify({e,p}),'i18n/sw.json is up to date');
// translations must not be identical to English (except names) and must keep numbers/placeholders
for(const[a,b]of Object.entries(e)){if(/[A-Za-z]{4}/.test(a)&&a===b&&!/^(Sample|Laptop|TV|Fundi Calc)/.test(a))ok(false,'not translated: '+a);const na=(a.match(/\d[\d,.]*\d|\d/g)||[]).join('|'),nb=(b.match(/\d[\d,.]*\d|\d/g)||[]).join('|');ok(na===nb||/^\d\. /.test(a),'numbers differ in: '+a.slice(0,50)+' ['+na+' vs '+nb+']')}
for(const[s,t]of p){const groups=new RegExp(s+'|').exec('').length-1;const used=[...t.matchAll(/[$~](\d)/g)].map(m=>+m[1]);ok(used.every(n=>n>=1&&n<=groups),'template uses a missing group: '+s.slice(0,50))}
// load the translator out of index.html and exercise it
const code=h.slice(h.indexOf('const SWD='),h.indexOf('const SWO='));const sw1=new Function(code+';return sw1')();
const T=(a,b)=>ok(sw1(a)===b,'sw1('+a.slice(0,40)+') = '+sw1(a).slice(0,60));
T('Saves about KES 3,000 a month','Inakuokolea takriban KES 3,000 kwa mwezi');T('  Get my quote ','  Pata nukuu yangu ');T('3 of 5 done. Do not pump yet.','3 kati ya 5 zimekamilika. Usisukume maji bado.');T('Fewer Fridge','Punguza Friji');T('More LED bulbs (10W)','Ongeza Balbu za LED (10W)');
T('Unlocked for Ruaka Hardware until 22 Dec 2026.','Imefunguliwa kwa Ruaka Hardware hadi 22 Dec 2026.');T('Quote by Ruaka Hardware, EPRA licence EPRA/T2/55','Nukuu kutoka Ruaka Hardware, leseni ya EPRA EPRA/T2/55');
T('Fundi Calc offer check: panels cover 80% of daily use, inverter is big enough, no battery. Estimate only.','Ukaguzi wa ofa wa Fundi Calc: paneli zinakidhi 80% ya matumizi ya kila siku, kigeuzi kinatosha, hakuna betri. Ni makadirio tu.');
T('Borehole pump estimate FC-ABC123: head 161.69 m, flow 3 m³/hr, about 3.57 kW of solar (7 x 550W panels). The vendor quote is above this estimate, so ask the vendor to explain. Estimate only. Confirm with licensed professionals.','Makadirio ya pampu ya kisima FC-ABC123: urefu 161.69 m, maji 3 m³/saa, takriban 3.57 kW za solar (paneli 7 za 550W). Nukuu ya muuzaji iko juu ya makadirio haya, kwa hivyo muulize muuzaji aeleze. Ni makadirio tu. Thibitisha na wataalamu wenye leseni.');
T('Hello <b>x</b> not in dictionary','Hello <b>x</b> not in dictionary');T('','');T('   ','   ');T('constructor','constructor');T('__proto__','__proto__');T('toString','toString');
for(let i=0;i<30000;i++){const s=Math.random().toString(36).repeat(1+i%5)+['',' ','\n','(',')','$1','~2','.*'][i%8];const r=sw1(s);if(typeof r!=='string'){ok(false,'sw1 returned non-string');break}}
// rules carry Kiswahili
const RU=JSON.parse(R('rules.json')).rules;ok(RU.every(r=>typeof r.x_sw==='string'&&r.x_sw.length>30&&r.x_sw!==r.x),'every rule has its own Kiswahili text');
const ENG=/\b(the|and|your|you|is|are|with|will|before|after)\b/i;ok(!RU.some(r=>(r.x_sw.match(/\b(the|and|your|you|is|are|with|will)\b/gi)||[]).length>1),'rule Kiswahili has no English sentences');
console.log(fails?fails+' FAILS (i18n)':'I18N ALL PASS');process.exit(fails?1:0);
