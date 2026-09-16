import json, os, math
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import yfinance as yf
from des_universe import TICKERS as DES_TICKERS, SECTOR_BY_TICKER, DES_SOURCE

TICKERS=[x.strip().upper() for x in os.getenv('TICKERS','').split(',') if x.strip()] or DES_TICKERS
OUT='data'; os.makedirs(OUT,exist_ok=True)
FX_CACHE={}

def n(x):
    try:
        v=float(x); return v if math.isfinite(v) else None
    except:return None

def sd(a,b):
    a=n(a); b=n(b); return a/b if a is not None and b is not None and abs(b)>1e-12 else None

def stmt(df,names):
    if df is None or df.empty:return None
    for k in names:
        if k in df.index:
            try:return n(df.loc[k].iloc[0])
            except:pass
    return None

def ser(df,names):
    if df is None or df.empty:return []
    for k in names:
        if k in df.index:return sorted([(pd.Timestamp(d),float(v)) for d,v in df.loc[k].items() if pd.notna(v) and n(v) is not None])
    return []

def fx_bundle(financial_currency,quote_currency):
    fc=(financial_currency or '').upper(); qc=(quote_currency or '').upper()
    if not fc or not qc or fc==qc:return {'factor':1.0,'history':None,'pair':None,'applied':False}
    key=(fc,qc)
    if key in FX_CACHE:return FX_CACHE[key]
    def fetch(pair,invert=False):
        try:
            h=yf.Ticker(pair).history(period='5y',auto_adjust=False).Close.dropna()
            if h.empty:return None
            if invert:h=1/h
            return {'factor':float(h.iloc[-1]),'history':h,'pair':pair,'applied':True}
        except:return None
    out=fetch(f'{fc}{qc}=X') or fetch(f'{qc}{fc}=X',True)
    FX_CACHE[key]=out
    return out

def fx_for_date(bundle,date):
    if not bundle or not bundle.get('applied'):return 1.0
    h=bundle.get('history'); fallback=bundle.get('factor')
    if h is None or h.empty:return fallback
    try:
        d=pd.Timestamp(date); idx=h.index
        if getattr(idx,'tz',None) is not None and d.tzinfo is None:d=d.tz_localize(idx.tz)
        elif getattr(idx,'tz',None) is None and d.tzinfo is not None:d=d.tz_localize(None)
        pos=idx.get_indexer([d],method='nearest')[0]
        return float(h.iloc[pos]) if pos>=0 else fallback
    except:return fallback

def convert_series(values,bundle):return [(d,v*fx_for_date(bundle,d)) for d,v in values]

def cagr(a):
    if len(a)<3 or a[0][1]<=0 or a[-1][1]<=0:return None
    y=max(1,a[-1][0].year-a[0][0].year); return (a[-1][1]/a[0][1])**(1/y)-1

def clamp(v,lo,hi):return max(lo,min(hi,v))

def profile(ds,ys,ind):
    s=ds or ys or 'Umum'; x=(ind or '').lower()
    if s=='Infrastruktur' and any(k in x for k in ['construction','engineering','building']):return 'Infrastruktur · Konstruksi',{'DCF':1.05,'FCF Yield':.85,'Historical P/E':1.15,'Historical PBV':.45},'Kontraktor dinilai terutama dari laba dan arus kas proyek; PBV hanya pendukung.'
    mp={'Infrastruktur':(1.2,1,.85,.6),'Properti & Real Estat':(.7,.55,.75,1.35),'Energi':(.65,1.1,.8,.55),'Barang Baku':(.7,1.05,.85,.65),'Perindustrian':(1,1,1,.65),'Barang Konsumen Primer':(1,1,1.2,.5),'Barang Konsumen Non-Primer':(1,1,1.2,.5),'Kesehatan':(1,.9,1.15,.45),'Teknologi':(1.15,.85,1,.25),'Transportasi & Logistik':(1.1,1.05,.9,.65)}
    if s=='Keuangan' or any(k in x for k in ['bank','financial','insurance']):return 'Keuangan',{'DCF':.15,'FCF Yield':.1,'Historical P/E':.85,'Historical PBV':1.55},'PBV/ROE menjadi acuan utama; FCF konvensional kurang representatif.'
    a=mp.get(s,(.9,.9,1,.65)); return s,dict(zip(['DCF','FCF Yield','Historical P/E','Historical PBV'],a)),'Bobot metode disesuaikan dengan karakter sektor dan kualitas data.'

