import sys
from playwright.sync_api import sync_playwright
import os
URL='file://'+os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'index.html')
errs=[];fails=[]
def ok(c,m):
    if not c: fails.append(m);print('FAIL',m)
with sync_playwright() as p:
    b=p.chromium.launch()
    for w,h,name in [(360,740,'phone'),(1024,800,'desktop')]:
        pg=b.new_page(viewport={'width':w,'height':h});pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append(m.text) if m.type=='error' and 'fonts.g' not in m.text and 'ERR_' not in m.text else None)
        pg.goto(URL);pg.wait_for_timeout(300)
        ok(pg.is_visible('#gate'),'gate shows first');ok(pg.eval_on_selector('main','m=>m.inert'),'main inert behind gate')
        ok(pg.is_disabled('#acc'),'continue disabled until ticked');pg.check('#ok1');pg.click('#acc');ok(not pg.is_visible('#gate'),'gate closes')
        # home
        ok(pg.is_visible('#try'),'home visible');ok(pg.locator('#h .ch').count()>=13,'home cards')
        if name=='phone': pg.screenshot(path='/tmp/s_home.png')
        # overflow
        def noov(tag):
            ov=pg.evaluate('document.documentElement.scrollWidth-document.documentElement.clientWidth');ok(ov<=0,f'horizontal overflow {ov}px on {tag} {name}')
        noov('home')
        # swahili
        pg.click('#lg');ok('Kagua kabla' in pg.inner_text('#h'),'swahili home');ok('Mwanzo' in pg.inner_text('#nv'),'swahili nav');ok(pg.inner_text('#lg')=='EN','toggle label')
        pg.click('#lg');ok('Check before' in pg.inner_text('#h'),'english back')
        # try it
        pg.click('#try');pg.wait_for_timeout(200);ok(pg.is_visible('#qo .hero'),'try-it shows quote');ok('KES' in pg.inner_text('#qo .hero'),'quote has KES')
        if name=='phone': pg.screenshot(path='/tmp/s_quote.png',full_page=True)
        noov('quote')
        ok(pg.locator('a[href^="sms:"]').count()>=1,'sms link');ok(pg.is_visible('#tl'),'installer button')
        # lead routing
        pg.click('#tl');pg.fill('#ph2','123');pg.click('[data-i="0"]');ok('valid Kenyan' in pg.inner_text('#lerr'),'lead phone validation')
        pg.fill('#ph2','0712345678');pg.click('[data-i="0"]');ok('Tick' in pg.inner_text('#lerr'),'lead consent required')
        # modes
        pg.click('.bar [data-t=q]');pg.click('#mode [data-v=app]');pg.click('[data-a="0"][data-d="1"]');pg.click('[data-a="2"][data-d="1"]');pg.click('#go');pg.wait_for_timeout(100);ok(pg.is_visible('#qo .hero'),'appliance quote')
        pg.click('#mode [data-v=tok]');pg.fill('#spend','0');pg.click('#go');ok('Enter what you spend' in pg.inner_text('#qo'),'zero spend message')
        pg.fill('#spend','8000');pg.click('#goal [data-v=night]');ok(pg.is_visible('#batw'),'battery shows for night');pg.click('#go');ok(pg.is_visible('#qo .hero'),'night quote')
        # kit
        pg.click('#mode [data-v=kit]');ok(pg.is_visible('#kitf')and not pg.is_visible('#goalw'),'kit fields shown, goals hidden')
        pg.click('#go');ok('Enter the panels' in pg.inner_text('#qo') or 'Add the appliances' in pg.inner_text('#qo'),'kit empty message')
        pg.fill('#kp','200');pg.fill('#kb','0');pg.fill('#ki','300');pg.click('[data-a="0"][data-d="1"]');pg.click('#go');pg.wait_for_timeout(100)
        ok('will not run' in pg.inner_text('#qo .v'),'small kit rejected: '+pg.inner_text('#qo .v'))
        pg.fill('#kp','1500');pg.fill('#kb','2400');pg.fill('#ki','2000');pg.click('#go');ok('fits' in pg.inner_text('#qo .v'),'good kit accepted: '+pg.inner_text('#qo .v'))
        # cable
        pg.click('.bar [data-t=k]');pg.click('#pre [data-p="0"]');ok(pg.input_value('#w')=='7500','preset sets watts');pg.click('#kg');ok(pg.is_visible('#ko .hero'),'cable result');noov('cable')
        pg.fill('#w','0');pg.click('#kg');ok('above zero' in pg.inner_text('#ko'),'cable validation')
        # borehole
        pg.click('.bar [data-t=b]');pg.click('#bgo');pg.wait_for_timeout(100);ok('161.69' in pg.inner_text('#bo'),'borehole baseline head');ok('Needs attention' in pg.inner_text('#bo .v'),'borehole red verdict')
        pg.fill('#bdy','300');pg.click('#bgo');ok('cannot be deeper' in pg.inner_text('#bo'),'borehole validation');noov('borehole')
        # shops buy
        pg.click('.bar [data-t=p]');ok(pg.locator('#shopgo').count()==1,'shop buy button');pg.click('#shopgo');ok('shop name' in pg.inner_text('#shope').lower() or 'business name' in pg.inner_text('#shope').lower(),'shop requires name')
        pg.fill('#shopn','Ruaka Hardware');pg.fill('#shopt','Ruaka');pg.fill('#shoph','0712345678');pg.click('#shopm [data-v=pay]');ok(pg.is_visible('#shopk'),'pay shows code box')
        pg.click('#shopgo');ok('10-character' in pg.inner_text('#shope'),'code required');pg.fill('#shopk','sgl7abc123');pg.click('#shopgo');ok('terms' in pg.inner_text('#shope').lower(),'consent required')
        pg.check('#shopc')
        pg.evaluate("window.__u=[];window.open=u=>{window.__u.push(u)}")
        pg.click('#shopgo')
        import urllib.parse as up
        u=up.unquote(pg.evaluate("(window.__u.filter(x=>x).pop())||''"))
        ok('FC-' in pg.inner_text('#shopok'),'order ref shown');ok('Amount paid: KES 3500' in u and 'SGL7ABC123' in u and 'Ruaka Hardware' in u,'order message complete: '+u[:120])
        pg.click('#shoppl [data-p="2"]');ok('9,000' in pg.inner_text('#shopgo'),'plan switch updates amount');noov('shops')
        # installers
        pg.click('.bar [data-t=i]');pg.click('#instgo');ok('business name' in pg.inner_text('#inste').lower(),'installer name required')
        pg.fill('#instn','Sunrise Ltd');pg.fill('#instt','Nakuru');pg.fill('#insth','0722111222');pg.click('#instgo');ok('EPRA licence' in pg.inner_text('#inste'),'installer needs licence');noov('installers')
        # kenyan rules
        pg.click('.bar [data-t=h]');pg.click('#h [data-g="r:build"]');ok(pg.is_visible('#rlist'),'rules page opens from home tile');ok(pg.locator('#rlist .ru').count()>=6,'build rules listed');ok(pg.locator('#rch [aria-pressed=true]').inner_text()=='Building','build chip active')
        pg.click('#rch [data-rt=pump]');ok('WRA' in pg.inner_text('#rlist'),'borehole filter shows WRA');ok(pg.locator('#rlist a[href^="https://"]').count()>=3,'rules have source links');noov('rules')
        pg.click('#rch [data-rt=all]');ok(pg.locator('#rlist .ru').count()>=15,'all rules');pg.click('#rb');ok(pg.is_visible('#try'),'back returns to previous screen')
        pg.click('#rl');ok(pg.is_visible('#rlist'),'rules link on home')
        pg.click('.bar [data-t=k]');pg.fill('#w','3000');pg.click('#kg');ok(pg.locator('#ko details.rc').count()==1,'cable result has rules card');pg.click('#ko details.rc summary');ok('licensed' in pg.inner_text('#ko details.rc').lower() if False else 'licensed' in pg.inner_text('#ko details.rc').lower(),'rules card text')
        pg.click('#ko [data-rules]');ok(pg.is_visible('#rlist'),'see all rules from result')
        pg.click('.bar [data-t=b]');pg.fill('#bdy','125');pg.click('#bgo');ok(pg.locator('#bo .pm').count()==5,'permit checklist');ok('Do not pump' in pg.inner_text('#pmst'),'permit status initial')
        pg.check('#bo .pm >> nth=3');ok('Finish the rest' in pg.inner_text('#pmst'),'permit status after abstraction ticked')
        for i in (0,1,2,4): pg.check(f'#bo .pm >> nth={i}')
        ok('All 5 done' in pg.inner_text('#pmst'),'permit all done')
        pg.click('.bar [data-t=p]');ok(pg.locator('#rs-shop details[open]').count()==1,'shop rules visible');pg.click('.bar [data-t=i]');ok('EPRA' in pg.inner_text('#rs-inst'),'installer rules visible')
        pg.click('.bar [data-t=q]');pg.click('#mode [data-v=tok]');pg.fill('#spend','5000');pg.click('#go');ok(pg.locator('#qo details.rc').count()==1,'solar result has rules card')
        pg.click('#qo details.rc summary');ok('EPRA' in pg.inner_text('#qo details.rc'),'solar rules mention EPRA')
        # dark mode + reduced
        pg.click('#th');ok(pg.evaluate("document.documentElement.dataset.theme")in('dark','light'),'theme toggles')
        # touch target sizes
        small=pg.evaluate("[...document.querySelectorAll('button,input,select,a.btn')].filter(e=>e.offsetParent&&!e.closest('.hide')).filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&(r.height<40||r.width<40)&&e.type!='checkbox'}).map(e=>(e.id||e.className||e.tagName)+':'+Math.round(e.getBoundingClientRect().width)+'x'+Math.round(e.getBoundingClientRect().height))")
        ok(not small,'small touch targets '+str(small[:6]))
        pg.close()
    b.close()
ok(not errs,'console errors: '+str(errs[:5]))
print('BROWSER QA:','ALL PASS' if not fails else f'{len(fails)} FAILS')
