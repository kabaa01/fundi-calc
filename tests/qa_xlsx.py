import json,subprocess,shutil,sys
from openpyxl import load_workbook
import os
SRC=os.environ.get('FC_XLSX','Borehole___Solar_Pump_Audit___E2E_Automation___QA_Sandbox.xlsx')
cases=[dict(county='Kiambu',depth=180,stat=85,dyn=125,yld=5,elev=15,run=120,pipe='40mm HDPE_PN16',need=15,win=5,vkwp=5.5),
 dict(county='Turkana',depth=250,stat=120,dyn=180,yld=8,elev=30,run=300,pipe='50mm HDPE_PN16',need=30,win=6,vkwp=9),
 dict(county='Nakuru',depth=100,stat=40,dyn=60,yld=12,elev=10,run=50,pipe='63mm HDPE_PN10',need=40,win=6,vkwp=4),
 dict(county='Kilifi',depth=60,stat=20,dyn=30,yld=3,elev=5,run=20,pipe='32mm HDPE_PN10',need=12,win=5,vkwp=2),
 dict(county='Kajiado',depth=220,stat=100,dyn=160,yld=4,elev=20,run=200,pipe='40mm GI_MEDIUM',need=25,win=5,vkwp=7),
 dict(county='Nyeri',depth=150,stat=70,dyn=90,yld=20,elev=8,run=80,pipe='50mm GI_MEDIUM',need=60,win=5,vkwp=10),
 dict(county='Meru',depth=90,stat=30,dyn=50,yld=2,elev=3,run=10,pipe='40mm HDPE_PN10',need=20,win=5,vkwp=3)]
json.dump(cases,open('/tmp/fc_cases.json','w'))
js=json.loads(subprocess.check_output(['node',os.path.join(os.path.dirname(os.path.abspath(__file__)),'qa_pump.js'),'/tmp/fc_cases.json']))
M={'depth':'B13','stat':'B14','dyn':'B15','yld':'B16','elev':'B17','run':'B18','need':'B21','win':'B22','vkwp':'B23','county':'B11'}
bad=0
for n,c in enumerate(cases):
    p=f'/home/claude/c{n}.xlsx';shutil.copy(SRC,p);wb=load_workbook(p);ws=wb['1_Layman_Simulator']
    for k,a in M.items(): ws[a]=c[k]
    ws['B19']=int(c['pipe'].split('mm')[0]);ws['B20']=c['pipe'].split('mm ')[1];wb.save(p)
    subprocess.run(['python3','/mnt/skills/public/xlsx/scripts/recalc.py',p,'90'],capture_output=True)
    v=load_workbook(p,data_only=True)['1_Layman_Simulator'];j=js[n]
    chk=[('Q','F10'),('v','F11'),('hf','F13'),('mf','F14'),('tdh','F15'),('ph','F17'),('pe','F18'),('kwp','F19'),('panels','F20'),('surplus','F21'),('save','F22')]
    for k,a in chk:
        x,y=j[k],v[a].value
        if abs(x-y)>0.011: bad+=1;print('MISMATCH case',n,k,'js',x,'xlsx',y)
    sj='DANGER' if j['surge'] else 'PASS'
    if not str(v['F16'].value).startswith(sj): bad+=1;print('MISMATCH surge',n,sj,v['F16'].value)
    print('case',n,'tdh',j['tdh'],v['F15'].value,'kwp',j['kwp'],v['F19'].value,'ok')
print('XLSX CROSS-CHECK:','ALL MATCH' if not bad else f'{bad} MISMATCHES')
