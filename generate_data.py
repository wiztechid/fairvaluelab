import json, os, math
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import yfinance as yf

TICKERS=[x.strip().upper() for x in os.getenv('TICKERS','TOTL,STAA,CMRY,PDPP,SMGA,PKPK,PORT,SMAR,GTRA,CINT,AMIN,CLPI,PSGO,UNIC,BULL,CASS,FORE,JTPE,DWGL').split(',') if x.strip()]
OUT='data'; os.makedirs(OUT,exist_ok=True)

def n(x):
    try:
        v=float(x); return v if math.isfinite(v) else None
    except:return None

def stmt(df,names):
    if df is None or df.empty:return None
    for k in names:
        if k in df.index:
            try:return n(df.loc[k].iloc[0])
            except:pass

def series(df,names):
    if df is None or df.empty:return []
    for k in names:
        if k in df.index:
            a=[]
            for d,v in df.loc[k].items():
                if pd.notna(v):a.append((pd.Timestamp(d),float(v)))
            return sorted(a)
    return []

def cagr(a):
    if len(a)<3:return None
    old,new=a[0][1],a[-1][1]; years=max(1,a[-1][0].year-a[0][0].year)
    if old<=0 or new<=0:return None
    return (new/old)**(1/years)-1

def technical(h):
    c=h.Close.dropna(); last=float(c.iloc[-1])
    ma=lambda p: n(c.rolling(p).mean().iloc[-1]) if len(c)>=p else None
    d=c.diff(); up=d.clip(lower=0).rolling(14).mean(); dn=(-d.clip(upper=0)).rolling(14).mean(); rs=up/dn.replace(0,np.nan)
    rsi=n((100-100/(1+rs)).iloc[-1])
    e12=c.ewm(span=12,adjust=False).mean();e26=c.ewm(span=26,adjust=False).mean();macd=e12-e26;sig=macd.ewm(span=9,adjust=False).mean()
    return {'ma20':ma(20),'ma50':ma(50),'ma200':ma(200),'rsi14':rsi,'macd':n(macd.iloc[-1]),'macdSignal':n(sig.iloc[-1]),'return1m':n(last/c.iloc[-22]-1) if len(c)>=22 else None,'return3m':n(last/c.iloc[-66]-1) if len(c)>=66 else None,'low52':n(c.tail(252).min()),'high52':n(c.tail(252).max())}

def hist_mult(h,annual,shares,current_ps,kind):
    if not shares or not current_ps or current_ps<=0:return None
    vals=[]
    for d,total in annual:
        ps=total/shares
        if ps<=0:continue
        px=h[h.index.year==d.year].Close
        if len(px):vals += list((px/ps).replace([np.inf,-np.inf],np.nan).dropna().values)
    if len(vals)<30:return None
    a=np.array(vals,float); a=a[(a>0)&(a<np.nanpercentile(a,99))]
    mean=float(np.mean(a));sd=float(np.std(a))
    return {'mean':mean,'sd':sd,'minus2':max(0,mean-2*sd)*current_ps,'minus1':max(0,mean-sd)*current_ps,'base':mean*current_ps,'plus1':(mean+sd)*current_ps,'plus2':(mean+2*sd)*current_ps}

