import json, glob, math, os
import numpy as np

OUT='data'

def finite(x):
    return isinstance(x,(int,float)) and math.isfinite(x)

def family(m):
    if m.get('family'): return m['family']
    n=m.get('name','')
    if n.startswith('Historical P/E'): return 'earnings'
    if n.startswith('Historical PBV'): return 'book'
    if n in ('DCF','FCF Yield'): return 'cashflow'
    return n

def robust_keep(methods, price):
    candidates=[]
    for m in methods:
        vals=[m.get('bear'),m.get('base'),m.get('bull')]
        sane=price and all(finite(v) and v>0 and .05*price <= v <= 5*price for v in vals)
        m['qcStatus']='CANDIDATE' if sane else 'OUTLIER'
        m['included']=False; m['normalizedWeight']=0
        if sane: candidates.append(m)
        else: m['qcReason']='Ditolak: hasil berada di luar economic sanity range 0.05x–5x harga pasar.'
    if len(candidates)<2:return []
    bases=np.array([m['base'] for m in candidates],float)
    logs=np.log(bases)
    med=float(np.median(logs)); mad=float(np.median(np.abs(logs-med)))
    # Cross-method robust filter. Ratio guard remains active even when MAD collapses.
    keep=[]
    for m,l in zip(candidates,logs):
        ratio=math.exp(abs(float(l)-med))
        robust_z=(abs(float(l)-med)/(1.4826*mad)) if mad>1e-9 else 0
        ok=ratio<=2.5 and robust_z<=3.5
        if ok: keep.append(m); m['qcStatus']='VALID'
        else:
            m['qcStatus']='OUTLIER'; m['qcReason']=f'Ditolak cross-method outlier: deviasi {ratio:.2f}x dari median metode.'
    return keep

def process(path):
    try:d=json.load(open(path,encoding='utf-8'))
    except:return None
    price=d.get('price'); methods=d.get('methods') or []; guards=d.setdefault('quality',{}).setdefault('guards',[])
    keep=robust_keep(methods,price)
    fam=set(family(m) for m in keep)
    sufficient=len(keep)>=2 and len(fam)>=2
    if sufficient:
        tw=sum(float(m.get('rawWeight') or 0) for m in keep)
        if tw<=0:tw=float(len(keep)); [m.update(rawWeight=1) for m in keep]
        for m in keep:m['included']=True; m['normalizedWeight']=float(m.get('rawWeight') or 0)/tw
        def comp(k):return sum(m[k]*m['normalizedWeight'] for m in keep)
        bear,base,bull=comp('bear'),comp('base'),comp('bull')
        vals=np.array([m['base'] for m in keep],float); disp=float(np.std(vals)/np.mean(vals)) if np.mean(vals)>0 else None
        agreement='HIGH' if disp is not None and disp<.18 else 'MEDIUM' if disp is not None and disp<.32 else 'LOW'
    else:
        bear=base=bull=disp=None; agreement='INSUFFICIENT'
        msg='Composite FV tidak diterbitkan setelah QC outlier: minimal 2 keluarga valuasi independen wajib lolos.'
        if msg not in guards:guards.append(msg)
    d['fairValue']={'bear':bear,'base':base,'bull':bull,'dispersion':disp,'agreement':agreement,'available':sufficient}
    d['quality']['validMethodCount']=len(keep) if sufficient else 0
    d['quality']['independentFamilies']=len(fam) if sufficient else 0
    d['quality']['outlierMethodCount']=sum(m.get('qcStatus')=='OUTLIER' for m in methods)
    if not sufficient and d['quality'].get('dataLabel')=='BAIK':d['quality']['dataLabel']='CUKUP'
    json.dump(d,open(path,'w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False)
    return d

rows=[]
for path in glob.glob(os.path.join(OUT,'*.json')):
    if path.endswith('summary.json'):continue
    d=process(path)
    if d:rows.append(d)
# Rebuild summary from all retained ticker JSONs so transient fetch failures do not erase Universe coverage.
rows.sort(key=lambda x:x.get('ticker',''))
stocks=[]
for d in rows:
    q=d.get('quality',{}); f=d.get('fairValue',{}); cp=d.get('companyProfile',{})
    stocks.append({'ticker':d.get('ticker','').replace('.JK',''),'sector':cp.get('sector'),'valuationProfile':cp.get('valuationProfile'),'price':d.get('price'),**f,'dataLabel':q.get('dataLabel'),'validMethods':q.get('validMethodCount',0),'outliers':q.get('outlierMethodCount',0)})
old={}
try:old=json.load(open(os.path.join(OUT,'summary.json'),encoding='utf-8'))
except:pass
old['count']=len(stocks); old['stocks']=stocks
json.dump(old,open(os.path.join(OUT,'summary.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False)
print('QC postprocess:',len(stocks),'ticker files; extreme outliers excluded from composites')
