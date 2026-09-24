# Final pipeline QC: full FV requires independent evidence; single methods remain reference-only.
import json, glob, math, os
import numpy as np
from des_universe import TICKERS, SECTOR_BY_TICKER, DES_SOURCE
OUT='data';QC_VERSION='3.19-sector-waterfall-qc'
def finite(x):return isinstance(x,(int,float)) and math.isfinite(x)
def family(m):
    if m.get('family'):return m['family']
    n=m.get('name','');return 'earnings' if n.startswith('Historical P/E') else 'book' if n.startswith('Historical PBV') else 'cashflow' if n in ('DCF','FCF Yield') else n
def robust_keep(methods,price):
    cand=[]
    for m in methods:
        vals=[m.get('bear'),m.get('base'),m.get('bull')];sane=all(finite(v) and v>0 for v in vals) and vals[0]<=vals[1]<=vals[2];m['qcStatus']='CANDIDATE' if sane else 'OUTLIER';m['included']=False;m['normalizedWeight']=0
        if sane:cand.append(m)
        else:m['qcReason']='Ditolak: skenario fundamental tidak finite/positif/berurutan. Harga pasar tidak digunakan untuk eligibility metode.'
    if len(cand)==1:
        cand[0]['qcStatus']='VALID';return cand
    if not cand:return []
    logs=np.log(np.array([m['base'] for m in cand],float));med=float(np.median(logs));mad=float(np.median(np.abs(logs-med)));keep=[]
    for m,l in zip(cand,logs):
        ratio=math.exp(abs(float(l)-med));z=abs(float(l)-med)/(1.4826*mad) if mad>1e-9 else 0
        if ratio<=3.5 and z<=3.5:keep.append(m);m['qcStatus']='VALID'
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
    # data/ also contains collector caches (e.g. news_raw.json) that are not ticker objects.
    if not isinstance(d,dict) or not d.get('ticker'):return None
    upstream=d.get('engineGeneration') or d.get('engineVersion') or 'unknown';price=d.get('price');methods=d.get('methods') or [];q=d.setdefault('quality',{});guards=q.setdefault('guards',[]);keep=robust_keep(methods,price)
    independent=[m for m in keep if m.get('countsForIndependence',True)];ifam={family(m) for m in independent};suf=len(keep)>=2 and len(ifam)>=2
    if suf:
        weights=capped_weights(keep,.60)
        for m,w in zip(keep,weights):m['included']=True;m['normalizedWeight']=float(w)
        comp=lambda k:sum(m[k]*m['normalizedWeight'] for m in keep);bear,base,bull=comp('bear'),comp('base'),comp('bull');a=np.array([m['base'] for m in keep],float);disp=float(np.std(a)/np.mean(a)) if np.mean(a)>0 else None;agr='HIGH' if disp<.18 else 'MEDIUM' if disp<.32 else 'LOW'
    else:
        bear=base=bull=disp=None;agr='INSUFFICIENT';msg='Composite FV tidak diterbitkan: minimal 2 keluarga valuasi independen wajib lolos QC.'
        if msg not in guards:guards.append(msg)
    ratio=(base/price) if suf and price and base else None;large_gap=bool(ratio is not None and (ratio<.50 or ratio>2.0));extreme=bool(ratio is not None and (ratio<.25 or ratio>3.0));review=[]
    if extreme:
        direction='BELOW_MARKET' if ratio<.25 else 'ABOVE_MARKET';review.append('EXTREME_VALUATION');guards.append(f'Extreme Valuation Review: Base FV = {ratio:.2f}x harga pasar. Verifikasi currency/unit/shares, earnings quality, siklus, corporate action, dan model; harga pasar tidak menarik FV ke arahnya.')
        d['valuationReview']={'required':True,'status':'REVIEW','reason':'EXTREME_VALUATION','direction':direction,'baseToPrice':ratio,'thresholds':{'low':.25,'high':3.0},'checks':['currency_and_units','shares_and_dilution','earnings_quality_and_oneoffs','cycle_and_corporate_actions','cashflow_confirmation','independent_model_agreement'],'policy':'Market price is a review trigger only; it never pulls fair value toward market.'}
    else:d['valuationReview']={'required':False,'status':'PASS','reason':None,'baseToPrice':ratio,'thresholds':{'low':.25,'high':3.0}}
    d['fairValue']={'bear':bear,'base':base,'bull':bull,'dispersion':disp,'agreement':agr,'available':suf,'indicative':False,'referenceOnly':False};q['validMethodCount']=len(keep);q['independentFamilies']=len(ifam);q['outlierMethodCount']=sum(m.get('qcStatus')=='OUTLIER' for m in methods);q['reviewFlags']=review + (['LARGE_MARKET_GAP'] if large_gap and not extreme else [])
    score=q.get('dataScore')
    if finite(score):q['dataLabel']='BAIK' if score>=80 else ('CUKUP' if score>=60 else 'TERBATAS')
    conf=0
    if suf:
        conf=45+min(20,5*len(ifam))+(15 if agr=='HIGH' else 8 if agr=='MEDIUM' else 2)+(10 if q.get('dataLabel')=='BAIK' else 5 if q.get('dataLabel')=='CUKUP' else 0)
        if extreme:conf-=25
        elif large_gap:conf-=12
        if (d.get('quarterlyNormalization') or {}).get('status') in ('INSUFFICIENT','LIMITED'):conf-=8
        if finite(q.get('cashConversion')) and q['cashConversion']<0:conf-=5
    q['valuationConfidence']=max(0,min(100,int(round(conf))))
    fresh=d.get('freshnessStatus','FRESH');d['analysisStatus']='STALE' if fresh=='STALE' else ('REVIEW' if extreme else ('SIAP' if suf else 'TERBATAS'))
    d['engineGeneration']=upstream;d['qcVersion']=QC_VERSION;d['engineVersion']=f'{upstream}+{QC_VERSION}'
    json.dump(d,open(path,'w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False);return d
rows={}
for path in glob.glob(os.path.join(OUT,'*.json')):
    if path.endswith('summary.json'):continue
    d=process(path)
    if d and d.get('ticker'):rows[d['ticker'].replace('.JK','')]=d
old={}
try:old=json.load(open(os.path.join(OUT,'summary.json'),encoding='utf-8'))
except:pass
errmap={e.get('ticker'):e for e in old.get('errors',[]) if e.get('ticker')};stocks=[];errors=[]
for ticker in TICKERS:
    d=rows.get(ticker)
    if d:
        q=d.get('quality',{});f=d.get('fairValue',{});cp=d.get('companyProfile',{});status=d.get('analysisStatus','TERBATAS')
        stocks.append({'ticker':ticker,'sector':cp.get('sector') or SECTOR_BY_TICKER.get(ticker),'valuationProfile':cp.get('valuationProfile'),'price':d.get('price'),**f,'dataLabel':q.get('dataLabel'),'valuationConfidence':q.get('valuationConfidence'),'validMethods':q.get('validMethodCount',0),'independentFamilies':q.get('independentFamilies',0),'outliers':q.get('outlierMethodCount',0),'reviewFlags':q.get('reviewFlags',[]),'status':status,'freshnessStatus':d.get('freshnessStatus','FRESH'),'engineVersion':d.get('engineVersion')})
    else:
        e=errmap.get(ticker,{});errors.append({'ticker':ticker,'sector':SECTOR_BY_TICKER.get(ticker),'error':e.get('error','Belum ada JSON hasil yang dapat digunakan.'),'status':e.get('status','GAGAL_FETCH')})
old['universeSource']=DES_SOURCE;old['requested']=len(TICKERS);old['count']=len(stocks);old['stocks']=stocks;old['errors']=errors;old['qcVersion']=QC_VERSION;old['statusCounts']={k:sum(x['status']==k for x in stocks) for k in ['SIAP','REVIEW','INDIKATIF','REFERENSI','BELUM_DINILAI','TERBATAS','STALE']};old['statusCounts']['ERROR']=len(errors)
json.dump(old,open(os.path.join(OUT,'summary.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False);print('QC:',len(TICKERS),'DES =',old['statusCounts'])