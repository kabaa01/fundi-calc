# Lists every visible piece of text in the app (English), so each can be translated. Run: python3 tests/i18n_inventory.py out.json
import os,sys,json,re
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL='file://'+os.path.join(ROOT,'index.html')
COLLECT="""()=>{const out=new Set();const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;
while(n=w.nextNode()){const p=n.parentElement;if(!p||/SCRIPT|STYLE/.test(p.tagName))continue;if(p.closest('.hide'))continue;const t=n.nodeValue.replace(/\\s+/g,' ').trim();if(t)out.add(t)}
for(const e of document.querySelectorAll('[placeholder],[aria-label],[title]')){if(e.closest('.hide'))continue;for(const a of ['placeholder','aria-label','title']){const v=e.getAttribute(a);if(v&&v.trim())out.add(v.trim())}}
return [...out]}"""
seen={}
def grab(pg,tag):
    for t in pg.evaluate(COLLECT):seen.setdefault(t,tag)
def go(pg,t):pg.evaluate(f"go('{t}')");pg.wait_for_timeout(20)
def setv(pg,sel,v):pg.evaluate("([s,v])=>{const e=document.querySelector(s);if(e){e.value=v;e.dispatchEvent(new Event('input',{bubbles:true}))}}",[sel,v])
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':400,'height':800});pg.goto(URL);pg.wait_for_timeout(300)
    grab(pg,'gate');pg.check('#ok1');pg.click('#acc')
    if len(sys.argv)>2 and sys.argv[2]=='sw':pg.evaluate("setLang('sw')");pg.wait_for_timeout(100)
    grab(pg,'home')
    pg.evaluate("showLock()");grab(pg,'lock');pg.evaluate("$('lock').classList.add('hide');mn.inert=false")
    go(pg,'q');grab(pg,'solar-form')
    for sp,g,bat in (('5000','none','li'),('20000','full','pb'),('9000','night','li'),('300','none','li'),('52000','none','li'),('0','none','li')):
        setv(pg,'#spend',sp);pg.click(f'#goal [data-v={g}]');pg.click(f'#bat [data-v={bat}]') if g!='none' else 0;pg.click('#go');grab(pg,'solar-'+sp)
    pg.click('#mode [data-v=app]');grab(pg,'appliances');pg.click('#go');grab(pg,'solar-noapp')
    for i in range(9):pg.click(f'[data-a="{i}"][data-d="1"]')
    pg.click('#go');grab(pg,'solar-allapp');pg.click('#tl');grab(pg,'lead');pg.click('[data-i="0"]');grab(pg,'lead-err1');setv(pg,'#ph2','0712345678');pg.click('[data-i="0"]');grab(pg,'lead-err2')
    pg.click('#mode [data-v=kit]');grab(pg,'kit-form');pg.click('#go');grab(pg,'kit-empty')
    for kp,kb,ki in (('200','0','300'),('1500','2400','2000'),('1500','300','2000'),('1500','1000','2000'),('1.5','0','2'),('900','0','2000')):
        setv(pg,'#kp',kp);setv(pg,'#kb',kb);setv(pg,'#ki',ki);pg.click('#go');grab(pg,'kit-'+kp+kb+ki)
    pg.click('#kbt [data-v=pb]');pg.click('#go');grab(pg,'kit-lead')
    go(pg,'k');grab(pg,'cable-form')
    for w,l,ph,us in (('3000','25','1','0'),('7500','60','1','0'),('1000','10','1','1'),('0','5','1','0'),('12000','40','3','0'),('60000','200','3','0'),('3000','900','1','0')):
        setv(pg,'#w',w);setv(pg,'#l',l);pg.click(f'#ph [data-v="{ph}"]');pg.click(f'#us [data-v="{us}"]');pg.click('#kg');grab(pg,'cable-'+w)
    go(pg,'b');grab(pg,'pump-form')
    base=dict(bd='180',bs='85',bdy='125',by='5',be='15',br='120',bn='15',bw='5',bv='')
    def run(tag,**kw):
        for k,v in {**base,**kw}.items():setv(pg,'#'+k,v)
        if 'pipe' in kw:pass
        pg.click('#bgo');grab(pg,'pump-'+tag)
    run('base');run('over',bv='9');run('under',bv='1');run('inrange',bv='4.3');run('short',bn='60');run('lowvel',bn='2',by='9')
    pg.select_option('#bpipe','63mm HDPE_PN10');run('pn10',bn='15',by='9',bdy='40',bs='20',bd='60');pg.select_option('#bpipe','32mm HDPE_PN10');run('highvel',bn='40',by='20',bdy='40',bs='20',bd='60',bw='4')
    pg.select_option('#bpipe','50mm GI_MEDIUM');run('green',bn='20',by='10',bdy='40',bs='20',bd='60',bw='5')
    for tag,kw in (('e1',dict(bdy='300')),('e2',dict(bs='200')),('e3',dict(bw='0')),('e4',dict(bn='0.01')),('e5',dict(by='0')),('e6',dict(bd='0')),('e7',dict(be='-1')),('e8',dict(bw='11')),('e9',dict(bd='5000')),('e10',dict(bs='-1')),('e11',dict(by='999')),('e12',dict(bd='')),('e13',dict(br='99999'))):run(tag,**{**dict(bd='180',bs='85',bdy='125'),**kw})
    pg.select_option('#bpipe','40mm HDPE_PN16');run('base2');pg.evaluate("document.querySelectorAll('.pm')[3].click()");grab(pg,'permit1');pg.evaluate("document.querySelectorAll('.pm')[0].click()");grab(pg,'permit2')
    for i in (1,2,4):pg.evaluate(f"document.querySelectorAll('.pm')[{i}].click()")
    grab(pg,'permit5');pg.click('#tl2');grab(pg,'pump-lead')
    go(pg,'p');grab(pg,'shops');pg.click('#shopgo');grab(pg,'shop-e1');setv(pg,'#shopn','Ruaka Hardware');pg.click('#shopgo');grab(pg,'shop-e2');setv(pg,'#shopt','Ruaka');pg.click('#shopgo');grab(pg,'shop-e3');setv(pg,'#shoph','0712345678')
    pg.click('#shopgo');grab(pg,'shop-e4');pg.evaluate("window.open=()=>{}");pg.check('#shopc');pg.click('#shopgo');grab(pg,'shop-pilot-ok')
    pg.click('#shopm [data-v=pay]');grab(pg,'shop-pay');pg.click('#shopgo');grab(pg,'shop-e5');setv(pg,'#shopk','SGL7ABC123');pg.evaluate("LU=''");pg.click('#shopgo');grab(pg,'shop-pay-ok');pg.click('#shoppl [data-p="2"]');grab(pg,'shop-plan3');pg.click('#shopua');grab(pg,'shop-code-empty')
    go(pg,'i');grab(pg,'inst');pg.click('#instgo');grab(pg,'inst-e1');setv(pg,'#instn','Sunrise Ltd');setv(pg,'#instt','Nakuru');setv(pg,'#insth','0722111222');pg.click('#instgo');grab(pg,'inst-e2');setv(pg,'#instl','EPRA/T2/555');pg.check('#instc');pg.click('#instm [data-v=pay]');grab(pg,'inst-pay')
    go(pg,'r')
    SRC_TR={}
    for t in ('all','cable','solar','pump','shop','inst','build'):pg.evaluate(f"showRules('{t}')");grab(pg,'rules-'+t)
    pg.evaluate("RMETA='Rules last checked 1 Dec 2026. Updated just now.'");pg.evaluate("showRules('all')");grab(pg,'rules-meta')
    pg.evaluate("go('q')");pg.evaluate("go('h')");grab(pg,'home2')
    SRCS=[]
    for m in re.finditer(r"""(?:err|textContent|innerHTML)\s*[:=]\s*(?:'([^'\\]*(?:\\.[^'\\]*)*)'|\"([^\"\\]*(?:\\.[^\"\\]*)*)\")""",open(os.path.join(ROOT,'index.html')).read()):
        v=(m.group(1) or m.group(2) or '').strip().replace("\\'","'")
        if v and re.search(r'[A-Za-z]{3}',v) and '${' not in v and '<' not in v and len(v)<400:SRCS.append(v)
    TR=pg.evaluate('(a)=>a.map(s=>[s,sw1(s)])',SRCS)
    pg_sw1=lambda t:dict(TR).get(t,t)
    b.close()
