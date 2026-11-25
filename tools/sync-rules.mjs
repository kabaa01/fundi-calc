// Copies rules.json into index.html so the app works offline with the newest rules.
// Run: node tools/sync-rules.mjs
import {readFileSync,writeFileSync} from 'node:fs';
const j=JSON.parse(readFileSync(new URL('../rules.json',import.meta.url)));
const p=new URL('../index.html',import.meta.url);let h=readFileSync(p,'utf8');
const a=h.indexOf('const RULES=['),b=h.indexOf(';\nconst TOPICS',a);
if(a<0||b<0)throw new Error('Could not find the RULES block in index.html');
h=h.slice(0,a)+'const RULES='+JSON.stringify(j.rules)+h.slice(b);
h=h.replace(/let RMETA='[^']*'/,`let RMETA='Rules last checked ${new Date(j.checked).toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric'})}. This is the copy saved in the app.'`);
writeFileSync(p,h);console.log('Saved',j.rules.length,'rules into index.html');
