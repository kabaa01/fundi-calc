import os,sys,json,shutil,subprocess,time,random,re
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));PART=os.environ.get('PART','all');SITE='/tmp/fc_stress_'+PART;PORT=8788+{'all':0,'layout':1,'fuzz':2,'misc':3}.get(PART,4)
shutil.rmtree(SITE,ignore_errors=True);os.makedirs(SITE)
for f in ('index.html','rules.json','config.json','sw.js'):
    if os.path.exists(os.path.join(ROOT,f)):shutil.copy(os.path.join(ROOT,f),SITE)
fails=[];errs=[]
def ok(c,m):
    if not c:
        fails.append(m);print('FAIL',m[:230])
BAD=re.compile(r'NaN|undefined|Infinity|\[object|null\b')
TABS=['h','q','k','b','p','i','r']
CONTRAST_JS="""()=>{
const parse=c=>{const m=c.match(/rgba?\\(([^)]+)\\)/);if(!m)return null;const p=m[1].split(/[ ,\\/]+/).filter(Boolean).map(Number);return{r:p[0],g:p[1],b:p[2],a:p.length>3?p[3]:1}};
const lum=({r,g,b})=>{const f=v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)};return .2126*f(r)+.7152*f(g)+.0722*f(b)};
const over=(t,b)=>({r:t.r*t.a+b.r*(1-t.a),g:t.g*t.a+b.g*(1-t.a),b:t.b*t.a+b.b*(1-t.a),a:1});
const bgOf=el=>{let layers=[];for(let e=el;e;e=e.parentElement){const c=parse(getComputedStyle(e).backgroundColor);if(c&&c.a>0){layers.push(c);if(c.a>=1)break}}let base={r:255,g:255,b:255,a:1};for(let i=layers.length-1;i>=0;i--)base=over(layers[i],base);return base};
const out=[];
for(const el of document.querySelectorAll('body *')){
 if(!el.offsetParent&&getComputedStyle(el).position!=='fixed')continue;
 if(el.closest('.hide')||el.closest('[aria-hidden=true]'))continue;
 const own=[...el.childNodes].some(n=>n.nodeType===3&&n.textContent.trim());if(!own)continue;
 const cs=getComputedStyle(el);if(cs.visibility==='hidden'||cs.opacity==='0')continue;
 const fg=parse(cs.color),bg=bgOf(el);if(!fg)continue;const f=over(fg,bg);
 const L1=lum(f),L2=lum(bg),r=(Math.max(L1,L2)+.05)/(Math.min(L1,L2)+.05);
 const size=parseFloat(cs.fontSize),bold=parseInt(cs.fontWeight)>=700,large=size>=24||(size>=18.66&&bold);
 if(r<(large?3:4.5))out.push((el.id||el.className||el.tagName)+' "'+el.textContent.trim().slice(0,28)+'" '+r.toFixed(2));
}return out}"""
LABEL_JS="""()=>{const out=[];for(const el of document.querySelectorAll('input,select,textarea,button,a[href]')){
 if(!el.offsetParent||el.closest('.hide'))continue;
 const name=(el.getAttribute('aria-label')||'').trim()||(el.labels&&el.labels.length&&[...el.labels].some(l=>l.textContent.trim()))||(el.getAttribute('aria-labelledby'))||((el.tagName==='BUTTON'||el.tagName==='A')&&el.textContent.trim());
 if(!name)out.push((el.id||el.className||el.tagName)+':'+el.tagName)}return out}"""
OVER_JS="""()=>{const w=document.documentElement.clientWidth,o=[];if(document.documentElement.scrollWidth>w+1)o.push('page scroll '+document.documentElement.scrollWidth+'>'+w);
 for(const e of document.querySelectorAll('main *,.bar *,header *')){if(!e.offsetParent)continue;const r=e.getBoundingClientRect();if(r.width&&r.right>w+1&&!e.closest('.chips'))o.push((e.id||e.className||e.tagName)+' right='+Math.round(r.right));if(o.length>4)break}return o}"""
