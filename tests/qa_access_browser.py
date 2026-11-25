import os,json,shutil,subprocess,sys,time,urllib.parse as up
from playwright.sync_api import sync_playwright
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE='/tmp/fc_site';PORT=8777
shutil.rmtree(SITE,ignore_errors=True);os.makedirs(SITE)
for f in ('index.html','rules.json','config.json'):shutil.copy(os.path.join(ROOT,f),SITE)
ADMIN=os.environ.get('FC_ADMIN') or os.path.join(ROOT,'..','admin','admin.html')
fails=[]
def ok(c,m):
    if not c:fails.append(m);print('FAIL',m)
def order(**o):
    js="const E=new Function(require('fs').readFileSync(process.argv[1],'utf8').split('/*ENGINE*/')[1].split('/*END*/')[0]+';return{order}')();console.log(JSON.stringify(E.order(JSON.parse(process.argv[2]))))"
    return json.loads(subprocess.check_output(['node','-e',js,os.path.join(ROOT,'index.html'),json.dumps(o)]))['msg']
SMS="""SGL7ABC123 Confirmed. You have received Ksh3,500.00 from JOHN KAMAU 254722111222 on 22/11/26 at 10:15 AM.
QHA1XYZ999 Confirmed. Ksh1,000.00 received from MARY WANJIRU 0733444555 on 22/11/26 at 11:00 AM.
RTB5LMN777 Confirmed. Ksh2,500.00 received from SUNRISE LTD 254700123456 on 22/11/26 at 12:00 PM."""
D='2026-11-22'
base=dict(role='shop',plan=1,name='Ruaka Hardware',town='Ruaka',phone='0722111222',mode='pay',code='SGL7ABC123',date=D)
with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context();ad=ctx.new_page();errs=[]
    ad.on('pageerror',lambda e:errs.append('admin:'+str(e)))
    ad.goto('file://'+os.path.abspath(ADMIN))
    # ---- admin
    ad.click('#mk');pub=ad.input_value('#pub');prv=ad.input_value('#prv');ok(json.loads(pub).get('kty')=='EC' and 'd' in json.loads(prv) and 'd' not in json.loads(pub),'admin makes EC keypair; public has no private part')
    ad.click('#ck');ok(ad.is_disabled('#is'),'cannot issue before checking');
    ad.fill('#om',order(**base));ad.fill('#sm',SMS);ad.click('#ck');ok('load your private key' in ad.inner_text('#res').lower(),'asks for private key first');ok(ad.is_disabled('#is'),'issue disabled without key')
    ad.fill('#prv2','{"bad":1}');ad.click('#lk');ok('not a private key' in ad.inner_text('#ks'),'bad key rejected')
    ad.fill('#prv2',prv);ad.click('#lk');ok('Key loaded' in ad.inner_text('#ks'),'key loaded')
    ad.click('#ck');ok('Payment found' in ad.inner_text('#res'),'payment verified: '+ad.inner_text('#res')[:80]);ok(not ad.is_disabled('#is'),'issue enabled after good check')
    ad.click('#is');shop_code=ad.input_value('#code');ok(shop_code.startswith('FC1.'),'shop code issued');ok('254722111222' in up.unquote(ad.get_attribute('#wl','href')),'whatsapp link to customer')
    ad.click('#ck');ok('already used' in ad.inner_text('#res'),'same M-Pesa code cannot be used twice');ok(ad.is_disabled('#is'),'issue disabled on reuse')
    ad.fill('#om',order(**{**base,'code':'QHA1XYZ999'}));ad.click('#ck');ok('plan costs KES 3500' in ad.inner_text('#res'),'short payment blocked');
    ad.fill('#om',order(**{**base,'code':'ZZZ9ZZZ999'}));ad.click('#ck');ok('not found in your till' in ad.inner_text('#res'),'fake code blocked')
    pil=order(**{**base,'name':'Kasarani Hardware','phone':'0733444555','mode':'pilot','code':''});ad.fill('#om',pil);ad.click('#ck');ok(ad.is_disabled('#is') and not ad.is_disabled('#ip'),'pilot uses pilot button only');ad.click('#ip');pilot_code=ad.input_value('#code');ok(pilot_code.startswith('FC1.'),'pilot code issued')
    import base64,datetime;pc=json.loads(base64.urlsafe_b64decode(pilot_code.split('.')[1]+'==='));want=(datetime.datetime.utcnow()+datetime.timedelta(hours=3)+datetime.timedelta(days=3)).strftime('%Y-%m-%d');ok(pc['e']==want,'shop pilot lasts 3 days: '+pc['e']+' vs '+want)
    ad.click('#ck');ad.click('#ip');ok('already issued for this order' in ad.inner_text('#res'),'same order cannot get a second code')
    ad.fill('#om',order(**{**base,'name':'kasarani hardware','phone':'0733444555','mode':'pilot','code':'','date':'2026-11-24'}));ad.click('#ck');ad.click('#ip');ok('already had a free pilot' in ad.inner_text('#res'),'same business cannot get another free pilot')
    inst_msg=order(role='inst',plan=0,name='Sunrise Ltd',town='Nakuru',phone='0700123456',lic='EPRA/T2/555',mode='pay',code='RTB5LMN777',date=D)
    ad.fill('#om',inst_msg);ad.click('#ck');ad.click('#is');ok('Tick the box' in ad.inner_text('#res'),'installer needs licence tick');ad.check('#lc');ad.click('#is');inst_code=ad.input_value('#code');ok(inst_code.startswith('FC1.'),'installer code issued')
    expired=ad.evaluate("signAccess({r:'FC-OLD111',n:'Old Shop',w:'254700000000',p:'Shop',k:'shop',l:'',e:'2020-01-01',i:'2019-12-01'},PRIV)")
    xss=ad.evaluate("""signAccess({r:'FC-XSS111',n:'<img src=x onerror="window.__x=1">',w:'254700000000',p:'Shop',k:'shop',l:'',e:'2030-01-01',i:'2026-11-22'},PRIV)""")
    ok('Ruaka Hardware' in ad.inner_text('#lg') and 'pilot' in ad.inner_text('#lg'),'ledger shows entries')
    # ---- app with config
    cfg=json.load(open(os.path.join(SITE,'config.json')));cfg.update(publicKey=json.loads(pub),till='123456',operatorWa='254700111222',gateAll=False);json.dump(cfg,open(os.path.join(SITE,'config.json'),'w'))
    srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'-d',SITE],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
    try:
        def fresh():
            c=b.new_context();pg=c.new_page();pg.on('pageerror',lambda e:errs.append('app:'+str(e)));pg.goto(f'http://localhost:{PORT}/index.html');pg.wait_for_timeout(500)
            pg.check('#ok1');pg.click('#acc');return c,pg
        c,pg=fresh()
        pg.click('.bar [data-t=p]');pg.click('#shopm [data-v=pay]');ok('123456' in pg.inner_text('#shoppay'),'till number shown from config.json')
        pg.fill('#shopa','FC1.garbage');pg.click('#shopua');ok('not valid' in pg.inner_text('#shopas'),'garbage code refused')
        parts=shop_code.split('.');tam='.'.join([parts[0],parts[1][:-2]+('AA' if parts[1][-2:]!='AA' else 'BB'),parts[2]])
        pg.fill('#shopa',tam);pg.click('#shopua');ok('not valid' in pg.inner_text('#shopas'),'tampered code refused')
        pg.fill('#shopa',expired);pg.click('#shopua');ok('ran out' in pg.inner_text('#shopas'),'expired code refused with reason')
        pg.fill('#shopa',shop_code);pg.click('#shopua');pg.wait_for_timeout(200);ok('Unlocked for Ruaka Hardware' in pg.inner_text('#shopas'),'valid shop code unlocks')
        pg.click('.bar [data-t=h]');ok('Ruaka Hardware' in pg.inner_text('#h .band'),'home shows who is unlocked')
        pg.click('.bar [data-t=k]');pg.click('#kg');ok('Quote by Ruaka Hardware' in pg.inner_text('#ko'),'cable result branded');pg.click('.bar [data-t=q]');pg.click('#go');pg.wait_for_timeout(200);ok('Send to Ruaka Hardware' in pg.inner_text('#tl'),'button says Send to the shop')
        pg.evaluate("window.__u=[];window.open=u=>{window.__u.push(u)}");pg.click('#tl');pg.fill('#ph2','0712345678');pg.check('#cs2');pg.click('[data-i="0"]');u=up.unquote(pg.evaluate("(window.__u.filter(x=>x).pop())||''"));ok('wa.me/254722111222' in u and 'Customer phone: 0712345678' in u,'lead goes to the shop WhatsApp: '+u[:80]+' | err='+pg.inner_text('#lerr')+' | rows='+str(pg.locator('#ld [data-i]').count())+' | U='+str(pg.evaluate('window.__u')))
        pg.reload();pg.wait_for_timeout(600);ok('Ruaka Hardware' in pg.inner_text('#h .band'),'access remembered after reload')
        c.close()
        # installer
        c,pg=fresh();pg.click('.bar [data-t=i]');pg.fill('#insta',inst_code);pg.click('#instua');pg.wait_for_timeout(200);ok('Unlocked for Sunrise Ltd' in pg.inner_text('#instas'),'installer code unlocks')
        pg.click('.bar [data-t=q]');pg.click('#go');pg.wait_for_timeout(200);ok('EPRA licence EPRA/T2/555' in pg.inner_text('#qo .band'),'solar quote shows installer licence');ok('Send to a licensed installer' in pg.inner_text('#tl'),'installer button label');c.close()
        # xss
        c,pg=fresh();pg.click('.bar [data-t=p]');pg.fill('#shopa',xss);pg.click('#shopua');pg.wait_for_timeout(200);pg.click('.bar [data-t=k]');pg.click('#kg');ok(pg.evaluate('window.__x')is None,'name cannot run script');ok('<img' in pg.inner_text('#ko .band'),'name shown as plain text');c.close()
        # lock whole app
        cfg['gateAll']=True;json.dump(cfg,open(os.path.join(SITE,'config.json'),'w'))
        c,pg=fresh();pg.wait_for_timeout(300);ok(pg.is_visible('#lock'),'app locked when gateAll');ok('wa.me/254700111222' in pg.get_attribute('#lkw','href'),'lock has WhatsApp to you')
        pg.fill('#lk','nope');pg.click('#lku');ok('not valid' in pg.inner_text('#lke'),'wrong code stays locked');ok(pg.is_visible('#lock'),'still locked')
        pg.fill('#lk',pilot_code);pg.click('#lku');pg.wait_for_timeout(200);ok(not pg.is_visible('#lock'),'valid code opens the app');ok(not pg.eval_on_selector('main','m=>m.inert'),'app usable after unlock');c.close()
        # live rules refresh
        cfg['gateAll']=False;json.dump(cfg,open(os.path.join(SITE,'config.json'),'w'))
        rj=json.load(open(os.path.join(SITE,'rules.json')));n0=len(rj['rules']);rj['checked']='2026-12-01';rj['rules'].append(dict(id='new1',t=['cable'],k='Law',x='A brand new rule was added to the list for testing the update.',s='Test source',u='https://example.com/x'));json.dump(rj,open(os.path.join(SITE,'rules.json'),'w'))
        c,pg=fresh();pg.click('#rl');ok('1 Dec 2026' in pg.inner_text('#rmeta'),'rules.json date shown on open: '+pg.inner_text('#rmeta'));pg.click('#rch [data-rt=cable]');ok('brand new rule' in pg.inner_text('#rlist'),'new rule appears')
        rj['checked']='2027-01-05';rj['rules'][0]['u']='javascript:alert(1)';json.dump(rj,open(os.path.join(SITE,'rules.json'),'w'));pg.click('#rup');pg.wait_for_timeout(400);ok('could not be used' in pg.inner_text('#rmeta'),'unsafe update rejected: '+pg.inner_text('#rmeta'));ok('brand new rule' in pg.inner_text('#rlist'),'kept the good copy')
        os.remove(os.path.join(SITE,'rules.json'));pg.click('#rup');pg.wait_for_timeout(400);ok('saved copy' in pg.inner_text('#rmeta'),'missing rules.json falls back to saved copy');c.close()
        # no config at all (artifact preview case): app still works
        os.remove(os.path.join(SITE,'config.json'));c,pg=fresh();pg.click('.bar [data-t=p]');pg.fill('#shopa','FC1.x.y');pg.click('#shopua');ok('not set up' in pg.inner_text('#shopas'),'no config: clear message');pg.click('.bar [data-t=k]');pg.click('#kg');ok(pg.is_visible('#ko .hero'),'tools still work without config');c.close()
    finally:srv.terminate()
    b.close()
ok(not errs,'page errors: '+str(errs[:3]))
print('ACCESS BROWSER QA:','ALL PASS' if not fails else f'{len(fails)} FAILS')
sys.exit(1 if fails else 0)
