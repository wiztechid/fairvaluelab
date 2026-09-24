import json, os, math
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import yfinance as yf
from des_universe import TICKERS as DES_TICKERS, SECTOR_BY_TICKER, DES_SOURCE

TICKERS=[x.strip().upper() for x in os.getenv('TICKERS','').split(',') if x.strip()] or DES_TICKERS
OUT='data'; os.makedirs(OUT,exist_ok=True)
OHLC_OUT=os.path.join(OUT,'ohlc_cache'); os.makedirs(OHLC_OUT,exist_ok=True)
FX_CACHE={}
def n(x):
    try:v=float(x);return v if math.isfinite(v) else None
    except:return None
def sd(a,b):
    a=n(a);b=n(b);return a/b if a is not None and b is not None and abs(b)>1e-12 else None
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
def fx_bundle(fc,qc):
    fc=(fc or '').upper();qc=(qc or '').upper()
    if not fc or not qc or fc==qc:return {'factor':1.0,'history':None,'pair':None,'applied':False}
    if (fc,qc) in FX_CACHE:return FX_CACHE[(fc,qc)]
    def get(pair,inv=False):
        try:
            h=yf.Ticker(pair).history(period='5y',auto_adjust=False).Close.dropna()
            if h.empty:return None
            if inv:h=1/h
            return {'factor':float(h.iloc[-1]),'history':h,'pair':pair,'applied':True}
        except:return None
    out=get(f'{fc}{qc}=X') or get(f'{qc}{fc}=X',True);FX_CACHE[(fc,qc)]=out;return out
def fx_for_date(b,d):
    if not b or not b.get('applied'):return 1.0
    h=b.get('history');fb=b.get('factor')
    if h is None or h.empty:return fb
    try:
        d=pd.Timestamp(d);idx=h.index
        if getattr(idx,'tz',None) is not None and d.tzinfo is None:d=d.tz_localize(idx.tz)
        elif getattr(idx,'tz',None) is None and d.tzinfo is not None:d=d.tz_localize(None)
        p=idx.get_indexer([d],method='nearest')[0];return float(h.iloc[p]) if p>=0 else fb
    except:return fb
def conv(a,b):return [(d,v*fx_for_date(b,d)) for d,v in a]
def cagr(a):
    if len(a)<3 or a[0][1]<=0 or a[-1][1]<=0:return None
    y=max(1,a[-1][0].year-a[0][0].year);return (a[-1][1]/a[0][1])**(1/y)-1
def clamp(v,lo,hi):return max(lo,min(hi,v))
def profile(ds,ys,ind):
    s=ds or ys or 'Umum';x=(ind or '').lower()
    if s=='Infrastruktur' and any(k in x for k in ['construction','engineering','building']):return 'Infrastruktur · Konstruksi',{'DCF':1.05,'FCF Yield':.85,'Historical P/E':1.15,'Historical PBV':.45},'Kontraktor dinilai terutama dari laba dan arus kas proyek; PBV hanya pendukung.'
    mp={'Infrastruktur':(1.2,1,.85,.6),'Properti & Real Estat':(.7,.55,.75,1.35),'Energi':(.65,1.1,.8,.55),'Barang Baku':(.7,1.05,.85,.65),'Perindustrian':(1,1,1,.65),'Barang Konsumen Primer':(1,1,1.2,.5),'Barang Konsumen Non-Primer':(1,1,1.2,.5),'Kesehatan':(1,.9,1.15,.45),'Teknologi':(1.15,.85,1,.25),'Transportasi & Logistik':(1.1,1.05,.9,.65)}
    if s=='Keuangan' or any(k in x for k in ['bank','financial','insurance']):return 'Keuangan',{'DCF':.15,'FCF Yield':.1,'Historical P/E':.85,'Historical PBV':1.55},'PBV/ROE menjadi acuan utama; FCF konvensional kurang representatif.'
    a=mp.get(s,(.9,.9,1,.65));return s,dict(zip(['DCF','FCF Yield','Historical P/E','Historical PBV'],a)),'Bobot metode disesuaikan dengan karakter sektor dan kualitas data.'
