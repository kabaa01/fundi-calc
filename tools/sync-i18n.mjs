// Turns i18n/sw.txt into i18n/sw.json and puts it inside index.html.
// Edit i18n/sw.txt (one line each: English => Kiswahili), then run: node tools/sync-i18n.mjs
import {readFileSync,writeFileSync} from 'node:fs';
const txt=readFileSync(new URL('../i18n/sw.txt',import.meta.url),'utf8').split('\n');
const e={},p=[];
txt.forEach((line,i)=>{
  if(!line.trim()||line.startsWith('#'))return;
  const k=line.indexOf(' => ');if(k<0)throw new Error(`line ${i+1}: missing =>`);
  const a=line.slice(0,k).trim(),b=line.slice(k+4).trim();if(!a||!b)throw new Error(`line ${i+1}: empty side`);
  if(a.startsWith('re:')){new RegExp(a.slice(3).trim());p.push([a.slice(3).trim(),b])}
  else{if(a in e)throw new Error(`line ${i+1}: duplicate ${a}`);e[a]=b}
});
const data={e,p};
writeFileSync(new URL('../i18n/sw.json',import.meta.url),JSON.stringify(data,null,0));
const ip=new URL('../index.html',import.meta.url);let h=readFileSync(ip,'utf8');
const a=h.indexOf('/*SWD*/')+7,b=h.indexOf('/*ENDSWD*/');if(a<7||b<0)throw new Error('markers not found in index.html');
h=h.slice(0,a)+JSON.stringify(data).replace(/<\//g,'<\\/')+h.slice(b);writeFileSync(ip,h);
console.log('Kiswahili saved:',Object.keys(e).length,'phrases,',p.length,'patterns');
