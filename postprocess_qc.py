import json, glob, math, os
import numpy as np
from des_universe import TICKERS, SECTOR_BY_TICKER, DES_SOURCE
OUT='data'
def finite(x):return isinstance(x,(int,float)) and math.isfinite(x)
def family(m):
    if m.get('family'):return m['family']
    n=m.get('name','');return 'earnings' if n.startswith('Historical P/E') else 'book' if n.startswith('Historical PBV') else 'cashflow' if n in ('DCF','FCF Yield') else n
def robust_keep(methods,price):
    cand=[]
    for m in methods:
        vals=[m.get('bear'),m.get('base'),m.get('bull')];sane=price and all(finite(v) and v>0 and .05*price<=v<=5*price for v in vals);m['qcStatus']='CANDIDATE' if sane else 'OUTLIER';m['included']=False;m['normalizedWeight']=0
        if sane:cand.append(m)
        else:m['qcReason']='Ditolak: hasil di luar economic sanity range 0.05x–5x harga pasar.'
    if len(cand)<2:return []
    logs=np.log(np.array([m['base'] for m in cand],float));med=float(np.median(logs));mad=float(np.median(np.abs(logs-med)));keep=[]
    for m,l in zip(cand,logs):
        ratio=math.exp(abs(float(l)-med));z=abs(float(l)-med)/(1.4826*mad) if mad>1e-9 else 0
        if ratio<=2.5 and z<=3.5:keep.append(m);m['qcStatus']='VALID'
        else:m['qcStatus']='OUTLIER';m['qcReason']=f'Ditolak cross-method outlier: deviasi {ratio:.2f}x dari median metode.'
    return keep
def process(path):
    try:d=json.load(open(path,encoding='utf-8'))
    except:return None
    price=d.get('price');methods=d.get('methods') or [];q=d.setdefault('quality',{});guards=q.setdefault('guards',[]);keep=robust_keep(methods,price);fam={family(m) for m in keep};suf=len(keep)>=2 and len(fam)>=2
    if suf:
        tw=sum(float(m.get('rawWeight') or 0) for m in keep)
        if tw<=0:tw=float(len(keep));[m.update(rawWeight=1) for m in keep]
        for m in keep:m['included']=True;m['normalizedWeight']=float(m.get('rawWeight') or 0)/tw
        comp=lambda k:sum(m[k]*m['normalizedWeight'] for m in keep);bear,base,bull=comp('bear'),comp('base'),comp('bull');a=np.array([m['base'] for m in keep],float);disp=float(np.std(a)/np.mean(a)) if np.mean(a)>0 else None;agr='HIGH' if disp<.18 else 'MEDIUM' if disp<.32 else 'LOW'
    else:
        bear=base=bull=disp=None;agr='INSUFFICIENT';msg='Composite FV tidak diterbitkan setelah QC: minimal 2 keluarga valuasi independen wajib lolos.'
        if msg not in guards:guards.append(msg)
    d['fairValue']={'bear':bear,'base':base,'bull':bull,'dispersion':disp,'agreement':agr,'available':suf};q['validMethodCount']=len(keep) if suf else 0;q['independentFamilies']=len(fam) if suf else 0;q['outlierMethodCount']=sum(m.get('qcStatus')=='OUTLIER' for m in methods)
    if not suf and q.get('dataLabel')=='BAIK':q['dataLabel']='CUKUP'
    fresh=d.get('freshnessStatus','FRESH');d['analysisStatus']='STALE' if fresh=='STALE' else ('SIAP' if suf else 'TERBATAS');d['engineVersion']='3.8-all-tickers-fx-qc';json.dump(d,open(path,'w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False);return d
rows={}
for path in glob.glob(os.path.join(OUT,'*.json')):
    if path.endswith('summary.json'):continue
    d=process(path)
    if d:rows[(d.get('ticker') or os.path.basename(path)).replace('.JK','').replace('.json','')]=d
old={}
try:old=json.load(open(os.path.join(OUT,'summary.json'),encoding='utf-8'))
except:pass
errmap={e.get('ticker'):e for e in old.get('errors',[]) if e.get('ticker')}
stocks=[];errors=[]
for ticker in TICKERS:
    d=rows.get(ticker)
    if d:
        q=d.get('quality',{});f=d.get('fairValue',{});cp=d.get('companyProfile',{});fresh=d.get('freshnessStatus','FRESH');status='STALE' if fresh=='STALE' else ('SIAP' if f.get('available') else 'TERBATAS')
        stocks.append({'ticker':ticker,'sector':cp.get('sector') or SECTOR_BY_TICKER.get(ticker),'valuationProfile':cp.get('valuationProfile'),'price':d.get('price'),**f,'dataLabel':q.get('dataLabel'),'validMethods':q.get('validMethodCount',0),'outliers':q.get('outlierMethodCount',0),'status':status,'freshnessStatus':fresh})
    else:
        e=errmap.get(ticker,{});errors.append({'ticker':ticker,'sector':SECTOR_BY_TICKER.get(ticker),'error':e.get('error','Belum ada JSON hasil yang dapat digunakan.'),'status':e.get('status','GAGAL_FETCH')})
old['universeSource']=DES_SOURCE;old['requested']=len(TICKERS);old['count']=len(stocks);old['stocks']=stocks;old['errors']=errors;old['statusCounts']={'SIAP':sum(x['status']=='SIAP' for x in stocks),'TERBATAS':sum(x['status']=='TERBATAS' for x in stocks),'STALE':sum(x['status']=='STALE' for x in stocks),'ERROR':len(errors)}
json.dump(old,open(os.path.join(OUT,'summary.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False)
print('QC:',len(TICKERS),'DES =',old['statusCounts'])