def tech(h):
    c=h.Close.dropna();last=float(c.iloc[-1]);ma=lambda p:n(c.rolling(p).mean().iloc[-1]) if len(c)>=p else None;d=c.diff();u=d.clip(lower=0).rolling(14).mean();dn=(-d.clip(upper=0)).rolling(14).mean();rs=u/dn.replace(0,np.nan)
    return {'ma20':ma(20),'ma50':ma(50),'ma200':ma(200),'rsi14':n((100-100/(1+rs)).iloc[-1]),'return1m':sd(last,c.iloc[-22])-1 if len(c)>=22 and sd(last,c.iloc[-22]) is not None else None,'return3m':sd(last,c.iloc[-66])-1 if len(c)>=66 and sd(last,c.iloc[-66]) is not None else None}
def history_years(h):return max(0,(h.index.max()-h.index.min()).days/365.25) if h is not None and not h.empty else 0
def hist_multiple(h,annual,shares,ps,years,kind,price):
    cov=history_years(h);req=2.5 if years==3 else 4.5
    if cov<req or not shares or not ps or ps<=0:return None
    hh=h[h.index>=h.index.max()-pd.DateOffset(years=years)];vals=[];cap=60 if kind=='pe' else 12;floor=1 if kind=='pe' else .2
    for d,total in annual:
        x=sd(total,shares)
        if not x or x<=0:continue
        px=hh[hh.index.year==d.year].Close
        if len(px):vals += [float(v) for v in (px/x).replace([np.inf,-np.inf],np.nan).dropna() if floor<=v<=cap]
    if len(vals)<30:return None
    a=np.array(vals,float);lo,hi=np.nanpercentile(a,[5,95]);a=a[(a>=lo)&(a<=hi)]
    if len(a)<10:return None
    med=float(np.median(a));mad=float(np.median(np.abs(a-med)));sig=1.4826*mad;cur=sd(price,ps)
    if cur is None or not floor<=cur<=cap:return None
    bear=max(floor,med-sig)*ps;base=med*ps;bull=min(cap,med+sig)*ps
    if not all(.05*price<=v<=5*price for v in [bear,base,bull]):return None
    return {'mean':med,'sd':sig,'current':cur,'z':sd(cur-med,sig) if sig>1e-12 else 0,'minus1':bear,'base':base,'plus1':bull,'coverageYears':cov}
