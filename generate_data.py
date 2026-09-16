import json, os, math
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import yfinance as yf
from des_universe import TICKERS as DES_TICKERS, SECTOR_BY_TICKER, DES_SOURCE

TICKERS=[x.strip().upper() for x in os.getenv('TICKERS','').split(',') if x.strip()] or DES_TICKERS
OUT='data'; os.makedirs(OUT,exist_ok=True)

def n(x):
    try:
        v=float(x); return v if math.isfinite(v) else None
    except: return None

def sd(a,b):
    a=n(a); b=n(b)
    return a/b if a is not None and b is not None and abs(b)>1e-12 else None

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
        if k in df.index:
            return sorted([(pd.Timestamp(d),float(v)) for d,v in df.loc[k].items() if pd.notna(v) and n(v) is not None])
    return []

def cagr(a):
    if len(a)<3 or a[0][1]<=0 or a[-1][1]<=0:return None
    y=max(1,a[-1][0].year-a[0][0].year)
    return (a[-1][1]/a[0][1])**(1/y)-1

def clamp(v,lo,hi): return max(lo,min(hi,v))

def profile(des_sector,yahoo_sector,industry):
    s=des_sector or yahoo_sector or 'Umum'; x=(industry or '').lower()
    if s=='Infrastruktur' and any(k in x for k in ['construction','engineering','building']):return 'Infrastruktur · Konstruksi',{'DCF':1.05,'FCF Yield':.85,'Historical P/E':1.15,'Historical PBV':.45},'Kontraktor dinilai terutama dari laba dan arus kas proyek; PBV hanya pendukung.'
    if s=='Infrastruktur':return s,{'DCF':1.20,'FCF Yield':1.00,'Historical P/E':.85,'Historical PBV':.60},'DCF dan FCF mendapat bobot lebih besar untuk aset dan arus kas jangka panjang.'
    if s=='Properti & Real Estat':return s,{'DCF':.70,'FCF Yield':.55,'Historical P/E':.75,'Historical PBV':1.35},'Nilai aset dan ekuitas lebih penting pada developer properti.'
    if s=='Energi':return s,{'DCF':.65,'FCF Yield':1.10,'Historical P/E':.80,'Historical PBV':.55},'FCF dan laba historis lebih ditekankan karena laba sektor energi cenderung siklikal.'
    if s=='Barang Baku':return s,{'DCF':.70,'FCF Yield':1.05,'Historical P/E':.85,'Historical PBV':.65},'Arus kas dan laba ternormalisasi lebih penting pada bisnis bahan baku.'
    if s=='Perindustrian':return s,{'DCF':1,'FCF Yield':1,'Historical P/E':1,'Historical PBV':.65},'DCF, FCF dan P/E digunakan seimbang.'
    if s in ['Barang Konsumen Primer','Barang Konsumen Non-Primer']:return s,{'DCF':1,'FCF Yield':1,'Historical P/E':1.20,'Historical PBV':.50},'P/E, DCF dan FCF lebih relevan untuk bisnis konsumsi.'
    if s=='Kesehatan':return s,{'DCF':1,'FCF Yield':.90,'Historical P/E':1.15,'Historical PBV':.45},'P/E dan DCF menjadi acuan utama.'
    if s=='Keuangan' or any(k in x for k in ['bank','financial','insurance']):return 'Keuangan',{'DCF':.15,'FCF Yield':.10,'Historical P/E':.85,'Historical PBV':1.55},'PBV/ROE menjadi acuan utama; FCF konvensional kurang representatif.'
    if s=='Teknologi':return s,{'DCF':1.15,'FCF Yield':.85,'Historical P/E':1,'Historical PBV':.25},'Pertumbuhan dan arus kas lebih penting pada teknologi.'
    if s=='Transportasi & Logistik':return s,{'DCF':1.10,'FCF Yield':1.05,'Historical P/E':.90,'Historical PBV':.65},'DCF dan FCF diperkuat karena kebutuhan aset dan arus kas operasional.'
    return s,{'DCF':.90,'FCF Yield':.90,'Historical P/E':1,'Historical PBV':.65},'Bobot seimbang digunakan; sektor DES menjadi klasifikasi utama.'

