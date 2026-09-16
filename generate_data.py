import json, os, math
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import yfinance as yf

TICKERS=[x.strip().upper() for x in os.getenv('TICKERS','TOTL,STAA,CMRY,PDPP,SMGA,PKPK,PORT,SMAR,GTRA,CINT,AMIN,CLPI,PSGO,UNIC,BULL,CASS,FORE,JTPE,DWGL').split(',') if x.strip()]
OUT='data';os.makedirs(OUT,exist_ok=True)

def n(x):
 try:
  v=float(x);return v if math.isfinite(v) else None
 except:return None

def safe_div(a,b):
 a=n(a);b=n(b)
 return a/b if a is not None and b is not None and abs(b)>1e-12 else None

def stmt(df,names):
 if df is None or df.empty:return None
 for k in names:
  if k in df.index:
   try:return n(df.loc[k].iloc[0])
   except:pass
 return None

def series(df,names):
 if df is None or df.empty:return []
 for k in names:
  if k in df.index:return sorted([(pd.Timestamp(d),float(v)) for d,v in df.loc[k].items() if pd.notna(v) and n(v) is not None])
 return []

def cagr(a):
 if len(a)<3 or a[0][1]<=0 or a[-1][1]<=0:return None
 y=max(1,a[-1][0].year-a[0][0].year);return (a[-1][1]/a[0][1])**(1/y)-1

def tech(h):
 c=h.Close.dropna();last=float(c.iloc[-1]);ma=lambda p:n(c.rolling(p).mean().iloc[-1]) if len(c)>=p else None;d=c.diff();u=d.clip(lower=0).rolling(14).mean();dn=(-d.clip(upper=0)).rolling(14).mean();rs=u/dn.replace(0,np.nan);e12=c.ewm(span=12,adjust=False).mean();e26=c.ewm(span=26,adjust=False).mean();m=e12-e26;s=m.ewm(span=9,adjust=False).mean()
 return {'ma20':ma(20),'ma50':ma(50),'ma200':ma(200),'rsi14':n((100-100/(1+rs)).iloc[-1]),'macd':n(m.iloc[-1]),'macdSignal':n(s.iloc[-1]),'return1m':safe_div(last,c.iloc[-22])-1 if len(c)>=22 and safe_div(last,c.iloc[-22]) is not None else None,'return3m':safe_div(last,c.iloc[-66])-1 if len(c)>=66 and safe_div(last,c.iloc[-66]) is not None else None,'low52':n(c.tail(252).min()),'high52':n(c.tail(252).max())}

def hist_mult(h,annual,shares,current_ps,years):
 shares=n(shares);current_ps=n(current_ps)
 if not shares or not current_ps or current_ps<=0:return None
 cutoff=h.index.max()-pd.DateOffset(years=years);hh=h[h.index>=cutoff];vals=[]
 for d,total in annual:
  ps=safe_div(total,shares)
  if ps is None or ps<=0:continue
  px=hh[hh.index.year==d.year].Close
  if len(px):vals+=list((px/ps).replace([np.inf,-np.inf],np.nan).dropna())
 if len(vals)<30:return None
 a=np.array(vals,float);a=a[np.isfinite(a)&(a>0)]
 if len(a)<30:return None
 cap=np.nanpercentile(a,99);a=a[a<cap]
 if len(a)<10:return None
 mean=float(np.mean(a));sd=float(np.std(a));current=safe_div(float(h.Close.iloc[-1]),current_ps)
 if current is None:return None
 return {'mean':mean,'sd':sd,'current':current,'z':safe_div(current-mean,sd) if sd>1e-12 else 0,'minus2':max(0,mean-2*sd)*current_ps,'minus1':max(0,mean-sd)*current_ps,'base':mean*current_ps,'plus1':(mean+sd)*current_ps,'plus2':(mean+2*sd)*current_ps}

