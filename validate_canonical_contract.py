import json, sys
from pathlib import Path
from des_universe import TICKERS

DATA=Path("data"); CFG=Path("config")
C=json.load(open(CFG/"canonical-engine.json",encoding="utf-8"))
P=json.load(open(CFG/"data-provenance.json",encoding="utf-8"))

def fail(errors,msg): errors.append(msg); print("FAIL",msg)

def main():
    errors=[]; represented=0
    summary=json.load(open(DATA/"summary.json",encoding="utf-8"))
    if summary.get("canonicalArtifact") is not True: fail(errors,"summary is not canonical")
    if summary.get("engineVersion")!=C["engineVersion"]: fail(errors,"summary engine version mismatch")
    if summary.get("qcVersion")!=C["qcVersion"]: fail(errors,"summary QC version mismatch")
    if summary.get("provenanceSchemaVersion")!=P["schemaVersion"]: fail(errors,"summary provenance schema mismatch")
    declared={x.get("ticker") for x in summary.get("errors",[]) if x.get("ticker")}
    for t in TICKERS:
        p=DATA/f"{t}.json"
        if not p.exists():
            if t in declared: represented+=1; continue
            fail(errors,f"{t}: missing canonical artifact and no explicit error"); continue
        d=json.load(open(p,encoding="utf-8")); represented+=1
        if d.get("canonicalArtifact") is not True: fail(errors,f"{t}: canonical flag missing")
        if d.get("engineVersion")!=C["engineVersion"]: fail(errors,f"{t}: engine version mismatch")
        if d.get("qcVersion")!=C["qcVersion"]: fail(errors,f"{t}: QC version mismatch")
        pr=d.get("provenance") or {}
        if pr.get("schemaVersion")!=P["schemaVersion"] or pr.get("canonical") is not True: fail(errors,f"{t}: provenance contract missing")
        mf=pr.get("marketAndFinancials") or {}; un=pr.get("universe") or {}; val=pr.get("valuation") or {}
        if mf.get("classification")!="THIRD_PARTY" or not mf.get("provider"): fail(errors,f"{t}: market provenance invalid")
        if not mf.get("observedAt"): fail(errors,f"{t}: observedAt missing")
        if mf.get("freshnessStatus") not in ("FRESH","STALE"): fail(errors,f"{t}: freshness invalid")
        if un.get("classification")!="OFFICIAL" or not un.get("source"): fail(errors,f"{t}: universe provenance invalid")
        if val.get("classification")!="DERIVED" or val.get("engineVersion")!=C["engineVersion"] or val.get("qcVersion")!=C["qcVersion"]: fail(errors,f"{t}: valuation lineage invalid")
    if represented!=len(TICKERS): fail(errors,f"atomic canonical universe failed {represented}/{len(TICKERS)}")
    print("CANONICAL_VALIDATION",{"represented":represented,"requested":len(TICKERS),"errors":len(errors)})
    if errors: sys.exit(1)

if __name__=="__main__": main()
