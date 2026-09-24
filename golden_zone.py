"""WISS Golden Zone Engine v1
Adaptive bullish swing detector. It does NOT anchor Fib to ATH/ATL or simple 50D min/max.
Searches confirmed pivot-low -> impulsive pivot-high -> active retracement across multiple windows.
"""
import json, math, os
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from des_universe import TICKERS

OUT=Path("data/golden_zone"); OUT.mkdir(parents=True,exist_ok=True)
OHLC=Path("data/ohlc_cache"); OHLC.mkdir(parents=True,exist_ok=True)
WINDOWS=(20,35,50,60)
PIVOTS=(2,3,5)
LEVELS=(0,.382,.5,.618,1,1.5,1.618)

def finite(x):
    try:return math.isfinite(float(x))
    except:return False

def atr(df,n=14):
    pc=df.Close.shift(1)
    tr=pd.concat([(df.High-df.Low).abs(),(df.High-pc).abs(),(df.Low-pc).abs()],axis=1).max(axis=1)
    return float(tr.rolling(n,min_periods=max(5,n//2)).mean().iloc[-1])

def pivots(df,k):
    lows=[]; highs=[]
    lo=df.Low.to_numpy(float); hi=df.High.to_numpy(float)
    for i in range(k,len(df)-k):
        if lo[i] <= np.min(lo[i-k:i+k+1]) and lo[i] < np.min(lo[i-k:i]): lows.append(i)
        if hi[i] >= np.max(hi[i-k:i+k+1]) and hi[i] > np.max(hi[i-k:i]): highs.append(i)
    return lows,highs

def candidate_score(df,li,hi,a,k):
    low=float(df.Low.iloc[li]); high=float(df.High.iloc[hi]); rng=high-low
    if rng<=0 or hi<=li:return None
    impulse_atr=rng/max(a,1e-9)
    bars=hi-li; age=len(df)-1-hi
    if bars<2 or impulse_atr<3:return None
    # confirmation: high must have at least k bars after it; current setup should be a retracement, not an unconfirmed rising leg
    current=float(df.Close.iloc[-1]); retr=(high-current)/rng
    if retr < -.12 or retr > 1.05:return None
    # structure quality: efficient upward displacement, meaningful impulse, recency and usable retracement
    path=df.Close.iloc[li:hi+1].diff().abs().sum()
    efficiency=min(1.0,rng/max(float(path) if finite(path) else rng,1e-9))
    impulse=min(1.0,impulse_atr/8)
    recency=max(0,1-age/max(12,len(df)*.55))
    retr_use=max(0,1-abs(retr-.50)/.70)
    pivot_quality={2:.70,3:.85,5:1.0}[k]
    score=100*(.28*impulse+.24*efficiency+.22*recency+.18*retr_use+.08*pivot_quality)
    return dict(li=li,hi=hi,low=low,high=high,score=score,impulseATR=impulse_atr,
                bars=bars,age=age,retracement=retr,k=k)

def choose_swing(h):
    base=h.tail(max(WINDOWS)+2).copy()
    a=atr(base)
    cands=[]
    for w in WINDOWS:
        d=base.tail(min(w,len(base))).copy()
        offset=len(base)-len(d)
        for k in PIVOTS:
            lows,highs=pivots(d,k)
            for li in lows:
                # use subsequent confirmed highs; not absolute high/low
                for hi in [x for x in highs if x>li]:
                    c=candidate_score(d,li,hi,a,k)
                    if c:
                        c["window"]=w;c["liGlobal"]=offset+li;c["hiGlobal"]=offset+hi
                        cands.append(c)
    if not cands:return None,a
    # Deduplicate same anchors found by different windows/pivot widths, keep strongest score.
    uniq={}
    for c in cands:
        key=(c["liGlobal"],c["hiGlobal"])
        if key not in uniq or c["score"]>uniq[key]["score"]:uniq[key]=c
    ranked=sorted(uniq.values(),key=lambda x:(x["score"],x["hiGlobal"]),reverse=True)
    return ranked[0],a

def round_idx(v):
    if v>=5000:return round(v/25)*25
    if v>=2000:return round(v/10)*10
    if v>=500:return round(v/5)*5
    if v>=200:return round(v/2)*2
    return round(v)

def load_cached_ohlc(sym):
    p=OHLC/f"{sym.replace('.JK','')}.csv"
    if not p.exists(): return None
    try:
        h=pd.read_csv(p,index_col=0,parse_dates=True)
        need={"Open","High","Low","Close"}
        return h if need.issubset(h.columns) and len(h)>=20 else None
    except Exception:return None

def analyze(sym):
    tk=sym if "." in sym else sym+".JK"
    h=load_cached_ohlc(sym)
    if h is None or h.empty or len(h)<20:return {"ticker":sym,"status":"CACHE_MISSING","reason":"Shared OHLC cache unavailable; Golden Zone does not refetch Yahoo"}
    h=h.dropna(subset=["Open","High","Low","Close"])
    c,a=choose_swing(h)
    now=float(h.Close.iloc[-1])
    if not c:return {"ticker":sym,"status":"NO_VALID_SWING","currentPrice":now,"reason":"No confirmed bullish pivot-low → pivot-high impulse passed structure/ATR/retracement gates"}
    lo,hi=c["low"],c["high"]; r=hi-lo
    lv={str(x):lo+x*r for x in LEVELS}
    early=(lv["0.382"],lv["0.5"]); golden=(lv["0.5"],lv["0.618"])
    # Structural invalidation: nearest confirmed local support below early zone, otherwise swing low.
    d=h.tail(max(WINDOWS)+2); lows,_=pivots(d,3)
    supports=[float(d.Low.iloc[i]) for i in lows if float(d.Low.iloc[i])<early[0] and i>c["liGlobal"]]
    invalid=max(supports) if supports else lo
    # ATR buffer prevents exact-pivot stop from being overly fragile.
    invalid=max(lo*.98,invalid-.25*a) if a and finite(a) else invalid
    ref=sum(golden)/2
    risk=ref-invalid
    targets=[lv["1"],lv["1.5"],lv["1.618"]]
    rr=[(t-ref)/risk if risk>0 else None for t in targets]
    if now<lv["0.382"]:pos="BELOW_EARLY_ZONE"
    elif now<=lv["0.5"]:pos="EARLY_ZONE"
    elif now<=lv["0.618"]:pos="GOLDEN_ZONE"
    elif now<=lv["1"]:pos="ABOVE_GOLDEN_ZONE"
    else:pos="BREAKOUT_ABOVE_SWING"
    # A broken original swing low invalidates the setup.
    if now<lo:pos="INVALIDATED"
    quality="HIGH" if c["score"]>=72 else "MEDIUM" if c["score"]>=58 else "LOW"
    return {
      "ticker":sym.replace(".JK",""),"status":"VALID" if quality!="LOW" else "LOW_CONFIDENCE",
      "engine":"WISS Golden Zone v1","currentPrice":now,"position":pos,
      "swing":{"low":round_idx(lo),"high":round_idx(hi),"lowDate":str(h.index[c["liGlobal"]].date()),"highDate":str(h.index[c["hiGlobal"]].date()),
               "searchWindow":c["window"],"pivotWidth":c["k"],"barsInImpulse":c["bars"],"highAgeBars":c["age"],
               "impulseATR":round(c["impulseATR"],2),"score":round(c["score"],1),"quality":quality},
      "fib":{k:round_idx(v) for k,v in lv.items()},
      "earlyZone":[round_idx(early[0]),round_idx(early[1])],
      "goldenZone":[round_idx(golden[0]),round_idx(golden[1])],
      "referenceEntry":round_idx(ref),"invalidation":round_idx(invalid),
      "targets":[{"level":"1.000","price":round_idx(targets[0]),"rr":round(rr[0],2) if rr[0] is not None else None},
                 {"level":"1.500","price":round_idx(targets[1]),"rr":round(rr[1],2) if rr[1] is not None else None},
                 {"level":"1.618","price":round_idx(targets[2]),"rr":round(rr[2],2) if rr[2] is not None else None}],
      "methodNote":"Adaptive multi-window confirmed pivot structure; not ATH/ATL or simple period min/max. R:R uses Golden Zone midpoint and structural invalidation."
    }

def main():
    ok=0
    summary={"updatedAt":datetime.now(timezone.utc).isoformat(),"engine":"WISS Golden Zone v1","tickers":{}}
    for i,sym in enumerate(TICKERS,1):
        s=sym.replace(".JK","")
        try:d=analyze(s)
        except Exception as e:d={"ticker":s,"status":"ERROR","reason":str(e)[:180]}
        if d.get("status")=="VALID":ok+=1
        summary["tickers"][s]={"status":d.get("status"),"position":d.get("position"),"quality":(d.get("swing") or {}).get("quality")}
        (OUT/f"{s}.json").write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8")
        if i%50==0:print("GOLDEN_ZONE",i,"/",len(TICKERS))
    summary["validCount"]=ok
    (OUT/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    print("GOLDEN_ZONE_DONE",ok,"/",len(TICKERS))
if __name__=="__main__":main()