def tech(h):
    c=h.Close.dropna(); last=float(c.iloc[-1]); ma=lambda p:n(c.rolling(p).mean().iloc[-1]) if len(c)>=p else None
    d=c.diff(); u=d.clip(lower=0).rolling(14).mean(); dn=(-d.clip(upper=0)).rolling(14).mean(); rs=u/dn.replace(0,np.nan)
    return {'ma20':ma(20),'ma50':ma(50),'ma200':ma(200),'rsi14':n((100-100/(1+rs)).iloc[-1]),'return1m':sd(last,c.iloc[-22])-1 if len(c)>=22 and sd(last,c.iloc[-22]) is not None else None,'return3m':sd(last,c.iloc[-66])-1 if len(c)>=66 and sd(last,c.iloc[-66]) is not None else None}

def history_years(h):return max(0,(h.index.max()-h.index.min()).days/365.25) if h is not None and not h.empty else 0

def hist_multiple(h,annual,shares,current_ps,years,kind,price):
    coverage=history_years(h); required=2.5 if years==3 else 4.5
    if coverage<required or not shares or not current_ps or current_ps<=0:return None
    hh=h[h.index>=h.index.max()-pd.DateOffset(years=years)]; vals=[]; cap=60 if kind=='pe' else 12; floor=1 if kind=='pe' else .2
    for d,total in annual:
        ps=sd(total,shares)
        if not ps or ps<=0:continue
        px=hh[hh.index.year==d.year].Close
        if len(px):vals += [float(v) for v in (px/ps).replace([np.inf,-np.inf],np.nan).dropna() if floor<=v<=cap]
    if len(vals)<30:return None
    a=np.array(vals,float); lo,hi=np.nanpercentile(a,[5,95]); a=a[(a>=lo)&(a<=hi)]
    if len(a)<10:return None
    med=float(np.median(a)); mad=float(np.median(np.abs(a-med))); sigma=1.4826*mad; cur=sd(price,current_ps)
    if cur is None or not floor<=cur<=cap:return None
    bear=max(floor,med-sigma)*current_ps; base=med*current_ps; bull=min(cap,med+sigma)*current_ps
    if not all(.05*price<=v<=5*price for v in [bear,base,bull]):return None
    return {'mean':med,'sd':sigma,'current':cur,'z':sd(cur-med,sigma) if sigma>1e-12 else 0,'minus1':bear,'base':base,'plus1':bull,'coverageYears':coverage}

