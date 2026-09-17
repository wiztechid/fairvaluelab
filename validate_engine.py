import json, math, sys
from pathlib import Path
from des_universe import TICKERS
DATA=Path('data');REGRESSION=['AADI','DSSA','BUMI','TPIA','BRMS'];EXPECTED_QC='3.12-atomic-qc'
def n(x):return isinstance(x,(int,float)) and math.isfinite(x)
def fail(msg,errors):errors.append(msg);print('FAIL',msg)
def main():
 errors=[];warn=[];status={'SIAP':0,'TERBATAS':0,'STALE':0,'ERROR':0};seen=set();versions=set()
 try:sm=json.load(open(DATA/'summary.json',encoding='utf-8'))
 except Exception as e:sm={};fail(f'summary.json missing/invalid: {e}',errors)
 declared_errors={e.get('ticker'):e for e in sm.get('errors',[]) if e.get('ticker')}
 for ticker in TICKERS:
  p=DATA/f'{ticker}.json'
  if not p.exists():
   # A fetch failure is a valid explicit production state when the same current run
   # records it in summary.errors. Do not fabricate/stale-copy a valuation merely
   # to reach 618 JSON files.
   if ticker in declared_errors:
    status['ERROR']+=1;warn.append(f"{ticker}: explicit {declared_errors[ticker].get('status','GAGAL_FETCH')}");continue
   fail(f'{ticker}: missing JSON and no explicit current-run error record',errors);continue
  try:d=json.load(open(p,encoding='utf-8'))
  except Exception as e:fail(f'{ticker}: invalid JSON {e}',errors);continue
  seen.add(ticker);versions.add(d.get('qcVersion'));s=d.get('analysisStatus','TERBATAS');status[s if s in status else 'TERBATAS']+=1
  if d.get('qcVersion')!=EXPECTED_QC:fail(f"{ticker}: stale QC version {d.get('qcVersion')}",errors)
  if not d.get('engineGeneration'):fail(f'{ticker}: missing upstream engine generation',errors)
  score=(d.get('quality') or {}).get('dataScore');label=(d.get('quality') or {}).get('dataLabel');expected='BAIK' if n(score) and score>=80 else ('CUKUP' if n(score) and score>=60 else 'TERBATAS')
  if n(score) and label!=expected:fail(f'{ticker}: dataScore/dataLabel mismatch {score}/{label}',errors)
  price=d.get('price');fv=d.get('fairValue') or {};methods=d.get('methods') or []
  if fv.get('available'):
   vals=[fv.get(k) for k in ('bear','base','bull')]
   if not price or not all(n(v) and v>0 and .05*price<=v<=5*price for v in vals):fail(f'{ticker}: published FV outside economic guard',errors)
   if not (vals[0]<=vals[1]<=vals[2]):fail(f'{ticker}: FV scenarios not ordered bear<=base<=bull',errors)
   inc=[m for m in methods if m.get('included')];fam={m.get('family') for m in inc if m.get('countsForIndependence',True)}
   if len(inc)<2 or len(fam)<2:fail(f'{ticker}: SIAP without >=2 independent families',errors)
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
  if sm.get('requested')!=len(TICKERS):fail('summary requested universe mismatch',errors)
  if sm.get('count')!=len(seen):fail(f"summary processed mismatch {sm.get('count')} vs {len(seen)}",errors)
  if len(sm.get('errors',[]))!=len(declared_errors):fail('summary contains duplicate/invalid error ticker records',errors)
  if sm.get('count',0)+len(declared_errors)!=len(TICKERS):fail('summary universe count mismatch',errors)
  if sm.get('qcVersion')!=EXPECTED_QC:fail('summary QC version mismatch',errors)
 for t in REGRESSION:
  p=DATA/f'{t}.json'
  if not p.exists():continue
  d=json.load(open(p,encoding='utf-8'));price=d.get('price');fv=(d.get('fairValue') or {}).get('base')
  if fv is not None and price and (fv<.05*price or fv>5*price):fail(f'{t}: regression extreme FV',errors)
  if t=='BRMS' and not [m for m in d.get('methods',[]) if str(m.get('name','')).startswith('Historical P/E')]:warn.append('BRMS: adaptive P/E absent; inspect EPS/history source')
 print('VALIDATION',{'requested':len(TICKERS),'valuations':len(seen),'explicitErrors':len(declared_errors),'represented':represented,'status':status,'qcVersions':list(versions),'errors':len(errors),'warnings':warn})
 if errors:sys.exit(1)
if __name__=='__main__':main()