def analyze(sym):
    tk=sym if '.' in sym else sym+'.JK'; t=yf.Ticker(tk); info=t.info or {}; h=t.history(period='5y',auto_adjust=False)
    if h.empty:raise ValueError('price unavailable')
    price=n(h.Close.dropna().iloc[-1]); inc=t.income_stmt;bs=t.balance_sheet;cf=t.cashflow
    shares=n(info.get('sharesOutstanding') or info.get('impliedSharesOutstanding')); mcap=n(info.get('marketCap'))
    if not shares and mcap and price:shares=mcap/price
    ni=stmt(inc,['Net Income','Net Income Common Stockholders']); eq=stmt(bs,['Stockholders Equity','Total Stockholder Equity','Common Stock Equity'])
    eps=n(info.get('trailingEps')) or (ni/shares if ni and shares else None);bvps=(eq/shares if eq and shares else n(info.get('bookValue')))
    roe=n(info.get('returnOnEquity')); beta=n(info.get('beta')) or 1.0; ocf=stmt(cf,['Operating Cash Flow','Total Cash From Operating Activities']);capex=stmt(cf,['Capital Expenditure','Capital Expenditures'])
    fcf=n(info.get('freeCashflow'))
    if not fcf and ocf is not None and capex is not None:fcf=ocf+capex if capex<0 else ocf-capex
    fcfps=fcf/shares if fcf and shares else None
    ni_s=series(inc,['Net Income','Net Income Common Stockholders']); rev_s=series(inc,['Total Revenue']);fcf_s=series(cf,['Free Cash Flow']);eq_s=series(bs,['Stockholders Equity','Total Stockholder Equity','Common Stock Equity'])
    gs=[g for g in [cagr(ni_s),cagr(rev_s),cagr(fcf_s)] if g is not None]
    hg=float(np.median(gs)) if gs else .08; payout=n(info.get('payoutRatio')); sustainable=roe*(1-min(max(payout if payout is not None else .35,0),.9)) if roe is not None else None
    growth=min(.25,max(-.05,float(np.median([hg,sustainable])) if sustainable is not None else hg))
    rf=.065;erp=.0738;ke=min(.22,max(.10,rf+beta*erp));terminal=.04
    methods=[]
    if fcfps and fcfps>0 and ke>terminal:
        def dcf(g,k):
            f=fcfps;s=0
            for yr in range(1,6):f*=1+g;s+=f/(1+k)**yr
            return s+(f*(1+terminal)/(k-terminal))/(1+k)**5
        methods.append({'name':'DCF','bear':dcf(max(-.03,growth-.05),min(.24,ke+.02)),'base':dcf(growth,ke),'bull':dcf(min(.30,growth+.05),max(.09,ke-.02)),'confidence':.85})
        req=min(.18,max(.08,ke-growth*.25));methods.append({'name':'FCF Yield','bear':fcfps/.16,'base':fcfps/req,'bull':fcfps/max(.07,req-.02),'confidence':.7})
    pe=hist_mult(h,ni_s,shares,eps,'pe');pbv=hist_mult(h,eq_s,shares,bvps,'pbv')
    if pe:methods.append({'name':'Historical P/E 5Y','bear':pe['minus1'],'base':pe['base'],'bull':pe['plus1'],'confidence':.85,'bands':pe})
    if pbv:methods.append({'name':'Historical PBV 5Y','bear':pbv['minus1'],'base':pbv['base'],'bull':pbv['plus1'],'confidence':.8,'bands':pbv})
    if bvps and roe and ke>growth:
        j=(roe-growth)/(ke-growth)
        if j>0:methods.append({'name':'Justified PBV','bear':bvps*j*.85,'base':bvps*j,'bull':bvps*j*1.15,'confidence':.7})
    bases=[m['base'] for m in methods if m.get('base') and m['base']>0]
    if not bases:raise ValueError('insufficient fundamentals')
    med=float(np.median(bases));use=[m for m in methods if .25*med<=m['base']<=4*med]
    def comp(k):return sum(m[k]*m['confidence'] for m in use)/sum(m['confidence'] for m in use)
    bear,base,bull=comp('bear'),comp('base'),comp('bull');disp=float(np.std([m['base'] for m in use])/np.mean([m['base'] for m in use])) if len(use)>1 else .5
    conf=round(100*max(0,min(1,.55*min(1,len(use)/5)+.45*(1-min(disp,1)))))
    ratio=price/base;label='DEEP UNDERVALUED' if ratio<.70 else 'UNDERVALUED' if ratio<.85 else 'FAIR / WATCH' if ratio<=1.10 else 'EXPENSIVE' if ratio<=1.30 else 'VERY EXPENSIVE'
    for m in methods:m['upside']=m['base']/price-1;m['included']=m in use
    return {'ticker':tk,'name':info.get('longName') or info.get('shortName') or tk,'asOf':datetime.now(timezone.utc).isoformat(),'price':price,'fairValue':{'bear':bear,'base':base,'bull':bull,'upside':base/price-1,'label':label,'confidence':conf,'dispersion':disp},'methods':methods,'technical':technical(h),'raw':{'epsTTM':eps,'bvps':bvps,'roe':roe,'fcf':fcf,'fcfPerShare':fcfps,'growthNormalized':growth,'costOfEquity':ke,'terminalGrowth':terminal,'marketCap':mcap,'shares':shares},'source':'Yahoo Finance via yfinance'}

summary=[]
for s in TICKERS:
    try:
        d=analyze(s);json.dump(d,open(f'{OUT}/{s}.json','w'),ensure_ascii=False,indent=2);summary.append({'ticker':s,'price':d['price'],**d['fairValue']});print('OK',s)
    except Exception as e:print('ERR',s,e)
json.dump({'updatedAt':datetime.now(timezone.utc).isoformat(),'count':len(summary),'stocks':summary},open(f'{OUT}/summary.json','w'),ensure_ascii=False,indent=2)