def go(pg,t):pg.evaluate(f"go('{t}')");pg.wait_for_timeout(30)
def accept(pg):
    if pg.is_visible('#gate'):pg.check('#ok1');pg.click('#acc')
def states(pg):
    """put the app in each result state, yielding (name) after each"""
    go(pg,'h');yield 'home'
    go(pg,'q');pg.click('#go');yield 'solar'
    pg.click('#mode [data-v=kit]');pg.fill('#kp','1500');pg.fill('#kb','2400');pg.fill('#ki','2000');pg.click('[data-a="0"][data-d="1"]');pg.click('#go');yield 'kit'
    pg.click('#mode [data-v=tok]');pg.click('#goal [data-v=night]');pg.click('#go');yield 'solar-night'
    go(pg,'k');pg.click('#kg');yield 'cable'
    go(pg,'b');pg.click('#bgo');yield 'pump'
    pg.click('#bo .pm >> nth=0');yield 'pump-checklist'
    go(pg,'p');yield 'shops'
    pg.click('#shopm [data-v=pay]');yield 'shops-pay'
    go(pg,'i');yield 'installers'
    go(pg,'r');yield 'rules'
    pg.evaluate("showRules('build')");yield 'rules-build'
    go(pg,'q');pg.click('#tl');yield 'lead-form'
