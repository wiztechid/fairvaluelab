from flask import Flask, request, jsonify, send_from_directory
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timezone

app = Flask(__name__, static_folder=".", static_url_path="")

def fnum(x):
    try:
        if x is None or pd.isna(x): return None
        return float(x)
    except: return None

def pick(info, *keys):
    for k in keys:
        v = info.get(k)
        if v is not None: return fnum(v)
    return None

def stmt_value(df, names, col=0):
    if df is None or df.empty: return None
    for n in names:
        if n in df.index:
            try: return fnum(df.loc[n].iloc[col])
            except: pass
    return None

def annual_series(df, names):
    if df is None or df.empty: return []
    for n in names:
        if n in df.index:
            vals=[]
            for d,v in df.loc[n].items():
                if pd.notna(v): vals.append((pd.Timestamp(d), float(v)))
            return sorted(vals)
    return []

def cap(x, lo, hi): return max(lo, min(hi, x))

def technical(hist):
    c=hist["Close"].dropna()
    if len(c)<30: return {}
    last=float(c.iloc[-1]); ma20=float(c.rolling(20).mean().iloc[-1]) if len(c)>=20 else None
    ma50=float(c.rolling(50).mean().iloc[-1]) if len(c)>=50 else None; ma200=float(c.rolling(200).mean().iloc[-1]) if len(c)>=200 else None
    d=c.diff(); up=d.clip(lower=0).rolling(14).mean(); dn=(-d.clip(upper=0)).rolling(14).mean(); rs=up/dn.replace(0,np.nan)
    rsi=float((100-100/(1+rs)).iloc[-1]) if pd.notna(rs.iloc[-1]) else None
    ema12=c.ewm(span=12,adjust=False).mean(); ema26=c.ewm(span=26,adjust=False).mean(); macd=ema12-ema26; sig=macd.ewm(span=9,adjust=False).mean()
    ret1m=(last/float(c.iloc[-22])-1) if len(c)>=22 else None; ret3m=(last/float(c.iloc[-66])-1) if len(c)>=66 else None
    low52=float(c.tail(252).min()); high52=float(c.tail(252).max()); pos52=(last-low52)/(high52-low52) if high52>low52 else None
    score=(20 if ma20 and last>ma20 else 0)+(25 if ma50 and last>ma50 else 0)+(20 if ma200 and last>ma200 else 0)+(20 if macd.iloc[-1]>sig.iloc[-1] else 0)+(15 if rsi and 50<=rsi<=70 else (8 if rsi and 40<=rsi<50 else 0))
    return dict(ma20=ma20,ma50=ma50,ma200=ma200,rsi14=rsi,macd=float(macd.iloc[-1]),macdSignal=float(sig.iloc[-1]),return1m=ret1m,return3m=ret3m,low52=low52,high52=high52,pos52=pos52,score=score)

def hist_multiple_fv(price_hist, annual_income, annual_bs, shares, current_eps, current_bvps):
    out={}
    if shares and shares>0 and current_eps and current_eps>0:
        eps_by_year={d.year:ni/shares for d,ni in annual_income}; pes=[]
        for y,eps in eps_by_year.items():
            if eps<=0: continue
            px=price_hist[price_hist.index.year==y]["Close"]
            if len(px): pes += list((px/eps).replace([np.inf,-np.inf],np.nan).dropna().values)
        if len(pes)>30:
            a=np.array(pes,float); a=a[(a>0)&(a<np.nanpercentile(a,99))]; mean=float(np.mean(a)); sd=float(np.std(a))
            out["pe"]={"mean":mean,"sd":sd,"minus1":max(0,mean-sd)*current_eps,"base":mean*current_eps,"plus1":(mean+sd)*current_eps}
    if shares and shares>0 and current_bvps and current_bvps>0:
        bv_by_year={d.year:eq/shares for d,eq in annual_bs}; pbvs=[]
        for y,bvps in bv_by_year.items():
            if bvps<=0: continue
            px=price_hist[price_hist.index.year==y]["Close"]
            if len(px): pbvs += list((px/bvps).replace([np.inf,-np.inf],np.nan).dropna().values)
        if len(pbvs)>30:
            a=np.array(pbvs,float); a=a[(a>0)&(a<np.nanpercentile(a,99))]; mean=float(np.mean(a)); sd=float(np.std(a))
            out["pbv"]={"mean":mean,"sd":sd,"minus1":max(0,mean-sd)*current_bvps,"base":mean*current_bvps,"plus1":(mean+sd)*current_bvps}
    return out

