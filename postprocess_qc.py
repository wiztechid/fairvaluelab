# Final pipeline QC: preserve upstream engine generation and publish consistent status/quality semantics.
import json, glob, math, os
import numpy as np
from des_universe import TICKERS, SECTOR_BY_TICKER, DES_SOURCE
OUT='data'
QC_VERSION='3.12-atomic-qc'
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
def capped_weights(keep,cap=.60):
    raw=np.array([max(float(m.get('rawWeight') or .01),.01) for m in keep]);w=raw/raw.sum()
    for _ in range(8):
        fams={}
        for i,m in enumerate(keep):fams.setdefault(family(m),[]).append(i)
        excess=0;free=[]
        for idxs in fams.values():
            total=sum(w[i] for i in idxs)
            if total>cap:
                scale=cap/total;excess+=total-cap
                for i in idxs:w[i]*=scale
            else:free+=idxs
        if excess<1e-9 or not free:break
        den=sum(w[i] for i in free)
        if den<=0:break
        for i in free:w[i]+=excess*w[i]/den
    return w/w.sum()
def process(path):
    try:d=json.load(open(path,encoding='utf-8'))
    except:return None
    upstream=d.get('engineVersion') or 'unknown';price=d.get('price');methods=d.get('methods') or [];q=d.setdefault('quality',{});guards=q.setdefault('guards',[]);keep=robust_keep(methods,price)
    independent=[m for m in keep if m.get('countsForIndependence',True)];ifam={family(m) for m in independent};suf=len(keep)>=2 and len(ifam)>=2
    if suf:
        weights=capped_weights(keep,.60)
        for m,w in zip(keep,weights):m['included']=True;m['normalizedWeight']=float(w)
        comp=lambda k:sum(m[k]*m['normalizedWeight'] for m in keep);bear,base,bull=comp('bear'),comp('base'),comp('bull');a=np.array([m['base'] for m in keep],float);disp=float(np.std(a)/np.mean(a)) if np.mean(a)>0 else None;agr='HIGH' if disp<.18 else 'MEDIUM' if disp<.32 else 'LOW'
    else:
        bear=base=bull=disp=None;agr='INSUFFICIENT';msg='Composite FV tidak diterbitkan: minimal 2 keluarga valuasi yang benar-benar independen wajib lolos QC.'
        if msg not in guards:guards.append(msg)
    d['fairValue']={'bear':bear,'base':base,'bull':bull,'dispersion':disp,'agreement':agr,'available':suf};q['validMethodCount']=len(keep);q['independentFamilies']=len(ifam);q['outlierMethodCount']=sum(m.get('qcStatus')=='OUTLIER' for m in methods)
    score=q.get('dataScore')
    if finite(score):q['dataLabel']='BAIK' if score>=80 else ('CUKUP' if score>=60 else 'TERBATAS')
    fresh=d.get('freshnessStatus','FRESH');d['analysisStatus']='STALE' if fresh=='STALE' else ('SIAP' if suf else 'TERBATAS')
    d['engineGeneration']=upstream;d['qcVersion']=QC_VERSION;d['engineVersion']=f'{upstream}+{QC_VERSION}'
    json.dump(d,open(path,'w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False);return d
rows={}
for path in glob.glob(os.path.join(OUT,'*.json')):
    if path.endswith('summary.json'):continue
    d=process(path)
    if d:rows[(d.get('ticker') or os.path.basename(path)).replace('.JK','').replace('.json','')]=d
old={}
try:old=json.load(open(os.path.join(OUT,'summary.json'),encoding='utf-8'))
except:pass
errmap={e.get('ticker'):e for e in old.get('errors',[]) if e.get('ticker')};stocks=[];errors=[]
for ticker in TICKERS:
    d=rows.get(ticker)
    if d:
        q=d.get('quality',{});f=d.get('fairValue',{});cp=d.get('companyProfile',{});fresh=d.get('freshnessStatus','FRESH');status='STALE' if fresh=='STALE' else ('SIAP' if f.get('available') else 'TERBATAS')
        stocks.append({'ticker':ticker,'sector':cp.get('sector') or SECTOR_BY_TICKER.get(ticker),'valuationProfile':cp.get('valuationProfile'),'price':d.get('price'),**f,'dataLabel':q.get('dataLabel'),'validMethods':q.get('validMethodCount',0),'independentFamilies':q.get('independentFamilies',0),'outliers':q.get('outlierMethodCount',0),'status':status,'freshnessStatus':fresh,'engineVersion':d.get('engineVersion')})
    else:
        e=errmap.get(ticker,{});errors.append({'ticker':ticker,'sector':SECTOR_BY_TICKER.get(ticker),'error':e.get('error','Belum ada JSON hasil yang dapat digunakan.'),'status':e.get('status','GAGAL_FETCH')})
old['universeSource']=DES_SOURCE;old['requested']=len(TICKERS);old['count']=len(stocks);old['stocks']=stocks;old['errors']=errors;old['qcVersion']=QC_VERSION;old['statusCounts']={'SIAP':sum(x['status']=='SIAP' for x in stocks),'TERBATAS':sum(x['status']=='TERBATAS' for x in stocks),'STALE':sum(x['status']=='STALE' for x in stocks),'ERROR':len(errors)}
json.dump(old,open(os.path.join(OUT,'summary.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False);print('QC:',len(TICKERS),'DES =',old['statusCounts'])