def analyze(sym):
    tk=sym if '.' in sym else sym+'.JK'; t=yf.Ticker(tk); info=t.info or {}; h=t.history(period='5y',auto_adjust=False)
    if h.empty:raise ValueError('price unavailable')
    price=n(h.Close.dropna().iloc[-1]); ys=info.get('sector') or info.get('sectorDisp'); ind=info.get('industry') or info.get('industryDisp'); ds=SECTOR_BY_TICKER.get(sym.replace('.JK','')); sector,sw,note=profile(ds,ys,ind)
    inc=t.income_stmt; bs=t.balance_sheet; cf=t.cashflow; mcap=n(info.get('marketCap')); shares=n(info.get('sharesOutstanding') or info.get('impliedSharesOutstanding')); guards=[]
    quote_currency=(info.get('currency') or 'IDR').upper(); financial_currency=(info.get('financialCurrency') or quote_currency).upper(); fx=fx_bundle(financial_currency,quote_currency)
    if financial_currency!=quote_currency:
        if not fx:raise ValueError(f'currency mismatch {financial_currency}->{quote_currency}; FX unavailable')
        guards.append(f'Laporan keuangan dinormalisasi {financial_currency}→{quote_currency} dengan FX Yahoo; data historis memakai FX terdekat tanggal laporan.')
    factor=fx.get('factor',1.0) if fx else 1.0
    sm=sd(mcap,price) if mcap and price else None
    if shares and sm and not .8<=shares/sm<=1.25:shares=sm; guards.append('Jumlah saham direkonsiliasi dari market cap/harga karena denominator Yahoo tidak konsisten.')
    elif not shares:shares=sm
    ni0=stmt(inc,['Net Income','Net Income Common Stockholders']); eq0=stmt(bs,['Stockholders Equity','Total Stockholder Equity','Common Stock Equity']); ni=ni0*factor if ni0 is not None else None; eq=eq0*factor if eq0 is not None else None
    eps_calc=sd(ni,shares); eps_info=n(info.get('trailingEps')); eps=None
    if eps_calc and eps_calc>0:
        eps=eps_calc
        if eps_info and eps_info>0 and .5<=eps_info/eps_calc<=2:eps=eps_info
        elif eps_info and eps_info>0:guards.append('EPS Yahoo tidak konsisten dengan laba/jumlah saham; EPS hasil rekonsiliasi FX digunakan.')
    bvps=sd(eq,shares) if eq and eq>0 and shares else None
    roe=n(info.get('returnOnEquity')); beta=n(info.get('beta')) or 1.; ocf0=stmt(cf,['Operating Cash Flow','Total Cash From Operating Activities']); capex0=stmt(cf,['Capital Expenditure','Capital Expenditures']); ocf=ocf0*factor if ocf0 is not None else None; capex=capex0*factor if capex0 is not None else None; fcf0=n(info.get('freeCashflow')); fcf=fcf0*factor if fcf0 is not None else None
    if fcf is None and ocf is not None and capex is not None:fcf=ocf+capex if capex<0 else ocf-capex
    fcfps=sd(fcf,shares); nis=convert_series(ser(inc,['Net Income','Net Income Common Stockholders']),fx); revs=convert_series(ser(inc,['Total Revenue']),fx); fcfs=convert_series(ser(cf,['Free Cash Flow']),fx); eqs=convert_series(ser(bs,['Stockholders Equity','Total Stockholder Equity','Common Stock Equity']),fx)
    gs=[g for g in [cagr(nis),cagr(revs),cagr(fcfs)] if g is not None]; hg=float(np.median(gs)) if gs else .08; payout=n(info.get('payoutRatio')); sust=roe*(1-clamp(payout if payout is not None else .35,0,.9)) if roe is not None else None
    growth=clamp(float(np.median([hg,sust])) if sust is not None else hg,-.03,.18); ke=clamp(.065+beta*.0738,.105,.22); terminal=.035; methods=[]; dcfdiag=None; coverage=history_years(h)
    currentPE=sd(price,eps) if eps and eps>0 else None; currentPBV=sd(price,bvps) if bvps and bvps>0 else None; pe_ok=currentPE is not None and 1<=currentPE<=60; pbv_ok=currentPBV is not None and .2<=currentPBV<=12
    if not pe_ok:guards.append('P/E tidak lolos sanity check atau EPS tidak tervalidasi; Historical P/E dinonaktifkan.')
    if not pbv_ok:guards.append('P/BV tidak lolos sanity check atau BVPS tidak tervalidasi; Historical PBV dinonaktifkan.')
    def rel(name,b):
        key='Historical P/E' if name.startswith('Historical P/E') else 'Historical PBV' if name.startswith('Historical PBV') else name; return b*sw.get(key,1)
    def add(name,bear,base,bull,q,r,family,bands=None,warning=None,explain=''):
        vals=[n(bear),n(base),n(bull)]
        if all(v is not None and .05*price<=v<=5*price for v in vals):methods.append({'name':name,'family':family,'bear':vals[0],'base':vals[1],'bull':vals[2],'confidence':q,'relevance':rel(name,r),'rawWeight':q*rel(name,r),'bands':bands,'warning':warning,'explanation':explain})
        else:guards.append(f'{name} ditolak economic sanity guard karena hasil tidak konsisten dengan skala harga pasar.')
    if fcfps and fcfps>0 and ke>terminal:
        def dcf(g,k):
            if k-terminal<=.01:return None,None
            f=fcfps;s=0
            for yr in range(1,6):f*=1+g;s+=f/(1+k)**yr
            tv=f*(1+terminal)/(k-terminal)/(1+k)**5;return s+tv,sd(tv,s+tv)
        b,tvb=dcf(max(-.02,growth-.05),min(.24,ke+.02)); base,tv=dcf(growth,ke); bu,tvu=dcf(min(.22,growth+.04),max(.095,ke-.015))
        if base:
            rr=.65 if tv and tv>.70 else .85; dcfdiag={'terminalValueShare':tv,'bearTerminalValueShare':tvb,'bullTerminalValueShare':tvu,'warning':bool(tv and tv>.70),'growth':growth,'costOfEquity':ke,'terminalGrowth':terminal}; add('DCF',b,base,bu,.85,rr,'cashflow',warning='Porsi nilai jangka panjang tinggi' if tv and tv>.70 else None,explain='Estimasi nilai saham dari arus kas masa depan yang didiskontokan.')
        req=clamp(ke-growth*.2,.09,.18); add('FCF Yield',fcfps/.16,fcfps/req,fcfps/max(.08,req-.02),.75,.9,'cashflow',explain='Free cash flow per saham dibandingkan required cash yield.')
    if pe_ok:
        for yrs in [3,5]:
            pe=hist_multiple(h,nis,shares,eps,yrs,'pe',price)
            if pe:add(f'Historical P/E {yrs}Y',pe['minus1'],pe['base'],pe['plus1'],.9,1,'earnings',pe,explain=f'EPS tervalidasi dikalikan median P/E historis {yrs} tahun.')
    if pbv_ok:
        pb=hist_multiple(h,eqs,shares,bvps,5,'pbv',price)
        if pb:add('Historical PBV 5Y',pb['minus1'],pb['base'],pb['plus1'],.8,.7,'book',pb,explain='BVPS tervalidasi dikalikan median P/BV historis 5 tahun.')
    if not methods:raise ValueError('no usable valuation models after QC')
    med=float(np.median([m['base'] for m in methods])); use=[m for m in methods if .4*med<=m['base']<=2.5*med]; families=set(m['family'] for m in use); sufficient=len(use)>=2 and len(families)>=2
    if not sufficient:guards.append('Composite FV tidak diterbitkan: dibutuhkan minimal 2 metode dari keluarga valuasi independen.')
    tw=sum(m['rawWeight'] for m in use) if sufficient else 0
    for m in methods:m['included']=bool(sufficient and m in use); m['normalizedWeight']=sd(m['rawWeight'],tw) if sufficient and m in use else 0
    if sufficient:
        comp=lambda k:sum(m[k]*m['normalizedWeight'] for m in use); bear,base,bull=comp('bear'),comp('base'),comp('bull'); vals=[m['base'] for m in use]; disp=sd(float(np.std(vals)),float(np.mean(vals))); agreement='HIGH' if disp<.18 else 'MEDIUM' if disp<.32 else 'LOW'
    else:bear=base=bull=disp=None; agreement='INSUFFICIENT'
    cashconv=sd(fcf,ni) if ni and ni>0 else None; checks=[price,eps,bvps,roe,fcf,shares,mcap]; available=sum(v is not None for v in checks); qs=round(available/7*100); ql='BAIK' if qs>=80 and sufficient else 'CUKUP' if qs>=60 else 'TERBATAS'
    return {'ticker':tk,'name':info.get('longName') or info.get('shortName') or tk,'asOf':datetime.now(timezone.utc).isoformat(),'price':price,'companyProfile':{'sector':ds or sector,'valuationProfile':sector,'sourceSector':ys,'industry':ind,'sectorNote':note,'sectorSource':'OJK DES Periode I 2026' if ds else 'Yahoo Finance'},'fairValue':{'bear':bear,'base':base,'bull':bull,'dispersion':disp,'agreement':agreement,'available':sufficient},'methods':methods,'dcfDiagnostics':dcfdiag,'technical':tech(h),'quality':{'cashConversion':cashconv,'roe':roe,'dataScore':qs,'dataLabel':ql,'availableInputs':available,'totalInputs':7,'guards':guards,'historyYears':coverage,'validMethodCount':len(use) if sufficient else 0,'independentFamilies':len(families) if sufficient else 0},'raw':{'epsTTM':eps,'bvps':bvps,'currentPE':currentPE,'currentPBV':currentPBV,'roe':roe,'fcf':fcf,'growthNormalized':growth,'costOfEquity':ke,'terminalGrowth':terminal,'marketCap':mcap,'shares':shares,'quoteCurrency':quote_currency,'financialCurrency':financial_currency,'fxApplied':bool(fx and fx.get('applied')),'fxPair':fx.get('pair') if fx else None,'fxFactor':factor},'source':'Yahoo Finance via yfinance','universeSource':DES_SOURCE,'engineVersion':'3.7-fx-normalized'}

summary=[]; errors=[]
for s in TICKERS:
    try:
        d=analyze(s); json.dump(d,open(f'{OUT}/{s}.json','w'),ensure_ascii=False,indent=2,allow_nan=False); summary.append({'ticker':s,'sector':d['companyProfile']['sector'],'valuationProfile':d['companyProfile']['valuationProfile'],'price':d['price'],**d['fairValue'],'dataLabel':d['quality']['dataLabel'],'validMethods':d['quality']['validMethodCount']}); print('OK',s)
    except Exception as e:errors.append({'ticker':s,'sector':SECTOR_BY_TICKER.get(s),'error':str(e)}); print('ERR',s,e)
json.dump({'updatedAt':datetime.now(timezone.utc).isoformat(),'universeSource':DES_SOURCE,'count':len(summary),'requested':len(TICKERS),'stocks':summary,'errors':errors},open(f'{OUT}/summary.json','w'),ensure_ascii=False,indent=2,allow_nan=False)
