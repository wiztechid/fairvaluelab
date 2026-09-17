import json, math
from pathlib import Path
from datetime import datetime, timezone, timedelta
import pandas as pd
import yfinance as yf

DATA=Path('data'); OUT=DATA/'backtest'; OUT.mkdir(parents=True,exist_ok=True)
HORIZONS=[30,60,90,180,365]
def n(x):
    try:v=float(x);return v if math.isfinite(v) else None
    except:return None
def parse_dt(x):
    try:return datetime.fromisoformat(str(x).replace('Z','+00:00'))
    except:return None
def financial_quarter(d):
    qn=d.get('quarterlyNormalization') or {};metrics=qn.get('metrics') or {};latest=None
    for obj in metrics.values():
        for x in (obj or {}).get('observations') or []:
            try:key=(int(x['year']),int(x['quarter']))
            except:continue
            if latest is None or key>latest:latest=key
    return f'{latest[0]}Q{latest[1]}' if latest else None
def report_anchor(d):
    # Prefer explicit PIT/publication metadata when a future provider supplies it.
    for key in ('reportPublishedAt','filingDate','acceptedAt'):
        dt=parse_dt(d.get(key) or (d.get('raw') or {}).get(key))
        if dt:return dt,key
    # Current Yahoo pipeline has no authoritative IDX filing timestamp: asOf is conservative live-lock only.
    dt=parse_dt(d.get('asOf')) or datetime.now(timezone.utc)
    return dt,'engineAsOfFallback'
def first_hit(hist,start,target,direction):
    if target is None:return None
    idx=hist.index.tz_localize(None) if getattr(hist.index,'tz',None) else hist.index
    for pos,dt in enumerate(idx):
        if dt.to_pydatetime()<start:continue
        row=hist.iloc[pos];hi=n(row.get('High'));lo=n(row.get('Low'))
        if direction=='up' and hi is not None and hi>=target:return dt.date().isoformat()
        if direction=='down' and lo is not None and lo<=target:return dt.date().isoformat()
    return None
def zone(price,fv):
    bear=n(fv.get('bear'));base=n(fv.get('base'));bull=n(fv.get('bull'));p=n(price)
    if p is None or None in (bear,base,bull):return 'UNKNOWN'
    if p<bear:return 'BELOW_CONSERVATIVE'
    if p<base:return 'CONSERVATIVE_TO_BASE'
    if p<=bull:return 'BASE_TO_EXPENSIVE'
    return 'ABOVE_EXPENSIVE'
def evaluate(ticker,snap):
    start=parse_dt(snap['lockedAt']);start=start.replace(tzinfo=None) if start else datetime.now()
    try:h=yf.Ticker(ticker+'.JK').history(start=start.date().isoformat(),end=(datetime.now()+timedelta(days=1)).date().isoformat(),auto_adjust=False)
    except Exception:return snap
    if h.empty:return snap
    entry=n(snap.get('price'));fv=snap.get('fairValue') or {};targets={'conservative':n(fv.get('bear')),'base':n(fv.get('base')),'expensive':n(fv.get('bull'))};progress={}
    for name,target in targets.items():
        if target is None or entry is None:continue
        direction='up' if target>=entry else 'down';hit=first_hit(h,start,target,direction)
        progress[name]={'target':target,'direction':direction,'hit':bool(hit),'firstHit':hit,'daysToHit':(datetime.fromisoformat(hit)-start).days if hit else None}
    windows={};idx=h.index.tz_localize(None) if getattr(h.index,'tz',None) else h.index
    for days in HORIZONS:
        cut=start+timedelta(days=days);x=h.loc[idx<=cut]
        if x.empty:continue
        close=n(x.iloc[-1]['Close']);windows[str(days)]={'close':close,'zone':zone(close,fv),'return':(close/entry-1) if close and entry else None,'maxHigh':n(x['High'].max()),'minLow':n(x['Low'].min())}
    last=n(h.iloc[-1]['Close']);snap['progress']=progress;snap['windows']=windows;snap['currentPrice']=last;snap['currentZone']=zone(last,fv);snap['lastEvaluatedAt']=datetime.now(timezone.utc).isoformat();return snap
def main():
    index=[]
    for p in DATA.glob('*.json'):
        if p.name in ('summary.json','errors.json'):continue
        try:d=json.load(open(p,encoding='utf-8'))
        except:continue
        # data/ now also contains collector feeds/status files. Snapshot only
        # valuation ticker objects; disclosure feeds are JSON arrays and must
        # never be interpreted as ticker valuation documents.
        if not isinstance(d,dict):continue
        fv=d.get('fairValue') or {}
        if not isinstance(fv,dict) or not fv.get('available'):continue
        ticker=(d.get('ticker') or p.stem).replace('.JK','');fq=financial_quarter(d)
        if not fq:continue
        anchor,source=report_anchor(d);asof=anchor.isoformat();tdir=OUT/ticker;tdir.mkdir(parents=True,exist_ok=True);sp=tdir/f'{fq}.json'
        # One immutable valuation per financial-report quarter. Later engine runs cannot rewrite the thesis.
        if sp.exists():snap=json.load(open(sp,encoding='utf-8'))
        else:
            snap={'ticker':ticker,'financialQuarter':fq,'lockedAt':asof,'lockTimeSource':source,'pointInTimeQuality':'VERIFIED' if source!='engineAsOfFallback' else 'PROVISIONAL','price':d.get('price'),'entryZone':zone(d.get('price'),fv),'fairValue':{k:fv.get(k) for k in ('bear','base','bull')},'analysisStatus':d.get('analysisStatus'),'engineVersion':d.get('engineVersion'),'methods':[{'name':m.get('name'),'family':m.get('family'),'base':m.get('base'),'weight':m.get('normalizedWeight')} for m in d.get('methods',[]) if m.get('included')],'quarterlyNormalization':d.get('quarterlyNormalization'),'lockPolicy':'first valuation after each distinct financial quarter; immutable thereafter. Filing/publication timestamp preferred; engine asOf fallback is marked PROVISIONAL.'}
        snap=evaluate(ticker,snap);json.dump(snap,open(sp,'w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False)
        index.append({'ticker':ticker,'financialQuarter':fq,'lockedAt':snap['lockedAt'],'pointInTimeQuality':snap.get('pointInTimeQuality'),'price':snap['price'],'entryZone':snap.get('entryZone'),'fairValue':snap['fairValue'],'currentZone':snap.get('currentZone'),'progress':snap.get('progress',{})})
    stats={'snapshots':len(index),'verifiedPIT':sum(x.get('pointInTimeQuality')=='VERIFIED' for x in index),'provisionalPIT':sum(x.get('pointInTimeQuality')=='PROVISIONAL' for x in index)}
    for target in ('conservative','base','expensive'):
        eligible=[x for x in index if target in x.get('progress',{})];hits=[x for x in eligible if x['progress'][target].get('hit')];days=[x['progress'][target]['daysToHit'] for x in hits if x['progress'][target].get('daysToHit') is not None]
        stats[target]={'eligible':len(eligible),'hits':len(hits),'hitRate':len(hits)/len(eligible) if eligible else None,'medianDaysToHit':float(pd.Series(days).median()) if days else None}
    json.dump({'updatedAt':datetime.now(timezone.utc).isoformat(),'policy':'one immutable valuation snapshot per distinct financial-report quarter; target progress is evaluated forward only','stats':stats,'snapshots':index},open(OUT/'summary.json','w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False)
    print('BACKTEST',stats)
if __name__=='__main__':main()