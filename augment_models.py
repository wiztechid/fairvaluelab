import json, math
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf
DATA=Path('data')
def num(x):
    try:v=float(x);return v if math.isfinite(v) else None
    except:return None
def row(df,names):
    if df is None or df.empty:return None
    for name in names:
        if name in df.index:
            try:return num(df.loc[name].iloc[0])
            except:pass
    return None
def annual(df,names):
    if df is None or df.empty:return []
    for name in names:
        if name in df.index:return sorted([(pd.Timestamp(d),float(v)) for d,v in df.loc[name].items() if pd.notna(v) and num(v) is not None])
    return []
def diag(d,name,family,reason,inputs=None,status='NOT_APPLICABLE'):d.setdefault('methodDiagnostics',[]).append({'name':name,'family':family,'status':status,'reason':reason,'inputs':inputs or {}})
def add(d,name,family,bear,base,bull,c,r,explain,bands=None):
    p=num(d.get('price'));v=[num(bear),num(base),num(bull)]
    if not p or not all(x is not None and x>0 for x in v):diag(d,name,family,'Hasil nol/negatif/tidak lengkap; tidak masuk Composite FV.',{'bear':v[0],'base':v[1],'bull':v[2]},'NEGATIVE');return False
    if not all(.05*p<=x<=5*p for x in v):diag(d,name,family,'Hasil di luar economic sanity guard 0,05x–5x harga pasar.',{'bear':v[0],'base':v[1],'bull':v[2],'price':p},'OUTLIER');return False
    d.setdefault('methods',[]).append({'name':name,'family':family,'bear':v[0],'base':v[1],'bull':v[2],'confidence':c,'relevance':r,'rawWeight':c*r,'bands':bands,'warning':None,'explanation':explain,'included':False,'normalizedWeight':0,'qcStatus':'CANDIDATE'});return True
def bands(vals,lo=.1,hi=40):
    a=np.array([x for x in vals if x is not None and lo<=x<=hi],float)
    if len(a)<3:return None
    m=float(np.median(a));mad=float(np.median(np.abs(a-m)));s=1.4826*mad
    if s<=1e-9:s=max(.1*m,.1)
    return max(lo,m-s),m,min(hi,m+s),s
def rebuild(d):
    p=num(d.get('price'));cand=[]
    for m in d.get('methods') or []:
        v=[num(m.get(k)) for k in ('bear','base','bull')];ok=p and all(x is not None and x>0 and .05*p<=x<=5*p for x in v);m['included']=False;m['normalizedWeight']=0
        if ok:cand.append(m)
        else:m['qcStatus']='OUTLIER'
    use=[]
    if cand:
        logs=np.log([m['base'] for m in cand]);med=float(np.median(logs));mad=float(np.median(np.abs(logs-med)))
        for m,z in zip(cand,logs):
            robust=True if len(cand)<3 or mad<1e-9 else abs(z-med)<=3.5*1.4826*mad
            if robust and max(m['base']/p,p/m['base'])<=5:use.append(m)
            else:m['qcStatus']='OUTLIER'
    fam={m.get('family') for m in use};suf=len(use)>=2 and len(fam)>=2
    if suf:
        tw=sum(max(num(m.get('rawWeight')) or 0,.01) for m in use)
        for m in d.get('methods') or []:m['included']=m in use;m['normalizedWeight']=max(num(m.get('rawWeight')) or 0,.01)/tw if m in use else 0;m['qcStatus']='INCLUDED' if m in use else m.get('qcStatus','EXCLUDED')
        comp=lambda k:sum(m[k]*m['normalizedWeight'] for m in use);bear,base,bull=comp('bear'),comp('base'),comp('bull');a=np.array([m['base'] for m in use]);disp=float(np.std(a)/np.mean(a)) if np.mean(a) else None;agr='HIGH' if disp<.18 else 'MEDIUM' if disp<.32 else 'LOW'
    else:bear=base=bull=disp=None;agr='INSUFFICIENT'
    d['fairValue']={'bear':bear,'base':base,'bull':bull,'dispersion':disp,'agreement':agr,'available':suf};q=d.setdefault('quality',{});q['validMethodCount']=len(use) if suf else 0;q['independentFamilies']=len(fam) if suf else 0;q['diagnosticCount']=len(d.get('methodDiagnostics') or []);d['analysisStatus']='SIAP' if suf else ('STALE' if d.get('freshnessStatus')=='STALE' else 'TERBATAS')