def analyze(sym):
 tk=sym if '.' in sym else sym+'.JK';t=yf.Ticker(tk);info=t.info or {};h=t.history(period='5y',auto_adjust=False)
 if h.empty:raise ValueError('price unavailable')
 price=n(h.Close.dropna().iloc[-1]);inc=t.income_stmt;bs=t.balance_sheet;cf=t.cashflow;shares=n(info.get('sharesOutstanding') or info.get('impliedSharesOutstanding'));mcap=n(info.get('marketCap'))
 if not shares and mcap and price:shares=safe_div(mcap,price)
 ni=stmt(inc,['Net Income','Net Income Common Stockholders']);eq=stmt(bs,['Stockholders Equity','Total Stockholder Equity','Common Stock Equity']);eps=n(info.get('trailingEps')) or safe_div(ni,shares);bvps=safe_div(eq,shares) or n(info.get('bookValue'));roe=n(info.get('returnOnEquity'));beta=n(info.get('beta')) or 1.;ocf=stmt(cf,['Operating Cash Flow','Total Cash From Operating Activities']);capex=stmt(cf,['Capital Expenditure','Capital Expenditures']);fcf=n(info.get('freeCashflow'))
 if fcf is None and ocf is not None and capex is not None:fcf=ocf+capex if capex<0 else ocf-capex
 fcfps=safe_div(fcf,shares);ni_s=series(inc,['Net Income','Net Income Common Stockholders']);rev_s=series(inc,['Total Revenue']);fcf_s=series(cf,['Free Cash Flow']);eq_s=series(bs,['Stockholders Equity','Total Stockholder Equity','Common Stock Equity']);gs=[g for g in [cagr(ni_s),cagr(rev_s),cagr(fcf_s)] if g is not None];hg=float(np.median(gs)) if gs else .08;payout=n(info.get('payoutRatio'));sust=roe*(1-min(max(payout if payout is not None else .35,0),.9)) if roe is not None else None;growth=min(.18,max(-.03,float(np.median([hg,sust])) if sust is not None else hg));rf=.065;erp=.0738;ke=min(.22,max(.105,rf+beta*erp));terminal=.035;methods=[];dcfdiag=None
 def add(name,bear,base,bull,conf,rel,bands=None,warning=None):
  vals=[n(bear),n(base),n(bull)]
  if all(v is not None and v>0 for v in vals):methods.append({'name':name,'bear':vals[0],'base':vals[1],'bull':vals[2],'confidence':conf,'relevance':rel,'rawWeight':conf*rel,'bands':bands,'warning':warning})
 if fcfps and fcfps>0 and ke>terminal:
  def dcf(g,k):
   spread=k-terminal
   if spread<=.01:return None,None
   f=fcfps;s=0
   for yr in range(1,6):f*=1+g;s+=f/(1+k)**yr
   tv=f*(1+terminal)/spread/(1+k)**5;total=s+tv;return total,safe_div(tv,total)
  b,tvb=dcf(max(-.02,growth-.05),min(.24,ke+.02));base,tv=dcf(growth,ke);bu,tvu=dcf(min(.22,growth+.04),max(.095,ke-.015))
  if base and tv is not None:
   rel=.65 if tv>.70 else .85;dcfdiag={'terminalValueShare':tv,'bearTerminalValueShare':tvb,'bullTerminalValueShare':tvu,'warning':tv>.70};add('DCF',b,base,bu,.85,rel,warning='Terminal value high' if tv>.70 else None)
  req=min(.18,max(.09,ke-growth*.20));add('FCF Yield',fcfps/.16,fcfps/req,fcfps/max(.08,req-.02),.75,.90)
 for yrs in [3,5]:
  pe=hist_mult(h,ni_s,shares,eps,yrs)
  if pe:add(f'Historical P/E {yrs}Y',pe['minus1'],pe['base'],pe['plus1'],.9,1.,pe)
 pbv=hist_mult(h,eq_s,shares,bvps,5)
 if pbv:add('Historical PBV 5Y',pbv['minus1'],pbv['base'],pbv['plus1'],.8,.45 if roe and roe>.25 else .7,pbv,'Low relevance for high-ROE business' if roe and roe>.25 else None)
 cashconv=safe_div(fcf,ni) if ni and ni>0 else None;bases=[m['base'] for m in methods if m.get('base') and m['base']>0]
 if not bases:raise ValueError('insufficient usable valuation inputs')
 med=float(np.median(bases));use=[m for m in methods if .30*med<=m['base']<=3*med];totalw=sum(m['rawWeight'] for m in use)
 if not use or totalw<=0:raise ValueError('no usable valuation models after validation')
 for m in methods:m['included']=m in use;m['upside']=safe_div(m['base'],price)-1 if safe_div(m['base'],price) is not None else None;m['normalizedWeight']=safe_div(m['rawWeight'],totalw) if m in use else 0
 def comp(k):return sum(m[k]*m['normalizedWeight'] for m in use)
 bear,base,bull=comp('bear'),comp('base'),comp('bull');avg=float(np.mean([m['base'] for m in use]));disp=safe_div(float(np.std([m['base'] for m in use])),avg) if len(use)>1 else .5;disp=disp if disp is not None else 1.;agreement='HIGH' if disp<.18 else 'MEDIUM' if disp<.32 else 'LOW';conf=round(100*max(0,min(1,.55*min(1,len(use)/5)+.45*(1-min(disp,1)))));potential=safe_div(base,price);potential=potential-1 if potential is not None else None;premium=safe_div(price,base);premium=premium-1 if premium is not None else None;label=(f"Below Fair Value {abs(premium)*100:.1f}%" if premium<0 else f"Above Fair Value {premium*100:.1f}%") if premium is not None else 'Fair value unavailable';currentPE=safe_div(price,eps) if eps and eps>0 else None;currentPBV=safe_div(price,bvps) if bvps and bvps>0 else None
 return {'ticker':tk,'name':info.get('longName') or info.get('shortName') or tk,'asOf':datetime.now(timezone.utc).isoformat(),'price':price,'fairValue':{'bear':bear,'base':base,'bull':bull,'potential':potential,'upside':potential,'pricePremium':premium,'label':label,'confidence':conf,'dispersion':disp,'agreement':agreement},'methods':methods,'dcfDiagnostics':dcfdiag,'technical':tech(h),'quality':{'cashConversion':cashconv,'roe':roe},'raw':{'epsTTM':eps,'bvps':bvps,'currentPE':currentPE,'currentPBV':currentPBV,'roe':roe,'fcf':fcf,'fcfPerShare':fcfps,'growthNormalized':growth,'costOfEquity':ke,'terminalGrowth':terminal,'marketCap':mcap,'shares':shares},'source':'Yahoo Finance via yfinance'}

summary=[];errors=[]
for s in TICKERS:
 try:
  d=analyze(s);json.dump(d,open(f'{OUT}/{s}.json','w'),ensure_ascii=False,indent=2,allow_nan=False);summary.append({'ticker':s,'price':d['price'],**d['fairValue']});print('OK',s)
 except Exception as e:
  errors.append({'ticker':s,'error':str(e)});print('ERR',s,e)
json.dump({'updatedAt':datetime.now(timezone.utc).isoformat(),'count':len(summary),'requested':len(TICKERS),'stocks':summary,'errors':errors},open(f'{OUT}/summary.json','w'),ensure_ascii=False,indent=2,allow_nan=False)
