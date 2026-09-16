import json, math
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

DATA=Path('data')

def n(x):
    try:
        v=float(x); return v if math.isfinite(v) else None
    except:return None

def annual(df,names):
    if df is None or df.empty:return []
    for name in names:
        if name in df.index:
            out=[]
            for dt,v in df.loc[name].items():
                if pd.notna(v) and n(v) is not None:out.append((pd.Timestamp(dt),float(v)))
            return sorted(out)
    return []

def adaptive_band(vals):
    # No universal 60x ceiling. Clean each stock relative to its own history.
    a=np.array([v for v in vals if n(v) is not None and 0.5<=v<=500],float)
    if len(a)<20:return None
    lo,hi=np.percentile(a,[5,95]);a=a[(a>=lo)&(a<=hi)]
    if len(a)<12:return None
    logs=np.log(a);medlog=float(np.median(logs));mad=float(np.median(np.abs(logs-medlog)))
    if mad>1e-9:a=a[np.abs(logs-medlog)<=3.5*1.4826*mad]
    if len(a)<10:return None
    med=float(np.median(a));madlin=float(np.median(np.abs(a-med)));sig=max(1.4826*madlin,med*.08)
    return max(.5,med-sig),med,min(500,med+sig),sig,len(a)

def process(path):
    d=json.load(open(path,encoding='utf-8'));price=n(d.get('price'));raw=d.get('raw') or {};eps=n(raw.get('epsTTM'));shares=n(raw.get('shares'))
    if not price or not eps or eps<=0 or not shares:return d
    ticker=d.get('ticker') or path.stem+'.JK';t=yf.Ticker(ticker)
    try:h=t.history(period='5y',auto_adjust=False);inc=t.income_stmt
    except:return d
    if h.empty:return d
    factor=n(raw.get('fxFactor')) or 1.0
    nis=annual(inc,['Net Income','Net Income Common Stockholders'])
    if not nis:return d
    # Replace old P/E methods so the adaptive version is authoritative.
    methods=[m for m in (d.get('methods') or []) if not str(m.get('name','')).startswith('Historical P/E')]
    guards=d.setdefault('quality',{}).setdefault('guards',[])
    cur=price/eps
    for yrs in (3,5):
        hh=h[h.index>=h.index.max()-pd.DateOffset(years=yrs)];vals=[]
        for dt,ni in nis:
            if dt.year not in set(hh.index.year):continue
            hist_eps=(ni*factor)/shares
            if hist_eps<=0:continue
            px=hh[hh.index.year==dt.year].Close.dropna()
            vals += [float(x)/hist_eps for x in px if .5<=float(x)/hist_eps<=500]
        b=adaptive_band(vals)
        if not b:continue
        low,med,high,sig,count=b;bear=low*eps;base=med*eps;bull=high*eps
        # Economic guard remains on fair-value output, not on the P/E multiple itself.
        if not all(.05*price<=v<=5*price for v in (bear,base,bull)):continue
        high_mult=med>60 or cur>60
        confidence=.72 if high_mult else .90
        warning='HIGH MULTIPLE · P/E di atas 60x diterima karena konsisten dengan distribusi historis emiten; confidence diturunkan.' if high_mult else None
        methods.append({'name':f'Historical P/E {yrs}Y','family':'earnings','bear':bear,'base':base,'bull':bull,'confidence':confidence,'relevance':1.0,'rawWeight':confidence,'bands':{'mean':med,'sd':sig,'current':cur,'sampleCount':count,'adaptive':True,'hardCap':None},'warning':warning,'explanation':f'EPS tervalidasi × median P/E historis {yrs} tahun. Outlier dinilai relatif terhadap histori emiten, bukan hard cap 60x.','included':False,'normalizedWeight':0,'qcStatus':'CANDIDATE'})
        if high_mult:guards.append(f'Historical P/E {yrs}Y memakai adaptive high-multiple QC: median {med:.1f}x, current {cur:.1f}x; confidence diturunkan, bukan otomatis ditolak.')
    d['methods']=methods;d['engineVersion']='3.9-adaptive-pe';return d

changed=0
for p in DATA.glob('*.json'):
    if p.name in ('summary.json','errors.json'):continue
    try:
        d=process(p);json.dump(d,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False);changed+=1
    except Exception as e:print('ADAPTIVE_PE_ERR',p.stem,e)
print('ADAPTIVE_PE_DONE',changed)