// Checks every source link in rules.json. Run weekly by GitHub Actions.
// - "w":1 rules are official pages: we also hash the page text and report any change.
// - every rule: we report broken links (HTTP error or no answer).
// A human must read each report. This tool cannot tell what a change means.
import {readFileSync,writeFileSync,existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
const rules=JSON.parse(readFileSync(new URL('../rules.json',import.meta.url))).rules;
const stateUrl=new URL('./watch-state.json',import.meta.url);
const state=existsSync(stateUrl)?JSON.parse(readFileSync(stateUrl)):{};
const norm=h=>h.replace(/<script[\s\S]*?<\/script>/gi,' ').replace(/<style[\s\S]*?<\/style>/gi,' ').replace(/<[^>]+>/g,' ').replace(/&[a-z#0-9]+;/gi,' ').replace(/\s+/g,' ').trim().slice(0,300000);
const out=[],seen=new Set(),today=new Date().toISOString().slice(0,10);
for(const r of rules){
  if(!r.u||seen.has(r.u))continue;seen.add(r.u);
  let status=0,hash='';
  try{
    const res=await fetch(r.u,{redirect:'follow',signal:AbortSignal.timeout(25000),headers:{'user-agent':'Mozilla/5.0 (FundiCalc rule watcher)'}});
    status=res.status;
    if(res.ok&&r.w&&/text|html|json/.test(res.headers.get('content-type')||''))hash=createHash('sha256').update(norm(await res.text())).digest('hex');
  }catch(e){status=0}
  const old=state[r.u];
  if(status===0||status>=400){
    // 403/429 from news sites blocking bots are common, so call them "check by hand"
    out.push(`- **Link problem (${status||'no answer'})** [${r.s}](${r.u}) for rule \`${r.id}\`. Open it by hand.`);
  }else if(r.w&&hash&&old&&old.hash&&old.hash!==hash){
    out.push(`- **Page changed** [${r.s}](${r.u}) for rule \`${r.id}\`. Read it and update \`rules.json\` if the law changed.`);
  }
  state[r.u]={hash:hash||(old&&old.hash)||'',status,checked:today};
}
writeFileSync(stateUrl,JSON.stringify(state,null,1));
const body=out.length?`Rule source check on ${today}\n\n${out.join('\n')}\n\nThis list is made by a robot. It cannot read the meaning of a change, so a person must check each item.\n`:'';
writeFileSync(new URL('./watch-report.md',import.meta.url),body);
console.log(out.length?body:`All ${seen.size} links answered. No official page changed.`);
