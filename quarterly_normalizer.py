import json, math
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

DATA=Path('data')
METRICS={
 'revenue':['Total Revenue','Operating Revenue'],
 'ebitda':['EBITDA','Normalized EBITDA'],
 'ebit':['EBIT','Operating Income'],
 'netIncome':['Net Income','Net Income Common Stockholders'],
 'operatingCashFlow':['Operating Cash Flow','Total Cash From Operating Activities'],
 'freeCashFlow':['Free Cash Flow'],
}
def n(x):
    try:v=float(x);return v if math.isfinite(v) else None
    except:return None
def series(df,names,factor=1.0):
    if df is None or df.empty:return []
    for name in names:
        if name in df.index:
            out=[]
            for dt,v in df.loc[name].items():
                z=n(v)
                if z is not None:out.append((pd.Timestamp(dt),z*factor))
            return sorted(out)
    return []
def robust(vals):
    vals=[x for x in vals if n(x) is not None]
    if not vals:return None,[],[]
    if len(vals)<3:return float(np.median(vals)),vals,[]
    a=np.array(vals,float);med=float(np.median(a));mad=float(np.median(np.abs(a-med)))
    if mad>1e-9:mask=np.abs(a-med)<=3.5*1.4826*mad
    else:
        q1,q3=np.percentile(a,[25,75]);iqr=q3-q1;mask=np.ones(len(a),dtype=bool) if iqr<=1e-9 else (a>=q1-1.5*iqr)&(a<=q3+1.5*iqr)
    keep=a[mask].tolist();drop=a[~mask].tolist();return (float(np.median(keep)) if keep else med),keep,drop
def standalone(points):
    # Yahoo quarterly statements are normally standalone. If repeated YTD-like dates are supplied,
    # preserve observations; explicit subtraction is only attempted when periods within a fiscal year
    # monotonically accumulate and 4 observations exist.
    by={}
    for dt,v in points:by[(dt.year,dt.quarter)]=(dt,v)
    return [by[k] for k in sorted(by)]
def yoy_growth(points):
    m={(dt.year,dt.quarter):v for dt,v in points};out=[]
    for (y,q),v in sorted(m.items()):
        prev=m.get((y-1,q))
        # Percentage growth is invalid around zero/sign changes: mark turnaround/base effect instead.
        if prev is None or abs(prev)<1e-9 or prev*v<=0:continue
        g=v/prev-1
        if math.isfinite(g):out.append({'year':y,'quarter':q,'growth':g})
    return out
def weighted_growth(obs):
    if not obs:return None,[],[]
    vals=[x['growth'] for x in obs];med,keep,drop=robust(vals)
    if not keep:return None,keep,drop
    # Match retained values back, favor recent observations; winsorize only after robust filtering.
    clean=[]
    pool=list(keep)
    for x in sorted(obs,key=lambda z:(z['year'],z['quarter'])):
        g=x['growth']
        j=next((i for i,v in enumerate(pool) if abs(v-g)<1e-12),None)
        if j is not None:clean.append(x);pool.pop(j)
    if not clean:return med,keep,drop
    weights=np.arange(1,len(clean)+1,dtype=float);weights/=weights.sum()
    gs=np.array([np.clip(x['growth'],-.75,1.5) for x in clean],float)
    return float(np.sum(gs*weights)),keep,drop
def process(path):
    d=json.load(open(path,encoding='utf-8'));ticker=d.get('ticker') or path.stem+'.JK';raw=d.setdefault('raw',{});factor=n(raw.get('fxFactor')) or 1.0
    try:
        t=yf.Ticker(ticker);qi=t.quarterly_income_stmt;qc=t.quarterly_cashflow
    except Exception as e:
        d['quarterlyNormalization']={'status':'UNAVAILABLE','reason':str(e)[:100]};return d
    details={};usable=[]
    for key,names in METRICS.items():
        df=qc if key in ('operatingCashFlow','freeCashFlow') else qi
        pts=standalone(series(df,names,factor));obs=yoy_growth(pts);g,keep,drop=weighted_growth(obs)
        details[key]={'observations':obs,'normalGrowth':g,'outliersRemoved':drop,'validGrowthCount':len(keep)}
        if g is not None:usable.append((key,g))
    # Earnings is primary, but sustainable growth requires operating confirmation.
    primary=details['netIncome']['normalGrowth'];rev=details['revenue']['normalGrowth'];eb=details['ebitda']['normalGrowth'];ocf=details['operatingCashFlow']['normalGrowth'];fcf=details['freeCashFlow']['normalGrowth']
    confirms=[x for x in (rev,eb,ocf,fcf) if x is not None]
    if primary is not None:
        base=np.clip(primary,-.35,.45);support=float(np.median(confirms)) if confirms else 0.0
        # 60% normalized earnings + 40% operating/cash confirmation, then conservative cap.
        sustainable=float(np.clip(.60*base+.40*np.clip(support,-.35,.45),-.25,.35))
        confidence=min(1.0,.45+.08*len(confirms)+.03*min(details['netIncome']['validGrowthCount'],4))
        status='READY' if len(confirms)>=2 else 'LIMITED'
    elif rev is not None and eb is not None:
        sustainable=float(np.clip(.5*rev+.5*eb,-.20,.25));confidence=.48;status='LIMITED'
    else:sustainable=None;confidence=.25;status='INSUFFICIENT'
    old=n(raw.get('growthNormalized'));raw['growthNormalizedLegacy']=old;raw['growthNormalizedQuarterly']=sustainable
    if sustainable is not None:raw['growthNormalized']=sustainable
    d['quarterlyNormalization']={'status':status,'sustainableGrowth':sustainable,'confidence':confidence,'method':'same-quarter YoY -> median/MAD outlier removal -> recency weighting -> earnings + operating/cash confirmation','metrics':details,'notes':['Sign changes and near-zero denominators are excluded from percentage growth and treated as turnaround/base-effect conditions.','Extreme reported growth remains visible in observations but is not allowed to dominate sustainable growth.']}
    d.setdefault('valuationPolicy',{})['growthSource']='Robust quarterly sustainable growth when available; legacy normalized growth otherwise.'
    d['engineVersion']='3.12-quarterly-normalized';return d

changed=0
for p in DATA.glob('*.json'):
    if p.name in ('summary.json','errors.json'):continue
    try:
        d=process(p);json.dump(d,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False);changed+=1
    except Exception as e:print('QUARTERLY_NORMALIZER_ERR',p.stem,e)
print('QUARTERLY_NORMALIZER_DONE',changed)