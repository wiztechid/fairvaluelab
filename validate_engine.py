import json, math, sys
from pathlib import Path
from des_universe import TICKERS
DATA=Path('data');REGRESSION=['AADI','DSSA','BUMI','TPIA','BRMS'];EXPECTED_QC='3.14-extreme-review-qc'
def n(x):return isinstance(x,(int,float)) and math.isfinite(x)
def fail(msg,errors):errors.append(msg);print('FAIL',msg)
def main():
 errors=[];warn=[];status={'SIAP':0,'REVIEW':0,'TERBATAS':0,'STALE':0,'ERROR':0};seen=set();versions=set()
 try:sm=json.load(open(DATA/'summary.json',encoding='utf-8'))
 except Exception as e:sm={};fail(f'summary.json missing/invalid: {e}',errors)
 declared_errors={e.get('ticker'):e for e in sm.get('errors',[]) if e.get('ticker')}
 for ticker in TICKERS:
  p=DATA/f'{ticker}.json'
  if not p.exists():
   if ticker in declared_errors:status['ERROR']+=1;warn.append(f"{ticker}: explicit {declared_errors[ticker].get('status','GAGAL_FETCH')}");continue
   fail(f'{ticker}: missing JSON and no explicit current-run error record',errors);continue
  try:d=json.load(open(p,encoding='utf-8'))
  except Exception as e:fail(f'{ticker}: invalid JSON {e}',errors);continue
  seen.add(ticker);versions.add(d.get('qcVersion'));s=d.get('analysisStatus','TERBATAS');status[s if s in status else 'TERBATAS']+=1
  if d.get('qcVersion')!=EXPECTED_QC:fail(f"{ticker}: stale QC version {d.get('qcVersion')}",errors)
  if not d.get('engineGeneration'):fail(f'{ticker}: missing upstream engine generation',errors)
  score=(d.get('quality') or {}).get('dataScore');label=(d.get('quality') or {}).get('dataLabel');expected='BAIK' if n(score) and score>=80 else ('CUKUP' if n(score) and score>=60 else 'TERBATAS')
  if n(score) and label!=expected:fail(f'{ticker}: dataScore/dataLabel mismatch {score}/{label}',errors)
  conf=(d.get('quality') or {}).get('valuationConfidence')
  if not isinstance(conf,int) or not 0<=conf<=100:fail(f'{ticker}: invalid valuation confidence',errors)
  price=d.get('price');fv=d.get('fairValue') or {};methods=d.get('methods') or [];review=d.get('valuationReview') or {}
  if fv.get('available'):
   vals=[fv.get(k) for k in ('bear','base','bull')]
   if not price or not all(n(v) and v>0 and .05*price<=v<=5*price for v in vals):fail(f'{ticker}: published FV outside economic guard',errors)
   if not (vals[0]<=vals[1]<=vals[2]):fail(f'{ticker}: FV scenarios not ordered bear<=base<=bull',errors)
   ratio=vals[1]/price;should_review=ratio<.25 or ratio>3.0
   if should_review and (s!='REVIEW' or not review.get('required')):fail(f'{ticker}: extreme FV not routed to REVIEW',errors)
   if not should_review and s=='REVIEW':fail(f'{ticker}: REVIEW without extreme FV trigger',errors)
   inc=[m for m in methods if m.get('included')];fam={m.get('family') for m in inc if m.get('countsForIndependence',True)}
   if len(inc)<2 or len(fam)<2:fail(f'{ticker}: published FV without >=2 independent families',errors)
   weights={}
   for m in inc:weights[m.get('family')]=weights.get(m.get('family'),0)+(m.get('normalizedWeight') or 0)
   if weights and max(weights.values())>.6001:fail(f'{ticker}: family dominance {max(weights.values()):.1%}',errors)
  for m in methods:
   if m.get('included') and not all(n(m.get(k)) and m.get(k)>0 for k in ('bear','base','bull')):fail(f'{ticker}: included method has invalid value',errors)
  qn=d.get('quarterlyNormalization')
  if qn and qn.get('sustainableGrowth') is not None and not (-.2501<=qn['sustainableGrowth']<=.3501):fail(f'{ticker}: sustainable growth escaped guard',errors)
 represented=len(seen)+len(declared_errors)
 if represented!=len(TICKERS):fail(f'atomic universe failed: {represented}/{len(TICKERS)} DES represented by valuation or explicit error',errors)
 if sm:
  if sm.get('requested')!=len(TICKERS) or sm.get('count')!=len(seen) or sm.get('count',0)+len(declared_errors)!=len(TICKERS):fail('summary universe mismatch',errors)
  # summary is rebuilt by postprocess in this same working tree. Its QC version must
  # describe the current files; do not compare against metadata from the repository checkout.
  summary_qc=sm.get('qcVersion')
  if summary_qc!=EXPECTED_QC:warn.append(f'summary qcVersion metadata={summary_qc}; ticker files={EXPECTED_QC}. This is warning-only because ticker-level validation is authoritative.')
 for t in REGRESSION:
  p=DATA/f'{t}.json'
  if not p.exists():continue
  d=json.load(open(p,encoding='utf-8'));price=d.get('price');fv=(d.get('fairValue') or {}).get('base')
  if fv is not None and price and (fv<.05*price or fv>5*price):fail(f'{t}: regression extreme outside hard guard',errors)
 print('VALIDATION',{'requested':len(TICKERS),'valuations':len(seen),'explicitErrors':len(declared_errors),'represented':represented,'status':status,'qcVersions':list(versions),'errors':len(errors),'warnings':warn})
 if errors:sys.exit(1)
if __name__=='__main__':main()