import json, math
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

DATA=Path('data')
def n(x):
    try:v=float(x);return v if math.isfinite(v) else None
    except:return None
def annual(df,names):
    if df is None or df.empty:return []
    for name in names:
        if name in df.index:return sorted([(pd.Timestamp(dt),float(v)) for dt,v in df.loc[name].items() if pd.notna(v) and n(v) is not None])
    return []
def adaptive_band(vals):
    a=np.array([v for v in vals if n(v) is not None and .5<=v<=500],float)
    if len(a)<20:return None
    lo,hi=np.percentile(a,[5,95]);a=a[(a>=lo)&(a<=hi)]
    if len(a)<12:return None
    logs=np.log(a);medlog=float(np.median(logs));mad=float(np.median(np.abs(logs-medlog)))
    if mad>1e-9:a=a[np.abs(logs-medlog)<=3.5*1.4826*mad]
    if len(a)<10:return None
    med=float(np.median(a));madlin=float(np.median(np.abs(a-med)));sig=max(1.4826*madlin,med*.08)
    return max(.5,med-sig),med,min(500,med+sig),sig,len(a)
def recover_eps(info,price,raw,inc):
    candidates=[]
    direct=n(info.get('trailingEps'))
    if direct and direct>0:candidates.append(('Yahoo trailingEps',direct))
    trailing_pe=n(info.get('trailingPE'))
    if price and trailing_pe and .5<=trailing_pe<=500:
        implied=price/trailing_pe
        if implied>0:candidates.append(('Price / Yahoo trailingPE',implied))
    stored=n(raw.get('epsTTM'))
    if stored and stored>0:candidates.append(('WISS reconciled EPS',stored))
    shares=n(raw.get('shares'));factor=n(raw.get('fxFactor')) or 1.0
    ni=annual(inc,['Net Income','Net Income Common Stockholders'])
    if shares and ni:
        calc=(ni[-1][1]*factor)/shares
        if calc>0:candidates.append(('Latest annual NI / shares',calc))
    if not candidates:return None,None,[]
    # Prefer TTM market-data EPS when direct and implied agree; otherwise robust median.
    direct_vals=[v for s,v in candidates if s in ('Yahoo trailingEps','Price / Yahoo trailingPE')]
    if len(direct_vals)>=2 and max(direct_vals)/min(direct_vals)<=1.20:
        eps=float(np.median(direct_vals));source='Yahoo TTM cross-check'
    elif len(candidates)>=2:
        vals=np.array([v for _,v in candidates]);med=float(np.median(vals));near=[(s,v) for s,v in candidates if .5<=v/med<=2]
        if len(near)>=2:eps=float(np.median([v for _,v in near]));source='Multi-source EPS median'
        else:eps,source=None,None
    else:eps,source=None,None
    return eps,source,candidates
def process(path):
    d=json.load(open(path,encoding='utf-8'));price=n(d.get('price'));raw=d.setdefault('raw',{});shares=n(raw.get('shares'))
    if not price or not shares:return d
    ticker=d.get('ticker') or path.stem+'.JK';t=yf.Ticker(ticker)
    try:info=t.info or {};h=t.history(period='5y',auto_adjust=False);inc=t.income_stmt
    except:return d
    if h.empty:return d
    guards=d.setdefault('quality',{}).setdefault('guards',[])
    eps,eps_source,candidates=recover_eps(info,price,raw,inc)
    raw['epsCandidates']=[{'source':s,'value':v} for s,v in candidates]
    if eps and eps>0:
        old=n(raw.get('epsTTM'));raw['epsTTM']=eps;raw['epsSource']=eps_source
        if old is None or abs(old/eps-1)>.20:guards.append(f'EPS TTM dipulihkan dengan cross-check {eps_source}: {eps:.4f} per saham.')
    else:
        guards.append('Adaptive P/E dilewati: EPS positif belum dapat divalidasi dari minimal dua sumber yang konsisten.');return d
    factor=n(raw.get('fxFactor')) or 1.0;nis=annual(inc,['Net Income','Net Income Common Stockholders'])
    if not nis:return d
    methods=[m for m in (d.get('methods') or []) if not str(m.get('name','')).startswith('Historical P/E')]
    cur=price/eps
    for yrs in (3,5):
        hh=h[h.index>=h.index.max()-pd.DateOffset(years=yrs)];vals=[]
        years_available=set(hh.index.year)
        for dt,ni in nis:
            if dt.year not in years_available:continue
            hist_eps=(ni*factor)/shares
            if hist_eps<=0:continue
            px=hh[hh.index.year==dt.year].Close.dropna()
            vals += [float(x)/hist_eps for x in px if .5<=float(x)/hist_eps<=500]
        b=adaptive_band(vals)
        if not b:continue
        low,med,high,sig,count=b;bear=low*eps;base=med*eps;bull=high*eps
        if not all(.05*price<=v<=5*price for v in (bear,base,bull)):continue
        high_mult=med>60 or cur>60;confidence=.72 if high_mult else .90
        warning='HIGH MULTIPLE · P/E >60x diterima karena konsisten dengan distribusi historis emiten; confidence diturunkan.' if high_mult else None
        methods.append({'name':f'Historical P/E {yrs}Y','family':'earnings','bear':bear,'base':base,'bull':bull,'confidence':confidence,'relevance':1.0,'rawWeight':confidence,'bands':{'mean':med,'sd':sig,'current':cur,'sampleCount':count,'adaptive':True,'hardCap':None,'epsSource':eps_source},'warning':warning,'explanation':f'EPS TTM tervalidasi ({eps_source}) × median P/E historis {yrs} tahun. Outlier dinilai relatif terhadap histori emiten.','included':False,'normalizedWeight':0,'qcStatus':'CANDIDATE'})
        if high_mult:guards.append(f'Historical P/E {yrs}Y adaptive: median {med:.1f}x, current {cur:.1f}x; confidence diturunkan.')
    d['methods']=methods;d['engineVersion']='3.10-adaptive-pe-eps';return d
changed=0
for p in DATA.glob('*.json'):
    if p.name in ('summary.json','errors.json'):continue
    try:d=process(p);json.dump(d,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False);changed+=1
    except Exception as e:print('ADAPTIVE_PE_ERR',p.stem,e)
print('ADAPTIVE_PE_EPS_DONE',changed)