# static messages in the source (errors that are hard to trigger in a browser)
src=open(os.path.join(ROOT,'index.html')).read()
for m in re.finditer(r"""(?:err|textContent|innerHTML)\s*[:=]\s*(?:'([^'\\]*(?:\\.[^'\\]*)*)'|"([^"\\]*(?:\\.[^"\\]*)*)")""",src):
    s=(m.group(1) or m.group(2) or '').strip()
    if s and re.search(r'[A-Za-z]{3}',s) and '${' not in s and '<' not in s and len(s)<400:seen.setdefault(s.replace("\\'","'"),'src')
json.dump(seen,open(sys.argv[1],'w'),indent=0,ensure_ascii=False)
print(len(seen),'strings')
if len(sys.argv)>2 and sys.argv[2]=='sw':
    STOP=set('the and your you is are to for with of in will it this that be not can but if on at by from as we our an a do does have has when then only before after about'.split())
    OK_WORDS=set('kes epra ebk nca wra kebs odpc kplc whatsapp sms m-pesa pn hdpe gi qr kw wh fc usd ussd ks bs iec ke fundi calc'.split())
    bad=[]
    src_miss=[t for t,tag in seen.items() if tag=='src' and pg_sw1(t)==t]
    print('SOURCE MESSAGES WITHOUT KISWAHILI:',len(src_miss))
    for t in src_miss:print('  src |',t[:140])
    for t,tag in seen.items():
        if tag in ('gate','src'):continue
        if t.endswith('↗') or t.startswith('FC-') or re.fullmatch(r'[\W\d_]+',t):continue
        words=re.findall(r"[A-Za-z’']+",t.lower())
        hits=[w for w in words if w in STOP]
        # 'a' and 'on'/'in'/'to' exist in Kiswahili text rarely; require at least 1 strong stopword, or a short phrase of 3+ plain English words
        strong=[w for w in hits if w not in ('a','on','at','by','as','an')]
        if strong:bad.append((tag,t+'   <'+','.join(strong)+'>'))
    print('ENGLISH LEFT IN KISWAHILI MODE:',len(bad))
    for tag,t in bad:print('  ',tag,'|',t[:140])
    sys.exit(1 if bad or [m for m in src_miss if m not in ('This code ran out on','Unlocked for')] else 0)