def tech(h):
    c=h.Close.dropna(); last=float(c.iloc[-1]); ma=lambda p:n(c.rolling(p).mean().iloc[-1]) if len(c)>=p else None
    d=c.diff(); u=d.clip(lower=0).rolling(14).mean(); dn=(-d.clip(upper=0)).rolling(14).mean(); rs=u/dn.replace(0,np.nan)
    return {'ma20':ma(20),'ma50':ma(50),'ma200':ma(200),'rsi14':n((100-100/(1+rs)).iloc[-1]),'return1m':sd(last,c.iloc[-22])-1 if len(c)>=22 and sd(last,c.iloc[-22]) is not None else None,'return3m':sd(last,c.iloc[-66])-1 if len(c)>=66 and sd(last,c.iloc[-66]) is not None else None}

def history_years(h):
    if h is None or h.empty:return 0
    return max(0,(h.index.max()-h.index.min()).days/365.25)

def hist_multiple(h,annual,shares,current_ps,years,kind):
    # Do not invent a 3Y/5Y multiple for newly listed/spun-off shares.
    coverage=history_years(h)
    required=2.5 if years==3 else 4.5
    if coverage<required or not shares or not current_ps or current_ps<=0:return None
    hh=h[h.index>=h.index.max()-pd.DateOffset(years=years)]; vals=[]
    cap=100 if kind=='pe' else 20
    floor=.5 if kind=='pe' else .1
    for d,total in annual:
        ps=sd(total,shares)
        if not ps or ps<=0:continue
        px=hh[hh.index.year==d.year].Close
        if len(px):
            ratios=(px/ps).replace([np.inf,-np.inf],np.nan).dropna()
            vals += [float(v) for v in ratios if floor<=v<=cap]
    if len(vals)<30:return None
    a=np.array(vals,float); a=a[np.isfinite(a)]
    if len(a)<10:return None
    lo,hi=np.nanpercentile(a,[2,98]); a=a[(a>=lo)&(a<=hi)]
    if len(a)<10:return None
    mean=float(np.median(a)); std=float(np.std(a)); cur=sd(float(h.Close.iloc[-1]),current_ps)
    if cur is None or cur<floor or cur>cap:return None
    return {'mean':mean,'sd':std,'current':cur,'z':sd(cur-mean,std) if std>1e-12 else 0,'minus1':max(floor,mean-std)*current_ps,'base':mean*current_ps,'plus1':min(cap,mean+std)*current_ps,'coverageYears':coverage}

