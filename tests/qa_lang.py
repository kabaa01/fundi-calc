# Kiswahili and English must both be complete, and switching must not break anything.
import os,sys,re,json
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));URL='file://'+os.path.join(ROOT,'index.html')
fails=[];errs=[]
def ok(c,m):
    if not c:fails.append(m);print('FAIL',m[:220])
STOP=set('the and your you is are to for with of in will it this that be not can but if when then only before after about we our do does have has'.split())
def english_left(t):
    out=[]
    for line in t.split('\n'):
        if re.search(r'↗',line):continue
        w=re.findall(r"[A-Za-z’']+",line.lower());s=[x for x in w if x in STOP]
        if s:out.append(line[:90]+' <'+','.join(s)+'>')
    return out
def go(pg,t):pg.evaluate(f"go('{t}')");pg.wait_for_timeout(20)
def setv(pg,sel,v):pg.evaluate("([s,v])=>{const e=document.querySelector(s);if(e){e.value=v;e.dispatchEvent(new Event('input',{bubbles:true}))}}",[sel,v])
def snap(pg):return re.sub(r'\s+',' ',pg.evaluate("document.body.innerText")).strip()
STATES=[]
def build(pg):
    def s_home():go(pg,'h')
    def s_solar():go(pg,'q');pg.click('#mode [data-v=tok]');pg.click('#go')
    def s_night():go(pg,'q');pg.click('#goal [data-v=night]');pg.click('#go')
    def s_err():go(pg,'q');setv(pg,'#spend','0');pg.click('#go')
    def s_kit():go(pg,'q');setv(pg,'#spend','5000');pg.click('#mode [data-v=kit]');setv(pg,'#kp','1500');setv(pg,'#kb','2400');setv(pg,'#ki','2000');pg.click('[data-a="0"][data-d="1"]');pg.click('#go')
    def s_cable():go(pg,'k');setv(pg,'#w','3000');pg.click('#kg')
    def s_cable_err():go(pg,'k');setv(pg,'#w','0');pg.click('#kg')
    def s_pump():go(pg,'b');pg.click('#bgo')
    def s_pump_err():go(pg,'b');setv(pg,'#bdy','999');pg.click('#bgo');setv(pg,'#bdy','125')
    def s_shop():go(pg,'p');pg.click('#shopm [data-v=pay]');pg.click('#shopgo')
    def s_inst():go(pg,'i');pg.click('#instgo')
    def s_rules():pg.evaluate("showRules('build')")
    def s_lead():go(pg,'q');setv(pg,'#spend','5000');pg.click('#mode [data-v=tok]');pg.click('#go');pg.click('#tl');pg.click('[data-i="0"]')
    return [('home',s_home),('solar',s_solar),('solar-night',s_night),('solar-error',s_err),('kit',s_kit),('cable',s_cable),('cable-error',s_cable_err),('pump',s_pump),('pump-error',s_pump_err),('shop-error',s_shop),('inst-error',s_inst),('rules',s_rules),('lead',s_lead)]
with sync_playwright() as p:
    b=p.chromium.launch();c=b.new_context(viewport={'width':400,'height':800});pg=c.new_page()
    pg.on('pageerror',lambda e:errs.append(str(e)[:150]))
    pg.goto(URL);pg.wait_for_timeout(300);pg.check('#ok1');pg.click('#acc');pg.evaluate("window.open=()=>{}")
    for name,fn in build(pg):
        fn();en=snap(pg)                                   # English as built
        pg.evaluate("setLang('sw')");pg.wait_for_timeout(60);sw=snap(pg)
        left=english_left(pg.evaluate("document.body.innerText"));ok(not left,f'English left in Kiswahili on {name}: {left[:3]}')
        ok(sw!=en or name=='home','Kiswahili differs from English on '+name)
        pg.evaluate("setLang('en')");pg.wait_for_timeout(60);back=snap(pg)
        ok(back==en,f'English restored exactly after switching back on {name}')
    # language flows
    pg.evaluate("setLang('sw')");go(pg,'q');setv(pg,'#spend','5000');pg.click('#mode [data-v=tok]');pg.click('#go');pg.wait_for_timeout(80)
    ok('Pata nukuu yangu' in pg.inner_text('#go'),'button in Kiswahili');ok('kwa mwezi' in pg.inner_text('#qo'),'saving line in Kiswahili: '+pg.inner_text('#qo .hero')[:90])
    h=pg.get_attribute('#qo a.btn.w','href');ok('Nukuu%20ya%20Fundi%20Calc' in h,'share message in Kiswahili: '+h[:100]);ok('Nukuu%20ya%20Fundi%20Calc' in pg.get_attribute('#qo a[href^="sms:"]','href'),'SMS message in Kiswahili')
    pg.evaluate("setLang('en')");pg.click('#go');ok('Fundi%20Calc%20quote' in pg.get_attribute('#qo a.btn.w','href'),'share message in English again')
    # toggle while a result is open: rules card follows the language
    pg.evaluate("setLang('sw')");pg.click('#qo details.rc summary');ok('mkandarasi' in pg.inner_text('#qo details.rc') or 'fundi' in pg.inner_text('#qo details.rc').lower(),'rule card in Kiswahili');pg.evaluate("setLang('en')");ok('licensed' in pg.inner_text('#qo details.rc').lower(),'rule card back in English')
    # rules page + shop/installer rule blocks
    pg.evaluate("setLang('sw')");pg.evaluate("showRules('all')");t=pg.inner_text('#rlist');ok(len(re.findall('Sheria|Kiwango|Mazoea mazuri',t))>=15,'rule tags in Kiswahili');ok('The county checks' not in t and 'mkandarasi' in t,'rules text in Kiswahili');ok('Uwekaji waya' in pg.inner_text('#rch'),'rule chips in Kiswahili')
    go(pg,'p');ok('Rules every shop' not in pg.inner_text('#rs-shop') and 'Sheria' in pg.inner_text('#rs-shop'),'shop rules block in Kiswahili')
    # persistence + live rules without Swahili fall back to English
    pg.reload();pg.wait_for_timeout(500);ok(pg.evaluate("document.documentElement.lang")=='sw','language remembered');pg.check('#ok1') if pg.is_visible('#gate') else 0
    pg.evaluate("setRules(RULES.map((r,i)=>i?r:{...r,x_sw:undefined,x:r.x+' extra'}))");pg.evaluate("showRules('all')");ok('extra' in pg.inner_text('#rlist'),'a rule without Kiswahili falls back to English')
    # hostile Kiswahili-mode input: user text is never rewritten
    pg.evaluate("setLang('sw')");go(pg,'p');pg.fill('#shopn','Shop');ok(pg.input_value('#shopn')=='Shop','typed text untouched')
    # stress: flip languages 40 times quickly, then the page still works
    for i in range(40):pg.evaluate(f"setLang('{'sw' if i%2==0 else 'en'}')")
    pg.evaluate("setLang('en')");go(pg,'k');pg.click('#kg');ok(pg.is_visible('#ko .hero'),'works after 40 language flips');ok(not english_left('\n'.join([]))  ,'noop')
    b.close()
ok(not errs,'page errors: '+str(errs[:3]))
print('LANG QA:','ALL PASS' if not fails else f'{len(fails)} FAILS');sys.exit(1 if fails else 0)