def augment(path):
    d=json.load(open(path,encoding='utf-8'));d['methodDiagnostics']=[];ticker=d.get('ticker') or path.stem+'.JK';p=num(d.get('price'));raw=d.get('raw') or {};shares=num(raw.get('shares'));factor=num(raw.get('fxFactor')) or 1.0
    if not p or not shares:diag(d,'Fallback models','data','Harga atau jumlah saham tidak tersedia.',status='INVALID');return d
    t=yf.Ticker(ticker);inc=t.income_stmt;bs=t.balance_sheet;sector=(d.get('companyProfile') or {}).get('sector') or '';existing={m.get('name') for m in d.get('methods') or []};eps=num(raw.get('epsTTM'));bvps=num(raw.get('bvps'));fcf=num(raw.get('fcf'))
    if eps is None:diag(d,'P/E & Graham','earnings','EPS tidak tersedia/tervalidasi.')
    elif eps<=0:diag(d,'P/E & Graham','earnings','EPS/laba negatif; metode dilewati.',{'eps':eps},'NEGATIVE')
    if bvps is None:diag(d,'PBV & Graham','book','BVPS tidak tersedia/tervalidasi.')
    elif bvps<=0:diag(d,'PBV & Graham','book','Ekuitas/BVPS negatif; metode dilewati.',{'bvps':bvps},'NEGATIVE')
    if fcf is None:diag(d,'DCF & FCF Yield','cashflow','FCF tidak tersedia/tervalidasi.')
    elif fcf<=0:diag(d,'DCF & FCF Yield','cashflow','FCF negatif; metode cashflow dilewati.',{'fcf':fcf},'NEGATIVE')
    if 'Historical EV/EBITDA' not in existing and 'Keuangan' not in sector:
        debt0=row(bs,['Total Debt']);cash0=row(bs,['Cash Cash Equivalents And Short Term Investments','Cash And Cash Equivalents','Cash Financial']);debt=(debt0 or 0)*factor;cash=(cash0 or 0)*factor;net=debt-cash;ebs=[(dt,e*factor) for dt,e in annual(inc,['EBITDA','Normalized EBITDA'])];eb0=row(inc,['EBITDA','Normalized EBITDA']);eb=eb0*factor if eb0 is not None else None
        if eb is None:diag(d,'Historical EV/EBITDA','enterprise','EBITDA tidak tersedia.')
        elif eb<=0:diag(d,'Historical EV/EBITDA','enterprise','EBITDA negatif/nol.',{'ebitda':eb},'NEGATIVE')
        else:
            try:h=t.history(period='5y',auto_adjust=False)
            except:h=pd.DataFrame()
            mult=[]
            if not h.empty:
                for dt,e in ebs:
                    if e<=0:continue
                    px=h[h.index.year==dt.year].Close.dropna()
                    if len(px):
                        for x in px.iloc[::max(1,len(px)//24)]:
                            m=(float(x)*shares+net)/e
                            if .5<=m<=30:mult.append(m)
            b=bands(mult,.5,30)
            if b:
                lo,med,hi,s=b;fv=lambda x:(x*eb-net)/shares;add(d,'Historical EV/EBITDA','enterprise',fv(lo),fv(med),fv(hi),.82,1,'Enterprise value berbasis median EV/EBITDA historis dengan debt/cash/EBITDA dinormalisasi ke mata uang harga.',{'mean':med,'sd':s})
            else:diag(d,'Historical EV/EBITDA','enterprise','Riwayat EV/EBITDA valid belum cukup.')
    if 'Graham Number' not in existing and eps and eps>0 and bvps and bvps>0:
        g=math.sqrt(22.5*eps*bvps);add(d,'Graham Number','fundamental',g*.8,g,g*1.2,.6,.55,'Cross-check konservatif berbasis EPS dan BVPS tervalidasi.')
    if 'Historical Dividend Yield' not in existing:
        try:
            div=t.dividends
            if div is None or len(div)<3:diag(d,'Historical Dividend Yield','income','Riwayat pembayaran dividen belum cukup.')
            else:
                div=div[div.index>=div.index.max()-pd.DateOffset(years=5)];ad=div.groupby(div.index.year).sum();ad=ad[ad>0];h=t.history(period='5y',auto_adjust=False);ys=[]
                for y,dps in ad.items():
                    px=h[h.index.year==y].Close.dropna()
                    if len(px):
                        z=float(dps)/float(px.median())
                        if .005<=z<=.20:ys.append(z)
                if len(ys)>=3:
                    med=float(np.median(ys));mad=float(np.median(np.abs(np.array(ys)-med)));sig=max(1.4826*mad,.001);dps=float(ad.iloc[-1]);add(d,'Historical Dividend Yield','income',dps/min(.25,med+sig),dps/med,dps/max(.005,med-sig),.68,.65,'Dividend per saham terbaru terhadap median dividend yield historis 5 tahun.',{'mean':med,'sd':sig})
                else:diag(d,'Historical Dividend Yield','income','Riwayat dividend yield valid kurang dari 3 periode.')
        except Exception as e:diag(d,'Historical Dividend Yield','income','Model dividen gagal: '+str(e)[:90],status='INVALID')
    rebuild(d);d['engineVersion']='3.8-all-tickers-fx';return d
changed=failed=0
for p in DATA.glob('*.json'):
    if p.name in ('summary.json','errors.json'):continue
    try:d=augment(p);json.dump(d,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False);changed+=1
    except Exception as e:failed+=1;print('AUGMENT_ERR',p.stem,e)
print('AUGMENT_DONE changed=',changed,'failed=',failed)