# Evidence ladder after QC: full FV > indicative FV > single-method reference > unvalued.
# Market price is never a valuation target; it is only a QC/review guard.
import json, math
from pathlib import Path
DATA=Path('data')
def finite(x): return isinstance(x,(int,float)) and math.isfinite(x)
def fam(m): return m.get('family') or m.get('name') or 'unknown'
def process(d):
    if (d.get('fairValue') or {}).get('available'): return d
    if d.get('freshnessStatus')=='STALE': return d
    methods=d.get('methods') or [];q=d.setdefault('quality',{});f=d.setdefault('fairValue',{});guards=q.setdefault('guards',[])
    keep=[m for m in methods if m.get('qcStatus')=='VALID' and all(finite(m.get(k)) and m.get(k)>0 for k in ('bear','base','bull'))]
    independent=[m for m in keep if m.get('countsForIndependence',True)];ifams={fam(m) for m in independent};q['validMethodCount']=len(keep);q['independentFamilies']=len(ifams)
    score=q.get('dataScore') if finite(q.get('dataScore')) else 0
    if not keep:
        f.update({'bear':None,'base':None,'bull':None,'available':False,'indicative':False,'referenceOnly':False,'evidenceLevel':'UNVALUED'})
        q['valuationConfidence']=0;d['analysisStatus']='BELUM_DINILAI';d['valuationReview']={'required':False,'status':'NO_DEFENSIBLE_METHOD','reason':'NO_VALID_METHOD','policy':'No value is fabricated or anchored to market price.'}
        msg='Belum dapat dinilai: tidak ada metode fundamental yang lolos QC. Harga pasar hanya ditampilkan sebagai harga pasar.'
        if msg not in guards:guards.append(msg)
        return d
    if len(keep)==1:
        m=keep[0];bear,base,bull=(m[k] for k in ('bear','base','bull'))
        # Preserve the method-derived range. Do not pull it toward current price.
        f.update({'bear':bear,'base':base,'bull':bull,'dispersion':None,'agreement':'SINGLE_METHOD','available':False,'indicative':False,'referenceOnly':True,'evidenceLevel':'REFERENCE','referenceMethod':m.get('name')})
        conf=18+(8 if score>=80 else 4 if score>=60 else 0)+(4 if m.get('countsForIndependence',True) else 0);q['valuationConfidence']=min(35,int(round(conf)));d['analysisStatus']='REFERENSI'
        d['valuationReview']={'required':False,'status':'SINGLE_METHOD','reason':'ONLY_ONE_VALID_METHOD','policy':'Reference value is method-derived, not a composite fair value and not anchored to market.'}
        msg=f"Referensi Nilai dari satu metode valid ({m.get('name','metode')}); belum cukup bukti untuk FV gabungan."
        if msg not in guards:guards.append(msg)
        return d
    raw=[max(float(m.get('rawWeight') or .01),.01) for m in keep];total=sum(raw);w=[x/total for x in raw]
    for m,x in zip(keep,w):m['indicativeWeight']=x
    comp=lambda k:sum(m[k]*x for m,x in zip(keep,w));bear,base,bull=comp('bear'),comp('base'),comp('bull');spread=max((bull-bear)/2,base*.15);bear=max(base-spread,min(m['bear'] for m in keep));bull=max(base+spread,max(m['bull'] for m in keep));vals=[m['base'] for m in keep];mean=sum(vals)/len(vals);disp=(sum((x-mean)**2 for x in vals)/len(vals))**.5/mean if mean else None
    f.update({'bear':bear,'base':base,'bull':bull,'dispersion':disp,'agreement':'LIMITED','available':False,'indicative':True,'referenceOnly':False,'evidenceLevel':'INDICATIVE'});q['indicativeMethodCount']=len(keep);conf=25+min(15,4*len(keep))+min(10,5*len(ifams))+(8 if score>=80 else 4 if score>=60 else 0);q['valuationConfidence']=min(55,int(round(conf)));d['analysisStatus']='INDIKATIF';d['valuationReview']={'required':False,'status':'LIMITED_EVIDENCE','reason':'INSUFFICIENT_INDEPENDENT_FAMILIES','policy':'Indicative FV is method-derived; market price is not a valuation anchor.'}
    msg='FV Indikatif diterbitkan karena >=2 metode valid tersedia tetapi bukti keluarga independen belum cukup untuk Composite FV penuh.'
    if msg not in guards:guards.append(msg)
    return d
rows={}
for p in DATA.glob('*.json'):
    if p.name in ('summary.json','errors.json','idx_disclosures.json','idx_collector_status.json'):continue
    try:
        d=json.load(open(p,encoding='utf-8'))
        if not isinstance(d,dict) or not d.get('ticker'):continue
        d=process(d);json.dump(d,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False);rows[d['ticker'].replace('.JK','')]=d
    except Exception as e:print('EVIDENCE_ERR',p.name,e)
try:
    sp=DATA/'summary.json';s=json.load(open(sp,encoding='utf-8'))
    for x in s.get('stocks',[]):
        d=rows.get(x.get('ticker'))
        if not d:continue
        f=d.get('fairValue',{});q=d.get('quality',{});x.update({'bear':f.get('bear'),'base':f.get('base'),'bull':f.get('bull'),'available':f.get('available',False),'indicative':f.get('indicative',False),'referenceOnly':f.get('referenceOnly',False),'evidenceLevel':f.get('evidenceLevel'),'referenceMethod':f.get('referenceMethod'),'agreement':f.get('agreement'),'status':d.get('analysisStatus'),'valuationConfidence':q.get('valuationConfidence'),'validMethods':q.get('validMethodCount',0),'independentFamilies':q.get('independentFamilies',0)})
    keys=['SIAP','REVIEW','INDIKATIF','REFERENSI','BELUM_DINILAI','STALE'];s['statusCounts']={k:sum(x.get('status')==k for x in s.get('stocks',[])) for k in keys};s['statusCounts']['ERROR']=len(s.get('errors',[]));json.dump(s,open(sp,'w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False)
except Exception as e:print('EVIDENCE_SUMMARY_ERR',e)
print('EVIDENCE_LADDER_DONE')