def reverse_dcf_growth(price, fcf_ps, ke, terminal=.04, years=5):
    if not fcf_ps or fcf_ps<=0 or price<=0 or ke<=terminal: return None
    def pv(g):
        s=0; f=fcf_ps
        for t in range(1,years+1): f*=1+g; s+=f/((1+ke)**t)
        return s+(f*(1+terminal)/(ke-terminal))/((1+ke)**years)
    lo,hi=-.30,.80
    if pv(lo)>price or pv(hi)<price: return None
    for _ in range(80):
        mid=(lo+hi)/2
        if pv(mid)<price: lo=mid
        else: hi=mid
    return (lo+hi)/2

@app.route("/")
def home(): return send_from_directory(".", "index.html")

@app.route("/api/analyze")
def analyze():
    raw=request.args.get("ticker","").upper().strip()
    if not raw: return jsonify({"error":"Ticker kosong"}),400
    ticker=raw if "." in raw else raw+".JK"
    try:
        t=yf.Ticker(ticker); info=t.info or {}; hist=t.history(period="5y", auto_adjust=False)
        if hist.empty: return jsonify({"error":"Harga tidak ditemukan untuk "+ticker}),404
        price=fnum(hist["Close"].dropna().iloc[-1])
        try:
            if getattr(t.fast_info,"last_price",None): price=float(t.fast_info.last_price)
        except: pass
        inc=t.income_stmt; bs=t.balance_sheet; cf=t.cashflow
        shares=pick(info,"sharesOutstanding","impliedSharesOutstanding"); marketcap=pick(info,"marketCap")
        if not shares and marketcap and price: shares=marketcap/price
        if not marketcap and shares and price: marketcap=shares*price
        eps=pick(info,"trailingEps"); netincome=stmt_value(inc,["Net Income","Net Income Common Stockholders"])
        if not eps and netincome and shares: eps=netincome/shares
        equity=stmt_value(bs,["Stockholders Equity","Total Stockholder Equity","Common Stock Equity"]); bvps=(equity/shares) if equity and shares else pick(info,"bookValue")
        roe=pick(info,"returnOnEquity"); beta=pick(info,"beta") or 1.0; debt=stmt_value(bs,["Total Debt"]) or pick(info,"totalDebt") or 0; cash=stmt_value(bs,["Cash Cash Equivalents And Short Term Investments","Cash And Cash Equivalents"]) or pick(info,"totalCash") or 0
        ebitda=stmt_value(inc,["EBITDA","Normalized EBITDA"]) or pick(info,"ebitda"); revenue=stmt_value(inc,["Total Revenue"]); ocf=stmt_value(cf,["Operating Cash Flow","Total Cash From Operating Activities"]); capex=stmt_value(cf,["Capital Expenditure","Capital Expenditures"]); fcf=pick(info,"freeCashflow")
        if not fcf and ocf is not None and capex is not None: fcf=ocf+capex if capex<0 else ocf-capex
        fcfps=(fcf/shares) if fcf and shares else None
        ni_ser=annual_series(inc,["Net Income","Net Income Common Stockholders"]); rev_ser=annual_series(inc,["Total Revenue"]); fcf_ser=annual_series(cf,["Free Cash Flow"])
        def cagr(series):
            if len(series)<3: return None
            old,new=series[0][1],series[-1][1]; n=max(1,series[-1][0].year-series[0][0].year)
            return (new/old)**(1/n)-1 if old>0 and new>0 else None
        gs=[x for x in [cagr(ni_ser),cagr(rev_ser),cagr(fcf_ser)] if x is not None and np.isfinite(x)]; hist_g=float(np.median(gs)) if gs else .08
        payout=pick(info,"payoutRatio"); sustainable=roe*(1-cap(payout if payout is not None else .35,0,.9)) if roe is not None else None
        growth=cap(float(np.median([hist_g,sustainable])) if sustainable is not None else hist_g,-.05,.25)
        rf=.065; erp=.0738; ke=cap(rf+beta*erp,.10,.22); terminal=.04; methods=[]
        if fcfps and fcfps>0 and ke>terminal:
            def dcf(g,k):
                ff=fcfps; s=0
                for yr in range(1,6): ff*=1+g; s+=ff/((1+k)**yr)
                return s+(ff*(1+terminal)/(k-terminal))/((1+k)**5)
            methods.append({"name":"DCF (FCF/share)","bear":dcf(max(-.03,growth-.05),min(.24,ke+.02)),"base":dcf(growth,ke),"bull":dcf(min(.30,growth+.05),max(.09,ke-.02)),"confidence":.9 if len(fcf_ser)>=3 else .65})
        if fcfps and fcfps>0:
            req=cap(ke-growth*.25,.08,.18); methods.append({"name":"FCF Yield","bear":fcfps/.16,"base":fcfps/req,"bull":fcfps/max(.07,req-.02),"confidence":.7})
        hm=hist_multiple_fv(hist,ni_ser,annual_series(bs,["Stockholders Equity","Total Stockholder Equity","Common Stock Equity"]),shares,eps,bvps)
        if "pe" in hm:
            h=hm["pe"]; methods.append({"name":"Historical P/E 5Y","bear":h["minus1"],"base":h["base"],"bull":h["plus1"],"confidence":.85,"detail":{"mean":h["mean"],"sd":h["sd"]}})
        if "pbv" in hm:
            h=hm["pbv"]; methods.append({"name":"Historical PBV 5Y","bear":h["minus1"],"base":h["base"],"bull":h["plus1"],"confidence":.8,"detail":{"mean":h["mean"],"sd":h["sd"]}})
        if bvps and bvps>0 and roe and ke>growth:
            jpbv=(roe-growth)/(ke-growth)
            if jpbv>0:
                b=bvps*jpbv; methods.append({"name":"Justified PBV","bear":b*.85,"base":b,"bull":b*1.15,"confidence":.75})
        bases=[m["base"] for m in methods if m["base"] and m["base"]>0]
        if not bases: return jsonify({"error":"Data fundamental tidak cukup untuk valuasi."}),422
        med=float(np.median(bases)); usable=[m for m in methods if .25*med<=m["base"]<=4*med]
        def comp(key):
            den=sum(m["confidence"] for m in usable); return sum(m[key]*m["confidence"] for m in usable)/den if den else None
        bear,base,bull=comp("bear"),comp("base"),comp("bull"); dispersion=float(np.std([m["base"] for m in usable])/np.mean([m["base"] for m in usable])) if len(usable)>1 else .5; completeness=min(1,len(usable)/5); confidence=round(100*max(0,min(1,.55*completeness+.45*(1-min(dispersion,1)))),0)
        for m in methods: m["upside"]=(m["base"]/price-1) if price else None; m["included"]=m in usable
        reverse=reverse_dcf_growth(price,fcfps,ke,terminal); ratio=price/base if base else None
        label="N/A" if ratio is None else "DEEP UNDERVALUED" if ratio<.70 else "UNDERVALUED" if ratio<.85 else "FAIR / WATCH" if ratio<=1.10 else "EXPENSIVE" if ratio<=1.30 else "VERY EXPENSIVE"
        rawdata={"price":price,"marketCap":marketcap,"shares":shares,"epsTTM":eps,"bookValuePerShare":bvps,"roe":roe,"beta":beta,"revenue":revenue,"netIncome":netincome,"fcf":fcf,"fcfPerShare":fcfps,"debt":debt,"cash":cash,"ebitda":ebitda,"growthNormalized":growth,"costOfEquity":ke,"terminalGrowth":terminal,"riskFreeAssumption":rf,"erpIndonesiaAssumption":erp}
        return jsonify({"ticker":ticker,"asOf":datetime.now(timezone.utc).isoformat(),"currency":info.get("currency","IDR"),"name":info.get("longName") or info.get("shortName") or ticker,"price":price,"fairValue":{"bear":bear,"base":base,"bull":bull,"upside":base/price-1,"label":label,"confidence":confidence,"dispersion":dispersion},"methods":methods,"reverseDCF":{"impliedGrowth":reverse},"technical":technical(hist),"raw":rawdata,"notes":["Yahoo Finance/yfinance market & statement data","Historical multiples reconstructed from Yahoo price + annual statements","Discount-rate assumptions are transparent; valuation is an estimate, not a guarantee."]})
    except Exception as e: return jsonify({"error":str(e)}),500

if __name__=="__main__": app.run(host="0.0.0.0",port=8000,debug=True)