def analyze(sym):
    tk=sym if '.' in sym else sym+'.JK';t=yf.Ticker(tk);info=t.info or {};h=t.history(period='5y',auto_adjust=False)
    if h.empty:raise ValueError('price unavailable')
    # Shared market-data cache: downstream technical engines must reuse this instead of refetching Yahoo.
    cache=h.tail(140)[['Open','High','Low','Close','Volume']].copy()
    cache.to_csv(os.path.join(OHLC_OUT,f\"{sym.replace('.JK','')}.csv\"))
    price=n(h.Close.dropna().iloc[-1]);ys=info.get('sector') or info.get('sectorDisp');ind=info.get('industry') or info.get('industryDisp');ds=SECTOR_BY_TICKER.get(sym.replace('.JK',''));sector,sw,note=profile(ds,ys,ind)
    inc=t.income_stmt;bs=t.balance_sheet;cf=t.cashflow;mcap=n(info.get('marketCap'));shares=n(info.get('sharesOutstanding') or info.get('impliedSharesOutstanding'));guards=[]
    qc=(info.get('currency') or 'IDR').upper();fc=(info.get('financialCurrency') or qc).upper();fx=fx_bundle(fc,qc)
    if fc!=qc:
        if not fx:raise ValueError(f'currency mismatch {fc}->{qc}; FX unavailable')
        guards.append(f'Laporan keuangan dinormalisasi {fc}→{qc} dengan FX Yahoo; data historis memakai FX terdekat tanggal laporan.')
    factor=fx.get('factor',1.0) if fx else 1.0;sm=sd(mcap,price) if mcap and price else None
    if shares and sm and not .8<=shares/sm<=1.25:shares=sm;guards.append('Jumlah saham direkonsiliasi dari market cap/harga karena denominator Yahoo tidak konsisten.')
    elif not shares:shares=sm
    ni0=stmt(inc,['Net Income','Net Income Common Stockholders']);eq0=stmt(bs,['Stockholders Equity','Total Stockholder Equity','Common Stock Equity']);ni=ni0*factor if ni0 is not None else None;eq=eq0*factor if eq0 is not None else None
    eps_calc=sd(ni,shares);eps_info=n(info.get('trailingEps'));eps=None
    if eps_calc and eps_calc>0:
        eps=eps_calc
        if eps_info and eps_info>0 and .5<=eps_info/eps_calc<=2:eps=eps_info
        elif eps_info and eps_info>0:guards.append('EPS Yahoo tidak konsisten dengan laba/jumlah saham; EPS hasil rekonsiliasi FX digunakan.')
    bvps=sd(eq,shares) if eq and eq>0 and shares else None;roe=n(info.get('returnOnEquity'));beta=n(info.get('beta')) or 1.;ocf0=stmt(cf,['Operating Cash Flow','Total Cash From Operating Activities']);capex0=stmt(cf,['Capital Expenditure','Capital Expenditures']);ocf=ocf0*factor if ocf0 is not None else None;capex=capex0*factor if capex0 is not None else None;fcf0=n(info.get('freeCashflow'));fcfv=fcf0*factor if fcf0 is not None else None
    if fcfv is None and ocf is not None and capex is not None:fcfv=ocf+capex if capex<0 else ocf-capex
    fcfps=sd(fcfv,shares);nis=conv(ser(inc,['Net Income','Net Income Common Stockholders']),fx);revs=conv(ser(inc,['Total Revenue']),fx);fcfs=conv(ser(cf,['Free Cash Flow']),fx);eqs=conv(ser(bs,['Stockholders Equity','Total Stockholder Equity','Common Stock Equity']),fx)
    gs=[g for g in [cagr(nis),cagr(revs),cagr(fcfs)] if g is not None];hg=float(np.median(gs)) if gs else .08;payout=n(info.get('payoutRatio'));sust=roe*(1-clamp(payout if payout is not None else .35,0,.9)) if roe is not None else None;growth=clamp(float(np.median([hg,sust])) if sust is not None else hg,-.03,.18);ke=clamp(.065+beta*.0738,.105,.22);terminal=.035;methods=[];dcfdiag=None;cov=history_years(h)
    pe=sd(price,eps) if eps and eps>0 else None;pbv=sd(price,bvps) if bvps and bvps>0 else None;pe_ok=pe is not None and 1<=pe<=60;pbv_ok=pbv is not None and .2<=pbv<=12
    if not pe_ok:guards.append('P/E tidak lolos sanity check atau EPS tidak tervalidasi; Historical P/E dinonaktifkan.')
    if not pbv_ok:guards.append('P/BV tidak lolos sanity check atau BVPS tidak tervalidasi; Historical PBV dinonaktifkan.')
    def rel(name,b):
        k='Historical P/E' if name.startswith('Historical P/E') else 'Historical PBV' if name.startswith('Historical PBV') else name;return b*sw.get(k,1)
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
        b,tvb=dcf(max(-.02,growth-.05),min(.24,ke+.02));base,tv=dcf(growth,ke);bu,tvu=dcf(min(.22,growth+.04),max(.095,ke-.015))
        if base:dcfdiag={'terminalValueShare':tv,'bearTerminalValueShare':tvb,'bullTerminalValueShare':tvu,'warning':bool(tv and tv>.70),'growth':growth,'costOfEquity':ke,'terminalGrowth':terminal};add('DCF',b,base,bu,.85,.65 if tv and tv>.70 else .85,'cashflow',warning='Porsi nilai jangka panjang tinggi' if tv and tv>.70 else None,explain='Estimasi nilai saham dari arus kas masa depan yang didiskontokan.')
        req=clamp(ke-growth*.2,.09,.18);add('FCF Yield',fcfps/.16,fcfps/req,fcfps/max(.08,req-.02),.75,.9,'cashflow',explain='Free cash flow per saham dibandingkan required cash yield.')
    if pe_ok:
        for yrs in [3,5]:
            x=hist_multiple(h,nis,shares,eps,yrs,'pe',price)
            if x:add(f'Historical P/E {yrs}Y',x['minus1'],x['base'],x['plus1'],.9,1,'earnings',x,explain=f'EPS tervalidasi dikalikan median P/E historis {yrs} tahun.')
    if pbv_ok:
        x=hist_multiple(h,eqs,shares,bvps,5,'pbv',price)
        if x:add('Historical PBV 5Y',x['minus1'],x['base'],x['plus1'],.8,.7,'book',x,explain='BVPS tervalidasi dikalikan median P/BV historis 5 tahun.')
    use=[];families=set();sufficient=False
    if methods:
        med=float(np.median([m['base'] for m in methods]));use=[m for m in methods if .4*med<=m['base']<=2.5*med];families={m['family'] for m in use};sufficient=len(use)>=2 and len(families)>=2
    if not methods:guards.append('Tidak ada metode core yang lolos QC; ticker tetap diterbitkan agar fallback model dapat dicoba.')
    elif not sufficient:guards.append('Composite FV belum diterbitkan: dibutuhkan minimal 2 metode dari keluarga valuasi independen.')
    tw=sum(m['rawWeight'] for m in use) if sufficient else 0
    for m in methods:m['included']=bool(sufficient and m in use);m['normalizedWeight']=sd(m['rawWeight'],tw) if sufficient and m in use else 0
    if sufficient:
        comp=lambda k:sum(m[k]*m['normalizedWeight'] for m in use);bear,base,bull=comp('bear'),comp('base'),comp('bull');vals=[m['base'] for m in use];disp=sd(float(np.std(vals)),float(np.mean(vals)));agreement='HIGH' if disp<.18 else 'MEDIUM' if disp<.32 else 'LOW'
    else:bear=base=bull=disp=None;agreement='INSUFFICIENT'
    cashconv=sd(fcfv,ni) if ni and ni>0 else None;checks=[price,eps,bvps,roe,fcfv,shares,mcap];avail=sum(v is not None for v in checks);qs=round(avail/7*100);ql='BAIK' if qs>=80 and sufficient else 'CUKUP' if qs>=60 else 'TERBATAS'
    return {'ticker':tk,'name':info.get('longName') or info.get('shortName') or tk,'asOf':datetime.now(timezone.utc).isoformat(),'price':price,'companyProfile':{'sector':ds or sector,'valuationProfile':sector,'sourceSector':ys,'industry':ind,'sectorNote':note,'sectorSource':'OJK DES Periode I 2026' if ds else 'Yahoo Finance'},'fairValue':{'bear':bear,'base':base,'bull':bull,'dispersion':disp,'agreement':agreement,'available':sufficient},'methods':methods,'dcfDiagnostics':dcfdiag,'technical':tech(h),'quality':{'cashConversion':cashconv,'roe':roe,'dataScore':qs,'dataLabel':ql,'availableInputs':avail,'totalInputs':7,'guards':guards,'historyYears':cov,'validMethodCount':len(use) if sufficient else 0,'independentFamilies':len(families) if sufficient else 0},'raw':{'epsTTM':eps,'bvps':bvps,'currentPE':pe,'currentPBV':pbv,'roe':roe,'fcf':fcfv,'growthNormalized':growth,'costOfEquity':ke,'terminalGrowth':terminal,'marketCap':mcap,'shares':shares,'quoteCurrency':qc,'financialCurrency':fc,'fxApplied':bool(fx and fx.get('applied')),'fxPair':fx.get('pair') if fx else None,'fxFactor':factor},'source':'Yahoo Finance via yfinance','universeSource':DES_SOURCE,'engineVersion':'3.8-all-tickers','analysisStatus':'SIAP' if sufficient else 'TERBATAS','freshnessStatus':'FRESH'}

summary=[];errors=[]
for s in TICKERS:
    try:
        d=analyze(s);json.dump(d,open(f'{OUT}/{s}.json','w'),ensure_ascii=False,indent=2,allow_nan=False);summary.append({'ticker':s,'sector':d['companyProfile']['sector'],'valuationProfile':d['companyProfile']['valuationProfile'],'price':d['price'],**d['fairValue'],'dataLabel':d['quality']['dataLabel'],'validMethods':d['quality']['validMethodCount'],'freshnessStatus':'FRESH'});print('OK',s)
    except Exception as e:
        err=str(e);oldpath=f'{OUT}/{s}.json';status='GAGAL_FETCH' if any(k in err.lower() for k in ['price unavailable','rate limit','too many requests','timeout','connection']) else 'ERROR_ENGINE'
        if os.path.exists(oldpath):
            try:
                old=json.load(open(oldpath,encoding='utf-8'));old['freshnessStatus']='STALE';old['analysisStatus']='STALE';old.setdefault('quality',{}).setdefault('guards',[]).append('Current run gagal: '+err[:180]+'; data sebelumnya dipertahankan dan ditandai STALE.');json.dump(old,open(oldpath,'w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False)
            except:pass
        errors.append({'ticker':s,'sector':SECTOR_BY_TICKER.get(s),'error':err,'status':status});print('ERR',s,err)
json.dump({'updatedAt':datetime.now(timezone.utc).isoformat(),'universeSource':DES_SOURCE,'count':len(summary),'requested':len(TICKERS),'stocks':summary,'errors':errors},open(f'{OUT}/summary.json','w'),ensure_ascii=False,indent=2,allow_nan=False)