run=lambda *n:PART=='all' or PART in n
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'-d',SITE],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
URL=f'http://localhost:{PORT}/index.html'
try:
 with sync_playwright() as p:
    b=p.chromium.launch()
    def newpage(vw=360,vh=740,scheme='light',**kw):
        c=b.new_context(viewport={'width':vw,'height':vh},color_scheme=scheme,**kw);pg=c.new_page()
        pg.on('pageerror',lambda e:errs.append(str(e)[:150]));pg.on('console',lambda m:errs.append(m.text[:150]) if m.type=='error' and 'ERR_' not in m.text and '404' not in m.text else None)
        return c,pg
    # ---- A/B/C: layout, contrast, labels across widths and themes
    for scheme,vw,lang in ([(sc,w,'en') for sc in ('light','dark') for w in (320,360,412,768,1280)]+[('light',w,'sw') for w in (320,360,412)]+[('dark',360,'sw')] if run('layout') else []):
        if True:
            c,pg=newpage(vw,740 if vw<700 else 900,scheme);pg.goto(URL);pg.wait_for_timeout(300)
            ok(pg.is_visible('#gate'),f'gate visible {scheme} {vw}')
            if vw==320:
                pg.screenshot(path=f'/tmp/st_gate_{scheme}.png')
            accept(pg)
            if lang=='sw':pg.evaluate("setLang('sw')")
            for st in states(pg):
                o=pg.evaluate(OVER_JS);ok(not o,f'overflow {lang} {scheme} {vw} {st}: {o}')
                if vw in (360,1280):
                    cf=pg.evaluate(CONTRAST_JS);ok(not cf,f'contrast {lang} {scheme} {vw} {st}: {cf[:4]}')
                    lb=pg.evaluate(LABEL_JS);ok(not lb,f'unlabelled {st}: {lb[:4]}')
            c.close()
    # ---- D: UI fuzz
    JUNK=['','0','-1','1e309','abc','   ','999999999999','0.0000001','<script>window.__x=1</script>','٣','1,5','5e3','9'*400,'😀','1.2.3','-0','Infinity','NaN']
    N=int(os.environ.get('FUZZ','40'))
    c,pg=newpage();pg.goto(URL);pg.wait_for_timeout(300);accept(pg);rnd=random.Random(7)
    def setv(sel,v):pg.evaluate("([s,v])=>{const e=document.querySelector(s);if(!e)return;e.value=(e.type==='number'&&isNaN(Number(v)))?'':v;e.dispatchEvent(new Event('input',{bubbles:true}))}",[sel,v])
    def clean(out,tag):
        t=pg.inner_text(out);ok(t.strip()!='',f'{tag} produced no output');ok(not BAD.search(t),f'{tag} shows bad text: {BAD.search(t).group(0) if BAD.search(t) else ""} in {t[:100]!r}')
    pg.evaluate("window.__x=undefined;window.open=u=>{}")
    for i in range(N if run('fuzz') else 0):
        go(pg,'q');pg.click('#mode [data-v=tok]');setv('#spend',rnd.choice(JUNK));setv('#tar',rnd.choice(JUNK));pg.click(f'#goal [data-v={rnd.choice(["none","night","full"])}]');pg.select_option('#city',index=rnd.randrange(8));pg.click('#go');clean('#qo','solar-token')
        pg.click('#mode [data-v=kit]');[setv(s,rnd.choice(JUNK)) for s in ('#kp','#kb','#ki')];pg.click(f'[data-a="{rnd.randrange(9)}"][data-d="1"]');pg.click('#go');clean('#qo','kit')
        go(pg,'k');[setv(s,rnd.choice(JUNK)) for s in ('#w','#l')];pg.click(f'#ph [data-v="{rnd.choice([1,3])}"]');pg.click('#kg');clean('#ko','cable')
        go(pg,'b');[setv(s,rnd.choice(JUNK)) for s in ('#bd','#bs','#bdy','#by','#be','#br','#bn','#bw','#bv')];pg.select_option('#bpipe',index=rnd.randrange(10));pg.select_option('#bc',index=rnd.randrange(15));pg.click('#bgo');clean('#bo','pump')
        go(pg,'p');[setv(s,rnd.choice(JUNK)) for s in ('#shopn','#shopt','#shoph')];pg.click(f'#shopm [data-v={rnd.choice(["pay","pilot"])}]');setv('#shopk',rnd.choice(JUNK));pg.click('#shopgo');ok(not BAD.search(pg.inner_text('#shope')+pg.inner_text('#shopok')),'shop buy bad text')
        go(pg,'i');[setv(s,rnd.choice(JUNK)) for s in ('#instn','#instt','#insth','#instl','#insta')];pg.click('#instua');pg.click('#instgo')
    ok(pg.evaluate('window.__x')is None,'XSS from fuzz');c.close()
    # ---- E: double submit
    if not run('misc'):
        b.close();real=[e for e in errs if 'favicon' not in e];ok(not real,'page errors: '+str(real[:4]));print('STRESS part done:',len(fails),'fails');sys.exit(1 if fails else 0)
    c,pg=newpage();pg.goto(URL);pg.wait_for_timeout(300);accept(pg);go(pg,'p')
    pg.evaluate("window.__u=[];window.open=u=>{if(u)window.__u.push(u)}")
    pg.fill('#shopn','Ruaka Hardware');pg.fill('#shopt','Ruaka');pg.fill('#shoph','0712345678');pg.check('#shopc');pg.dblclick('#shopgo');pg.wait_for_timeout(100)
    ok(pg.evaluate('window.__u.length')==1,'double click opens WhatsApp once, got '+str(pg.evaluate('window.__u.length')))
    go(pg,'q');pg.click('#go');pg.click('#tl');pg.fill('#ph2','0712345678');pg.check('#cs2');pg.evaluate("window.__u=[]");pg.dblclick('[data-i="0"]');pg.wait_for_timeout(100);ok(pg.evaluate('window.__u.length')==1,'double click lead once, got '+str(pg.evaluate('window.__u.length')));c.close()
    # ---- F: storage blocked
    c,pg=newpage();pg.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new Error('blocked')}})");pg.goto(URL);pg.wait_for_timeout(400)
    ok(pg.is_visible('#gate'),'gate shows with storage blocked');accept(pg);go(pg,'q');pg.click('#go');ok(pg.is_visible('#qo .hero'),'works with storage blocked');pg.click('#lg');ok('Kagua' in pg.inner_text('#h'),'language switch with storage blocked');c.close()
    # ---- G: slow config must not wipe typing
    cfg=json.load(open(os.path.join(SITE,'config.json')));cfg.update(till='555777',operatorWa='254711000111');json.dump(cfg,open(os.path.join(SITE,'config.json'),'w'))
    c,pg=newpage();pg.route('**/config.json',lambda r:(time.sleep(2.0),r.continue_())[1]);pg.goto(URL);pg.wait_for_timeout(200);accept(pg);go(pg,'p')
    pg.fill('#shopn','Typing Hardware');pg.click('#shopm [data-v=pay]');pg.fill('#shopk','sgl7abc123');pg.wait_for_timeout(3000)
    ok(pg.input_value('#shopn')=='Typing Hardware','typed shop name survives slow config');ok(pg.input_value('#shopk').lower()=='sgl7abc123','typed M-Pesa code survives slow config');ok('555777' in pg.inner_text('#shoppay'),'till appears after slow config');c.close()
    # ---- H: Nairobi midnight (UTC 21:30 = 00:30 EAT next day)
    c,pg=newpage();pg.goto(URL);pg.wait_for_timeout(300);accept(pg)
    pg.clock.set_fixed_time('2026-11-22T21:30:00Z');ok(pg.evaluate('today()')=='2026-11-23','today() uses Nairobi date at 00:30 EAT, got '+str(pg.evaluate('today()')));c.close()
    # ---- K: hostile config / rules
    cfg.update(till='<img src=x onerror="window.__x=1">',operatorWa='abc2547<b>11</b>000111');json.dump(cfg,open(os.path.join(SITE,'config.json'),'w'))
    rj=json.load(open(os.path.join(SITE,'rules.json')));rj['rules'][0]['x']='<img src=x onerror="window.__x=2"> '+rj['rules'][0]['x'];rj['rules'][0]['s']='<b>bad</b>';json.dump(rj,open(os.path.join(SITE,'rules.json'),'w'))
    c,pg=newpage();pg.goto(URL);pg.wait_for_timeout(500);accept(pg);go(pg,'p');pg.click('#shopm [data-v=pay]');pg.evaluate("showRules('all')");pg.wait_for_timeout(100)
    ok(pg.evaluate('window.__x')is None,'hostile config/rules cannot run script');ok(re.fullmatch(r'\d*',pg.evaluate('TILL')) is not None,'hostile till keeps digits only, got '+str(pg.evaluate('TILL')));ok(pg.evaluate('OPERATOR_WA')=='2547'+'11000111','operator number keeps digits only: '+pg.evaluate('OPERATOR_WA'));c.close()
    shutil.copy(os.path.join(ROOT,'rules.json'),SITE);cfg.update(till='123456',operatorWa='254700111222');json.dump(cfg,open(os.path.join(SITE,'config.json'),'w'))
    # ---- I: offline via service worker
    if os.path.exists(os.path.join(SITE,'sw.js')):
        c,pg=newpage();pg.goto(URL);pg.wait_for_timeout(300);accept(pg)
        pg.evaluate("navigator.serviceWorker.ready.then(()=>1)");pg.wait_for_timeout(1500)
        c.set_offline(True);pg.reload();pg.wait_for_timeout(800);ok(pg.is_visible('#h h2') or pg.is_visible('#gate'),'app opens offline after first visit');accept(pg);go(pg,'q');pg.click('#go');ok(pg.is_visible('#qo .hero'),'tools work offline');c.set_offline(False);c.close()
    else:ok(False,'no service worker for offline use')
    # ---- stale prices after 45 days
    c,pg=newpage();pg.goto(URL);pg.wait_for_timeout(300);accept(pg);pg.clock.set_fixed_time('2027-01-20T10:00:00Z');go(pg,'q');pg.click('#go');ok('out of date' in pg.inner_text('#qo'),'stale price warning after 45 days');c.close()
    b.close()
finally:srv.terminate()
real=[e for e in errs if 'favicon' not in e]
ok(not real,'page errors: '+str(real[:4]))
print('STRESS:','ALL PASS' if not fails else f'{len(fails)} FAILS')
sys.exit(1 if fails else 0)
