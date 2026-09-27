import json, math, sys
from pathlib import Path

DATA=Path("data")
CONFIG=Path("config")
CANONICAL=json.load(open(CONFIG/"canonical-engine.json",encoding="utf-8"))
PROVENANCE=json.load(open(CONFIG/"data-provenance.json",encoding="utf-8"))
SKIP={"summary.json","errors.json","idx_disclosures.json","idx_collector_status.json","news_raw.json","ticker_aliases.json"}

def ticker_files():
    for p in DATA.glob("*.json"):
        if p.name in SKIP: continue
        try:
            d=json.load(open(p,encoding="utf-8"))
        except Exception:
            continue
        if isinstance(d,dict) and d.get("ticker"):
            yield p,d

def provenance_for(d):
    return {
      "schemaVersion":"1.0",
      "canonical":True,
      "artifactRole":"PUBLIC_VALUATION",
      "marketAndFinancials":{
        "classification":"THIRD_PARTY",
        "provider":d.get("source") or "Yahoo Finance via yfinance",
        "observedAt":d.get("asOf"),
        "freshnessStatus":d.get("freshnessStatus") or "UNKNOWN"
      },
      "universe":{
        "classification":"OFFICIAL",
        "provider":"OJK",
        "source":d.get("universeSource")
      },
      "valuation":{
        "classification":"DERIVED",
        "engineVersion":d.get("engineVersion"),
        "engineGeneration":d.get("engineGeneration"),
        "qcVersion":d.get("qcVersion")
      },
      "assumptions":{
        "classification":"ESTIMATED",
        "fields":["growthNormalized","costOfEquity","terminalGrowth"]
      }
    }

def apply():
    count=0
    for p,d in ticker_files():
        d["canonicalArtifact"]=True
        d["provenance"]=provenance_for(d)
        json.dump(d,open(p,"w",encoding="utf-8"),ensure_ascii=False,indent=2,allow_nan=False)
        count+=1
    sp=DATA/"summary.json"
    if sp.exists():
        s=json.load(open(sp,encoding="utf-8"))
        s["canonicalArtifact"]=True
        s["canonicalContractVersion"]=CANONICAL["schemaVersion"]
        s["engineVersion"]=CANONICAL["engineVersion"]
        s["qcVersion"]=CANONICAL["qcVersion"]
        s["provenanceSchemaVersion"]=PROVENANCE["schemaVersion"]
        json.dump(s,open(sp,"w",encoding="utf-8"),ensure_ascii=False,indent=2,allow_nan=False)
    print("CANONICAL_CONTRACT_APPLIED",count)

if __name__=="__main__": apply()
