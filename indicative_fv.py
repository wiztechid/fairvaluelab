# Publish an indicative valuation when usable methods exist but independent evidence is insufficient.
# This layer never upgrades an indicative result to SIAP and never treats market price as a valuation target.
import json, math
from pathlib import Path

DATA=Path('data')
def finite(x): return isinstance(x,(int,float)) and math.isfinite(x)
def fam(m): return m.get('family') or m.get('name') or 'unknown'
def process(d):
    if (d.get('fairValue') or {}).get('available'): return d
    if d.get('freshnessStatus')=='STALE': return d
    price=d.get('price'); methods=d.get('methods') or []
    keep=[m for m in methods if m.get('qcStatus')=='VALID' and all(finite(m.get(k)) and m.get(k)>0 for k in ('bear','base','bull'))]
    if not keep:
        d.setdefault('fairValue',{})['indicative']=False
        return d
    # Graham/cross-check methods may support the range but cannot create independent evidence.
    independent=[m for m in keep if m.get('countsForIndependence',True)]
    ifams={fam(m) for m in independent}
    # Need at least two valid methods for an indicative composite. A single valid method remains reference-only.
    if len(keep)<2:
        d['fairValue'].update({'indicative':False,'referenceOnly':True})
        return d
    raw=[max(float(m.get('rawWeight') or .01),.01) for m in keep]; total=sum(raw); w=[x/total for x in raw]
    for m,x in zip(keep,w): m['indicativeWeight']=x
    comp=lambda k:sum(m[k]*x for m,x in zip(keep,w))
    bear,base,bull=comp('bear'),comp('base'),comp('bull')
    # Wider uncertainty band for limited evidence; preserve method-derived center without anchoring to price.
    spread=max((bull-bear)/2,base*.15)
    bear=max(base-spread, min(m['bear'] for m in keep))
    bull=max(base+spread, max(m['bull'] for m in keep))
    vals=[m['base'] for m in keep]; mean=sum(vals)/len(vals); disp=(sum((x-mean)**2 for x in vals)/len(vals))**.5/mean if mean else None
    d['fairValue'].update({'bear':bear,'base':base,'bull':bull,'dispersion':disp,'agreement':'LIMITED','available':False,'indicative':True,'referenceOnly':False,'evidenceLevel':'INDICATIVE'})
    q=d.setdefault('quality',{}); q['validMethodCount']=len(keep); q['independentFamilies']=len(ifams); q['indicativeMethodCount']=len(keep)
    # Confidence deliberately capped: useful estimate, insufficient independent confirmation.
    score=q.get('dataScore') if finite(q.get('dataScore')) else 0
    conf=25+min(15,4*len(keep))+min(10,5*len(ifams))+(8 if score>=80 else 4 if score>=60 else 0)
    q['valuationConfidence']=min(55,int(round(conf)))
    d['analysisStatus']='INDIKATIF'
    d['valuationReview']={'required':False,'status':'LIMITED_EVIDENCE','reason':'INSUFFICIENT_INDEPENDENT_FAMILIES','policy':'Indicative FV is method-derived and shown with lower confidence; market price is not a valuation anchor.'}
    guards=q.setdefault('guards',[]); msg='FV Indikatif diterbitkan karena >=2 metode valid tersedia tetapi bukti keluarga independen belum cukup untuk Composite FV penuh.'
    if msg not in guards: guards.append(msg)
    return d

rows={}
for p in DATA.glob('*.json'):
    if p.name in ('summary.json','errors.json','idx_disclosures.json','idx_collector_status.json'): continue
    try:
        d=json.load(open(p,encoding='utf-8'))
        if not isinstance(d,dict) or not d.get('ticker'): continue
        d=process(d); json.dump(d,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False)
        rows[d['ticker'].replace('.JK','')]=d
    except Exception as e: print('INDICATIVE_ERR',p.name,e)
try:
    sp=DATA/'summary.json'; s=json.load(open(sp,encoding='utf-8'))
    for x in s.get('stocks',[]):
        d=rows.get(x.get('ticker'))
        if not d: continue
        f=d.get('fairValue',{}); q=d.get('quality',{})
        x.update({'bear':f.get('bear'),'base':f.get('base'),'bull':f.get('bull'),'available':f.get('available',False),'indicative':f.get('indicative',False),'agreement':f.get('agreement'),'status':d.get('analysisStatus'),'valuationConfidence':q.get('valuationConfidence'),'validMethods':q.get('validMethodCount',0),'independentFamilies':q.get('independentFamilies',0)})
    keys=['SIAP','REVIEW','INDIKATIF','TERBATAS','STALE']; s['statusCounts']={k:sum(x.get('status')==k for x in s.get('stocks',[])) for k in keys}; s['statusCounts']['ERROR']=len(s.get('errors',[]))
    json.dump(s,open(sp,'w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False)
except Exception as e: print('INDICATIVE_SUMMARY_ERR',e)
print('INDICATIVE_FV_DONE')
