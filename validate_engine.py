import json, math, sys, os
from pathlib import Path
from des_universe import TICKERS
DATA=Path('data');REGRESSION=['AADI','DSSA','BUMI','TPIA','BRMS'];EXPECTED_QC='3.20-family-consensus-qc'
def n(x):return isinstance(x,(int,float)) and math.isfinite(x)
def fail(msg,errors):errors.append(msg);print('FAIL',msg)
def main():
 errors=[];warn=[];status={k:0 for k in ['SIAP','REVIEW','INDIKATIF','REFERENSI','BELUM_DINILAI','STALE','ERROR']};seen=set();versions=set()
 try:sm=json.load(open(DATA/'summary.json',encoding='utf-8'))
 except Exception as e:sm={};fail(f'summary.json missing/invalid: {e}',errors)
 declared_errors={e.get('ticker'):e for e in sm.get('errors',[]) if e.get('ticker')}
 summary_rows={x.get('ticker'):x for x in sm.get('stocks',[]) if x.get('ticker')}
 for ticker in TICKERS:
  p=DATA/f'{ticker}.json'
  if not p.exists():
   if ticker in declared_errors:status['ERROR']+=1;warn.append(f"{ticker}: explicit {declared_errors[ticker].get('status','GAGAL_FETCH')}");continue
   fail(f'{ticker}: missing JSON and no explicit current-run error record',errors);continue
  try:d=json.load(open(p,encoding='utf-8'))
  except Exception as e:fail(f'{ticker}: invalid JSON {e}',errors);continue
  seen.add(ticker);versions.add(d.get('qcVersion'));s=d.get('analysisStatus','BELUM_DINILAI');status[s if s in status else 'BELUM_DINILAI']+=1
  if d.get('qcVersion')!=EXPECTED_QC:fail(f"{ticker}: stale QC version {d.get('qcVersion')}",errors)
  if not d.get('engineGeneration'):fail(f'{ticker}: missing upstream engine generation',errors)
  engine_commit=d.get('engineCommit');expected_commit=os.getenv('CEKVALUASI_ENGINE_SHA');is_stale=d.get('freshnessStatus')=='STALE' or d.get('analysisStatus')=='STALE'
  if not engine_commit:fail(f'{ticker}: missing engine commit provenance',errors)
  elif expected_commit and not is_stale and engine_commit!=expected_commit:fail(f'{ticker}: fresh engine commit provenance mismatch {engine_commit} != {expected_commit}',errors)
  if expected_commit and is_stale and d.get('lastAttemptCommit')!=expected_commit:fail(f'{ticker}: stale carry-forward missing current attempt provenance',errors)
  q=d.get('quality') or {};score=q.get('dataScore');label=q.get('dataLabel');expected='BAIK' if n(score) and score>=80 else ('CUKUP' if n(score) and score>=60 else 'TERBATAS')
  if n(score) and label!=expected:fail(f'{ticker}: dataScore/dataLabel mismatch {score}/{label}',errors)
  conf=q.get('valuationConfidence')
  if not isinstance(conf,int) or not 0<=conf<=100:fail(f'{ticker}: invalid valuation confidence',errors)
  price=d.get('price');fv=d.get('fairValue') or {};methods=d.get('methods') or [];review=d.get('valuationReview') or {};vals=[fv.get(k) for k in ('bear','base','bull')]
  if fv.get('available'):
   if not price or not all(n(v) and v>0 for v in vals):fail(f'{ticker}: published FV must be finite and positive',errors)
   if not (vals[0]<=vals[1]<=vals[2]):fail(f'{ticker}: FV scenarios not ordered',errors)
   ratio=vals[1]/price;should_review=ratio<.25 or ratio>3.0
   if should_review and (s!='REVIEW' or not review.get('required')):fail(f'{ticker}: extreme FV not routed to REVIEW',errors)
   conflict='CROSS_FAMILY_CONFLICT' in (q.get('reviewFlags') or [])
   if s=='REVIEW' and not (should_review or conflict):fail(f'{ticker}: REVIEW without extreme or cross-family conflict trigger',errors)
   inc=[m for m in methods if m.get('included')];fam={m.get('family') for m in inc if m.get('countsForIndependence',True)}
   if len(inc)<2 or len(fam)<2:fail(f'{ticker}: full FV without >=2 independent families',errors)
   weights={}
   for m in inc:weights[m.get('family')]=weights.get(m.get('family'),0)+(m.get('normalizedWeight') or 0)
   if weights and max(weights.values())>.6001:fail(f'{ticker}: family dominance {max(weights.values()):.1%}',errors)
  elif s=='INDIKATIF':
   if not fv.get('indicative') or q.get('validMethodCount',0)<2:fail(f'{ticker}: invalid indicative evidence',errors)
   if not all(n(v) and v>0 for v in vals):fail(f'{ticker}: indicative range invalid',errors)
   elif not (vals[0]<=vals[1]<=vals[2]):fail(f'{ticker}: indicative scenarios not ordered',errors)
   if conf>55:fail(f'{ticker}: indicative confidence above cap',errors)
  elif s=='REFERENSI':
   if not fv.get('referenceOnly') or q.get('validMethodCount')!=1:fail(f'{ticker}: reference state must have exactly one valid method',errors)
   if not all(n(v) and v>0 for v in vals):fail(f'{ticker}: reference range invalid',errors)
   elif not (vals[0]<=vals[1]<=vals[2]):fail(f'{ticker}: reference scenarios not ordered',errors)
   if conf>35:fail(f'{ticker}: reference confidence above cap',errors)
  elif s=='BELUM_DINILAI':
   if q.get('validMethodCount',0)!=0 or any(v is not None for v in vals):fail(f'{ticker}: unvalued state contains fabricated value',errors)
  for m in methods:
   if not m.get('included'):continue
   mv=[m.get(k) for k in ('bear','base','bull')]
   if not all(n(v) and v>0 for v in mv):fail(f"{ticker}: included method {m.get('name')} has invalid scenarios",errors)
   elif not (mv[0]<=mv[1]<=mv[2]):fail(f"{ticker}: included method {m.get('name')} scenarios not ordered",errors)
  sr=summary_rows.get(ticker)
  if not sr:fail(f'{ticker}: missing summary projection row',errors)
  else:
   sfv=d.get('fairValue') or {};sq=d.get('quality') or {}
   expected_summary={'status':d.get('analysisStatus'),'base':sfv.get('base'),'valuationConfidence':sq.get('valuationConfidence'),'validMethods':sq.get('validMethodCount',0),'independentFamilies':sq.get('independentFamilies',0)}
   for k,v in expected_summary.items():
    if sr.get(k)!=v:fail(f'{ticker}: summary projection mismatch {k}: {sr.get(k)} != {v}',errors)
  qn=d.get('quarterlyNormalization')
  if qn and qn.get('sustainableGrowth') is not None and not (-.2501<=qn['sustainableGrowth']<=.3501):fail(f'{ticker}: sustainable growth escaped guard',errors)
 represented=len(seen)+len(declared_errors)
 if represented!=len(TICKERS):fail(f'atomic universe failed: {represented}/{len(TICKERS)}',errors)
 if sm and (sm.get('requested')!=len(TICKERS) or sm.get('count')!=len(seen) or sm.get('count',0)+len(declared_errors)!=len(TICKERS)):fail('summary universe mismatch',errors)
 for t in REGRESSION:
  p=DATA/f'{t}.json'
  if not p.exists():continue
  d=json.load(open(p,encoding='utf-8'));price=d.get('price');fv=(d.get('fairValue') or {}).get('base')
  if fv is not None and price and (fv<.05*price or fv>5*price):fail(f'{t}: regression outside hard guard',errors)
 print('VALIDATION',{'requested':len(TICKERS),'valuations':len(seen),'explicitErrors':len(declared_errors),'represented':represented,'status':status,'qcVersions':list(versions),'errors':len(errors),'warnings':warn})
 if errors:sys.exit(1)
if __name__=='__main__':main()