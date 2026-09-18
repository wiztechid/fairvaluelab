# v3.20 family consensus + forensic review gate.
# Rebuilds full FV from one consensus vote per independent valuation family.
import json, math, statistics
from pathlib import Path
DATA=Path("data"); QC="3.20-family-consensus-qc"
def n(x):
 try:
  v=float(x); return v if math.isfinite(v) else None
 except:return None
def med(xs):
 xs=[n(x) for x in xs if n(x) is not None and n(x)>0]
 return statistics.median(xs) if xs else None
def process(p):
 d=json.load(open(p,encoding="utf-8"))
 if not isinstance(d,dict) or not d.get("ticker") or not n(d.get("price")):return d
 price=float(d["price"]); q=d.setdefault("quality",{}); methods=d.get("methods") or []
 valid=[m for m in methods if m.get("qcStatus")=="VALID" and all(n(m.get(k)) and n(m.get(k))>0 for k in ("bear","base","bull"))]
 fam={}
 for m in valid:
  if not m.get("countsForIndependence",True):continue
  fam.setdefault(m.get("family") or "other",[]).append(m)
 votes=[]
 for f,ms in fam.items():
  vote={"family":f,"methods":[m.get("name") for m in ms],"bear":med([m["bear"] for m in ms]),"base":med([m["base"] for m in ms]),"bull":med([m["bull"] for m in ms])}
  vote["weight"]=max(.25,min(1.0,med([(n(m.get("confidence")) or 50)/100 for m in ms]) or .5))
  votes.append(vote)
 q["familyConsensus"]=votes;q["familyConsensusCount"]=len(votes)
 if len(votes)>=2:
  bases=[v["base"] for v in votes]; lo=min(bases);hi=max(bases); ratio=hi/lo if lo>0 else 999
  conflict=ratio>3.0
  q["crossFamilySpreadRatio"]=ratio
  flags=[x for x in q.get("reviewFlags",[]) if x not in ("CROSS_FAMILY_CONFLICT","FORENSIC_EXTREME")]
  if conflict:flags.append("CROSS_FAMILY_CONFLICT")
  def wavg(k):
   den=sum(v["weight"] for v in votes);return sum(v[k]*v["weight"] for v in votes)/den
  base=wavg("base"); bear=min(wavg("bear"),base); bull=max(wavg("bull"),base)
  # Preserve disagreement in range rather than deleting minority families.
  if conflict:
   bear=min(bear,lo*.90);bull=max(bull,hi*1.10)
  fv=d.setdefault("fairValue",{});fv.update({"bear":bear,"base":base,"bull":bull,"available":True,"indicative":False,"referenceOnly":False,"familyConsensus":True})
  market_ratio=base/price; extreme=market_ratio<.25 or market_ratio>3.0; large=market_ratio<.5 or market_ratio>2.0
  forensic=[]
  raw=d.get("raw") or {}
  if extreme:
   flags.append("FORENSIC_EXTREME")
   if not n(raw.get("shares")):forensic.append("SHARES_MISSING")
   if raw.get("fxNormalized") is False and str(raw.get("financialCurrency","")).upper() not in ("IDR",""):forensic.append("FX_NOT_NORMALIZED")
   if n(raw.get("bvps")) is not None and n(raw.get("bvps"))<=0:forensic.append("NEGATIVE_BOOK_VALUE")
   if (n(raw.get("epsTTM")) or 0)<=0:forensic.append("NON_POSITIVE_EARNINGS")
  q["reviewFlags"]=list(dict.fromkeys(flags));q["forensicChecks"]=forensic
  conf=int(q.get("valuationConfidence") or 0)
  if conflict:conf-=15
  if large and not extreme:conf-=12
  if extreme:conf-=25
  q["valuationConfidence"]=max(0,min(100,conf))
  review=d.setdefault("valuationReview",{})
  if extreme:
   d["analysisStatus"]="REVIEW";review.update({"required":True,"status":"REVIEW","reason":"FORENSIC_EXTREME","baseToPrice":market_ratio,"forensicChecks":forensic,"policy":"Extreme market divergence requires forensic review; market price never anchors FV."})
  elif conflict:
   d["analysisStatus"]="REVIEW";review.update({"required":True,"status":"REVIEW","reason":"CROSS_FAMILY_CONFLICT","baseToPrice":market_ratio,"familySpreadRatio":ratio,"policy":"Conflicting independent valuation families widen the range and reduce confidence; minority families are not discarded."})
  else:
   d["analysisStatus"]="SIAP";review.update({"required":False,"status":"PASS","reason":None,"baseToPrice":market_ratio})
  q["independentFamilies"]=len(votes);q["validMethodCount"]=len(valid)
 # Remove stale pipeline narratives once final evidence state is known.
 guards=q.get("guards") or []
 if d.get("analysisStatus") in ("SIAP","REVIEW"):
  guards=[g for g in guards if not ("Composite FV belum diterbitkan" in g or "Composite FV tidak diterbitkan" in g or "FV Indikatif diterbitkan" in g)]
 q["guards"]=guards
 d["qcVersion"]=QC;d["engineVersion"]="3.20-family-consensus";d.setdefault("valuationPolicy",{})["consensus"]="One consensus vote per independent family; cross-family disagreement is preserved as uncertainty."
 return d
for p in DATA.glob("*.json"):
 if p.name in ("summary.json","errors.json","idx_disclosures.json","idx_collector_status.json"):continue
 try:
  d=process(p);json.dump(d,open(p,"w",encoding="utf-8"),ensure_ascii=False,indent=2,allow_nan=False)
 except Exception as e:print("FAMILY_CONSENSUS_ERR",p.stem,e)
# rebuild summary from ticker jsons
sp=DATA/"summary.json"
if sp.exists():
 s=json.load(open(sp,encoding="utf-8")); rows=[]
 for p in DATA.glob("*.json"):
  if p.name in ("summary.json","errors.json","idx_disclosures.json","idx_collector_status.json"):continue
  try:
   d=json.load(open(p,encoding="utf-8"))
   if not d.get("ticker"):continue
   f=d.get("fairValue") or {};q=d.get("quality") or {}
   rows.append({"ticker":d["ticker"].replace(".JK",""),"name":d.get("name"),"sector":d.get("companyProfile",{}).get("sector") or d.get("sector"),"price":d.get("price"),"base":f.get("base"),"status":d.get("analysisStatus"),"valuationConfidence":q.get("valuationConfidence"),"validMethods":q.get("validMethodCount"),"independentFamilies":q.get("independentFamilies"),"outliers":q.get("outlierMethodCount",0),"reviewFlags":q.get("reviewFlags",[])})
  except:pass
 s["stocks"]=sorted(rows,key=lambda x:x["ticker"]);s["count"]=len(rows);s["qcVersion"]=QC
 cnt={}
 for x in rows:cnt[x["status"]]=cnt.get(x["status"],0)+1
 s["statusCounts"]=cnt
 json.dump(s,open(sp,"w",encoding="utf-8"),ensure_ascii=False,indent=2,allow_nan=False)
print("FAMILY_CONSENSUS_DONE")