def analyze(sym):
    tk=sym if '.' in sym else sym+'.JK'; t=yf.Ticker(tk); info=t.info or {}; h=t.history(period='5y',auto_adjust=False)
    if h.empty:raise ValueError('price unavailable')
    price=n(h.Close.dropna().iloc[-1]); yahoo_sector=info.get('sector') or info.get('sectorDisp'); industry=info.get('industry') or info.get('industryDisp'); des_sector=SECTOR_BY_TICKER.get(sym.replace('.JK',''))
    sector_label,sw,sector_note=profile(des_sector,yahoo_sector,industry)
    inc=t.income_stmt; bs=t.balance_sheet; cf=t.cashflow; mcap=n(info.get('marketCap')); shares=n(info.get('sharesOutstanding') or info.get('impliedSharesOutstanding'))
    # Market-cap reconciliation protects against bad Yahoo per-share denominators after IPO/spin-off/corporate actions.
    shares_from_mcap=sd(mcap,price) if mcap and price else None
    share_warning=None
    if shares and shares_from_mcap:
        ratio=sd(shares,shares_from_mcap)
        if ratio is not None and (ratio<.67 or ratio>1.50):
            shares=shares_from_mcap; share_warning='Jumlah saham Yahoo tidak konsisten dengan market cap; denominator direkonsiliasi dari market cap/harga.'
    elif not shares: shares=shares_from_mcap
    ni=stmt(inc,['Net Income','Net Income Common Stockholders']); eq=stmt(bs,['Stockholders Equity','Total Stockholder Equity','Common Stock Equity'])
    eps_calc=sd(ni,shares); eps_info=n(info.get('trailingEps')); eps=eps_info if eps_info and eps_info>0 else eps_calc
    bvps_calc=sd(eq,shares); bvps_info=n(info.get('bookValue')); bvps=bvps_calc if bvps_calc and bvps_calc>0 else bvps_info
    roe=n(info.get('returnOnEquity')); beta=n(info.get('beta')) or 1.; ocf=stmt(cf,['Operating Cash Flow','Total Cash From Operating Activities']); capex=stmt(cf,['Capital Expenditure','Capital Expenditures']); fcf=n(info.get('freeCashflow'))
    if fcf is None and ocf is not None and capex is not None:fcf=ocf+capex if capex<0 else ocf-capex
    fcfps=sd(fcf,shares); nis=ser(inc,['Net Income','Net Income Common Stockholders']); revs=ser(inc,['Total Revenue']); fcfs=ser(cf,['Free Cash Flow']); eqs=ser(bs,['Stockholders Equity','Total Stockholder Equity','Common Stock Equity'])
    gs=[g for g in [cagr(nis),cagr(revs),cagr(fcfs)] if g is not None]; hg=float(np.median(gs)) if gs else .08; payout=n(info.get('payoutRatio')); sust=roe*(1-clamp(payout if payout is not None else .35,0,.9)) if roe is not None else None
    growth=clamp(float(np.median([hg,sust])) if sust is not None else hg,-.03,.18); ke=clamp(.065+beta*.0738,.105,.22); terminal=.035; methods=[]; dcfdiag=None; guards=[]
    if share_warning:guards.append(share_warning)
    coverage=history_years(h)
    if coverage<2.5:guards.append(f'Riwayat harga baru {coverage:.1f} tahun; Historical P/E 3Y/5Y dinonaktifkan.')
    elif coverage<4.5:guards.append(f'Riwayat harga {coverage:.1f} tahun; Historical 5Y dinonaktifkan.')
    currentPE=sd(price,eps) if eps and eps>0 else None; currentPBV=sd(price,bvps) if bvps and bvps>0 else None
    if currentPE is not None and not (.5<=currentPE<=100):guards.append('P/E per-share gagal sanity check; metode P/E historis dinonaktifkan.')
    if currentPBV is not None and not (.1<=currentPBV<=20):guards.append('P/BV per-share gagal sanity check; metode PBV historis dinonaktifkan.')
    def rel(name,base):
        key='Historical P/E' if name.startswith('Historical P/E') else 'Historical PBV' if name.startswith('Historical PBV') else name
        return base*sw.get(key,1)
    def add(name,bear,base,bull,quality,relevance,bands=None,warning=None,explain=''):
        vals=[n(bear),n(base),n(bull)]
        if all(v is not None and v>0 and v<price*100 for v in vals):methods.append({'name':name,'bear':vals[0],'base':vals[1],'bull':vals[2],'confidence':quality,'relevance':rel(name,relevance),'rawWeight':quality*rel(name,relevance),'bands':bands,'warning':warning,'explanation':explain})
    if fcfps and fcfps>0 and ke>terminal:
        def dcf(g,k):
            if k-terminal<=.01:return None,None
            f=fcfps;s=0
            for yr in range(1,6):f*=1+g;s+=f/(1+k)**yr
            tv=f*(1+terminal)/(k-terminal)/(1+k)**5;return s+tv,sd(tv,s+tv)
        b,tvb=dcf(max(-.02,growth-.05),min(.24,ke+.02)); base,tv=dcf(growth,ke); bu,tvu=dcf(min(.22,growth+.04),max(.095,ke-.015))
        if base:
            rr=.65 if tv and tv>.70 else .85; dcfdiag={'terminalValueShare':tv,'bearTerminalValueShare':tvb,'bullTerminalValueShare':tvu,'warning':bool(tv and tv>.70),'growth':growth,'costOfEquity':ke,'terminalGrowth':terminal}
            add('DCF',b,base,bu,.85,rr,warning='Porsi nilai jangka panjang tinggi' if tv and tv>.70 else None,explain='Estimasi nilai saham dari arus kas masa depan yang didiskontokan.')
        req=clamp(ke-growth*.20,.09,.18); add('FCF Yield',fcfps/.16,fcfps/req,fcfps/max(.08,req-.02),.75,.90,explain='Free cash flow per saham dibandingkan dengan required cash yield.')
    if currentPE is not None and .5<=currentPE<=100:
        for yrs in [3,5]:
            pe=hist_multiple(h,nis,shares,eps,yrs,'pe')
            if pe:add(f'Historical P/E {yrs}Y',pe['minus1'],pe['base'],pe['plus1'],.9,1.,pe,explain=f'EPS sekarang dikalikan median P/E historis {yrs} tahun yang lolos sanity check.')
    if currentPBV is not None and .1<=currentPBV<=20:
        pbv=hist_multiple(h,eqs,shares,bvps,5,'pbv')
        if pbv:add('Historical PBV 5Y',pbv['minus1'],pbv['base'],pbv['plus1'],.8,.45 if roe and roe>.25 else .7,pbv,'Bobot dikurangi karena ROE tinggi' if roe and roe>.25 else None,explain='BVPS sekarang dikalikan median P/BV historis 5 tahun yang lolos sanity check.')
    if not methods:raise ValueError('no usable valuation models')
    bases=[m['base'] for m in methods]; med=float(np.median(bases)); use=[m for m in methods if .30*med<=m['base']<=3*med]
    # A composite based on one surviving method is not a composite. Keep JSON but flag FV unavailable.
    sufficient=len(use)>=2
    tw=sum(m['rawWeight'] for m in use) if sufficient else 0
    for m in methods:
        m['included']=sufficient and m in use; m['normalizedWeight']=sd(m['rawWeight'],tw) if sufficient and m in use else 0
    if sufficient:
        comp=lambda k:sum(m[k]*m['normalizedWeight'] for m in use); bear,base,bull=comp('bear'),comp('base'),comp('bull'); avg=float(np.mean([m['base'] for m in use])); disp=sd(float(np.std([m['base'] for m in use])),avg) if len(use)>1 else None; agreement='HIGH' if disp is not None and disp<.18 else 'MEDIUM' if disp is not None and disp<.32 else 'LOW'
    else:
        bear=base=bull=disp=None; agreement='INSUFFICIENT'; guards.append('Harga wajar gabungan tidak diterbitkan karena kurang dari 2 metode independen lolos validasi.')
    cashconv=sd(fcf,ni) if ni and ni>0 else None; checks=[price,eps,bvps,roe,fcf,shares,mcap]; available=sum(v is not None for v in checks)+int(any(m['name']=='Historical P/E 3Y' for m in methods))+int(any(m['name']=='Historical P/E 5Y' for m in methods))+int(dcfdiag is not None); qs=round(available*10); ql='BAIK' if qs>=80 else 'CUKUP' if qs>=60 else 'TERBATAS'
    return {'ticker':tk,'name':info.get('longName') or info.get('shortName') or tk,'asOf':datetime.now(timezone.utc).isoformat(),'price':price,'companyProfile':{'sector':des_sector or sector_label,'valuationProfile':sector_label,'sourceSector':yahoo_sector,'industry':industry,'sectorNote':sector_note,'sectorSource':'OJK DES Periode I 2026' if des_sector else 'Yahoo Finance'},'fairValue':{'bear':bear,'base':base,'bull':bull,'dispersion':disp,'agreement':agreement,'available':sufficient},'methods':methods,'dcfDiagnostics':dcfdiag,'technical':tech(h),'quality':{'cashConversion':cashconv,'roe':roe,'dataScore':qs,'dataLabel':ql,'availableInputs':available,'totalInputs':10,'guards':guards,'historyYears':coverage,'validMethodCount':len(use) if sufficient else 0},'raw':{'epsTTM':eps,'bvps':bvps,'currentPE':currentPE,'currentPBV':currentPBV,'roe':roe,'fcf':fcf,'growthNormalized':growth,'costOfEquity':ke,'terminalGrowth':terminal,'marketCap':mcap,'shares':shares},'source':'Yahoo Finance via yfinance','universeSource':DES_SOURCE}

summary=[]; errors=[]
for s in TICKERS:
    try:
        d=analyze(s); json.dump(d,open(f'{OUT}/{s}.json','w'),ensure_ascii=False,indent=2,allow_nan=False)
        summary.append({'ticker':s,'sector':d['companyProfile']['sector'],'valuationProfile':d['companyProfile']['valuationProfile'],'price':d['price'],**d['fairValue'],'dataLabel':d['quality']['dataLabel'],'validMethods':d['quality']['validMethodCount']}); print('OK',s)
    except Exception as e:
        errors.append({'ticker':s,'sector':SECTOR_BY_TICKER.get(s),'error':str(e)}); print('ERR',s,e)
json.dump({'updatedAt':datetime.now(timezone.utc).isoformat(),'universeSource':DES_SOURCE,'count':len(summary),'requested':len(TICKERS),'stocks':summary,'errors':errors},open(f'{OUT}/summary.json','w'),ensure_ascii=False,indent=2,allow_nan=False)
