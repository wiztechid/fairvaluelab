import json, math
from pathlib import Path
from datetime import datetime, timezone, timedelta
import yfinance as yf

DATA=Path('data'); OUT=DATA/'backtest'; OUT.mkdir(parents=True,exist_ok=True)
HORIZONS=[30,60,90,180,365]
def n(x):
    try:v=float(x);return v if math.isfinite(v) else None
    except:return None
def quarter_key(d):
    q=((d.month-1)//3)+1
    return f'{d.year}Q{q}'
def first_hit(hist,start,target,direction):
    if target is None:return None
    for dt,row in hist.loc[hist.index>=start].iterrows():
        hi=n(row.get('High'));lo=n(row.get('Low'))
        if direction=='up' and hi is not None and hi>=target:return dt.date().isoformat()
        if direction=='down' and lo is not None and lo<=target:return dt.date().isoformat()
    return None
def evaluate(ticker,snap):
    start=datetime.fromisoformat(snap['lockedAt'].replace('Z','+00:00')).replace(tzinfo=None)
    try:h=yf.Ticker(ticker+'.JK').history(start=start.date().isoformat(),end=(datetime.now()+timedelta(days=1)).date().isoformat(),auto_adjust=False)
    except Exception:return snap
    if h.empty:return snap
    entry=n(snap.get('price'));fv=snap.get('fairValue') or {};bear=n(fv.get('bear'));base=n(fv.get('base'));bull=n(fv.get('bull'))
    targets={'conservative':bear,'base':base,'expensive':bull};progress={}
    for name,target in targets.items():
        if target is None or entry is None:continue
        direction='up' if target>=entry else 'down';hit=first_hit(h,start,target,direction)
        progress[name]={'target':target,'direction':direction,'hit':bool(hit),'firstHit':hit,'daysToHit':(datetime.fromisoformat(hit)-start).days if hit else None}
    windows={}
    for days in HORIZONS:
        cut=start+timedelta(days=days);x=h.loc[h.index.tz_localize(None)<=cut] if getattr(h.index,'tz',None) else h.loc[h.index<=cut]
        if x.empty:continue
        close=n(x.iloc[-1]['Close']);windows[str(days)]={'close':close,'return':(close/entry-1) if close and entry else None,'maxHigh':n(x['High'].max()),'minLow':n(x['Low'].min())}
    snap['progress']=progress;snap['windows']=windows;snap['lastEvaluatedAt']=datetime.now(timezone.utc).isoformat();return snap
def main():
    index=[]
    for p in DATA.glob('*.json'):
        if p.name in ('summary.json','errors.json'):continue
        try:d=json.load(open(p,encoding='utf-8'))
        except:continue
        ticker=(d.get('ticker') or p.stem).replace('.JK','');asof=d.get('asOf') or datetime.now(timezone.utc).isoformat()
        try:dt=datetime.fromisoformat(asof.replace('Z','+00:00'))
        except:dt=datetime.now(timezone.utc)
        q=quarter_key(dt);tdir=OUT/ticker;tdir.mkdir(parents=True,exist_ok=True);sp=tdir/f'{q}.json'
        # Immutable quarter lock: first valid snapshot wins. Never overwrite valuation inputs later.
        if sp.exists():snap=json.load(open(sp,encoding='utf-8'))
        else:
            fv=d.get('fairValue') or {}
            if not fv.get('available'):continue
            snap={'ticker':ticker,'quarter':q,'lockedAt':asof,'price':d.get('price'),'fairValue':{k:fv.get(k) for k in ('bear','base','bull')},'analysisStatus':d.get('analysisStatus'),'engineVersion':d.get('engineVersion'),'methods':[{'name':m.get('name'),'family':m.get('family'),'base':m.get('base'),'weight':m.get('normalizedWeight')} for m in d.get('methods',[]) if m.get('included')],'quarterlyNormalization':d.get('quarterlyNormalization'),'lockPolicy':'first published valuation snapshot for this quarter; subsequent runs only update price progress'}
        snap=evaluate(ticker,snap);json.dump(snap,open(sp,'w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False)
        index.append({'ticker':ticker,'quarter':q,'lockedAt':snap['lockedAt'],'price':snap['price'],'fairValue':snap['fairValue'],'progress':snap.get('progress',{})})
    json.dump({'updatedAt':datetime.now(timezone.utc).isoformat(),'policy':'immutable quarterly valuation snapshots; market progress may update, valuation inputs may not','snapshots':index},open(OUT/'summary.json','w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False)
    print('BACKTEST_SNAPSHOTS',len(index))
if __name__=='__main__':main()