import json, math, os
from pathlib import Path
import numpy as np
import pandas as pd
import yfinance as yf

DATA=Path('data')

def num(x):
    try:
        v=float(x); return v if math.isfinite(v) else None
    except:return None

def row(df,names):
    if df is None or df.empty:return None
    for name in names:
        if name in df.index:
            try:return num(df.loc[name].iloc[0])
            except:pass
    return None

def annual(df,names):
    if df is None or df.empty:return []
    for name in names:
        if name in df.index:
            out=[]
            for d,v in df.loc[name].items():
                v=num(v)
                if v is not None:out.append((pd.Timestamp(d),v))
            return sorted(out)
    return []

def add_method(d,name,family,bear,base,bull,confidence,relevance,explanation,bands=None):
    price=num(d.get('price'))
    vals=[num(bear),num(base),num(bull)]
    if not price or not all(v is not None and .05*price<=v<=5*price for v in vals):
        d.setdefault('quality',{}).setdefault('guards',[]).append(f'{name} ditolak: hasil di luar economic sanity guard.')
        return False
    d.setdefault('methods',[]).append({'name':name,'family':family,'bear':vals[0],'base':vals[1],'bull':vals[2],'confidence':confidence,'relevance':relevance,'rawWeight':confidence*relevance,'bands':bands,'warning':None,'explanation':explanation,'included':False,'normalizedWeight':0})
    return True

def robust_bands(vals,floor=.1,cap=40):
    a=np.array([x for x in vals if x is not None and floor<=x<=cap],float)
    if len(a)<3:return None
    med=float(np.median(a)); mad=float(np.median(np.abs(a-med))); sig=1.4826*mad
    if sig<=1e-9:sig=max(.10*med,.1)
    return max(floor,med-sig),med,min(cap,med+sig),sig

def rebuild(d):
    price=num(d.get('price')); methods=d.get('methods') or []
    eligible=[]
    for m in methods:
        vals=[num(m.get(k)) for k in ('bear','base','bull')]
        ok=price and all(v is not None and .05*price<=v<=5*price for v in vals)
        if ok:eligible.append(m)
        else:
            m['included']=False;m['normalizedWeight']=0;m['qcStatus']='OUTLIER'
    if not eligible:
        sufficient=False; use=[]
    else:
        logs=np.log([m['base'] for m in eligible]); med=float(np.median(logs)); mad=float(np.median(np.abs(logs-med)))
        use=[]
        for m,z in zip(eligible,logs):
            ratio=max(m['base']/price,price/m['base'])
            robust=True if len(eligible)<3 or mad<1e-9 else abs(z-med)<=3.5*1.4826*mad
            if robust and ratio<=5:use.append(m)
            else:m['qcStatus']='OUTLIER';m['included']=False;m['normalizedWeight']=0
        families={m.get('family') for m in use}
        sufficient=len(use)>=2 and len(families)>=2
    if sufficient:
        tw=sum(max(num(m.get('rawWeight')) or 0,.01) for m in use)
        for m in methods:
            m['included']=m in use;m['normalizedWeight']=(max(num(m.get('rawWeight')) or 0,.01)/tw if m in use else 0);m['qcStatus']='INCLUDED' if m in use else m.get('qcStatus','EXCLUDED')
        comp=lambda k:sum(m[k]*m['normalizedWeight'] for m in use)
        bear,base,bull=comp('bear'),comp('base'),comp('bull'); a=np.array([m['base'] for m in use]); disp=float(np.std(a)/np.mean(a)) if np.mean(a) else None
        agreement='HIGH' if disp is not None and disp<.18 else 'MEDIUM' if disp is not None and disp<.32 else 'LOW'
    else:
        bear=base=bull=disp=None;agreement='INSUFFICIENT'
        for m in methods:m['included']=False;m['normalizedWeight']=0
    d['fairValue']={'bear':bear,'base':base,'bull':bull,'dispersion':disp,'agreement':agreement,'available':bool(sufficient)}
    q=d.setdefault('quality',{});q['validMethodCount']=len(use) if sufficient else 0;q['independentFamilies']=len({m.get('family') for m in use}) if sufficient else 0
    if not sufficient:q.setdefault('guards',[]).append('Composite FV belum diterbitkan: minimal 2 keluarga valuasi independen setelah QC.')

def augment(path):
    d=json.load(open(path,encoding='utf-8'))
    # Only spend extra Yahoo calls where coverage is still weak.
    if d.get('fairValue',{}).get('available') and len(d.get('methods') or [])>=4:return False
    ticker=d.get('ticker') or (path.stem+'.JK'); price=num(d.get('price')); raw=d.get('raw') or {}; shares=num(raw.get('shares')); mcap=num(raw.get('marketCap'))
    if not price or not shares:return False
    t=yf.Ticker(ticker); info=t.info or {}; inc=t.income_stmt; bs=t.balance_sheet
    sector=(d.get('companyProfile') or {}).get('sector') or ''
    changed=False
    existing={m.get('name') for m in d.get('methods') or []}

    # 1) Historical EV/EBITDA. EV = equity value + debt - cash; translate target EV back to equity/share.
    if 'Historical EV/EBITDA' not in existing and 'Keuangan' not in sector:
        debt=row(bs,['Total Debt']); cash=row(bs,['Cash Cash Equivalents And Short Term Investments','Cash And Cash Equivalents','Cash Financial']); netdebt=(debt or 0)-(cash or 0)
        ebitdas=annual(inc,['EBITDA','Normalized EBITDA'])
        try:h=t.history(period='5y',auto_adjust=False)
        except:h=pd.DataFrame()
        mult=[]
        if not h.empty:
            for dt,eb in ebitdas:
                if eb<=0:continue
                px=h[h.index.year==dt.year].Close.dropna()
                if len(px):
                    # current net debt is an approximation; wide QC prevents false precision
                    mult.extend([((float(p)*shares+netdebt)/eb) for p in px.iloc[::max(1,len(px)//24)] if .5<=((float(p)*shares+netdebt)/eb)<=30])
        b=robust_bands(mult,.5,30)
        eb=row(inc,['EBITDA','Normalized EBITDA'])
        if b and eb and eb>0:
            lo,med,hi,sig=b
            fv=lambda x:(x*eb-netdebt)/shares
            changed|=add_method(d,'Historical EV/EBITDA','enterprise',fv(lo),fv(med),fv(hi),.82,1.0,'Enterprise value berbasis median EV/EBITDA historis; net debt dikembalikan ke equity value.',{'mean':med,'sd':sig,'minus1':lo,'base':med,'plus1':hi})

    # 2) Graham Number as conservative cross-check, only from EPS/BVPS already validated by core engine.
    eps=num(raw.get('epsTTM')); bvps=num(raw.get('bvps'))
    if 'Graham Number' not in existing and eps and eps>0 and bvps and bvps>0:
        g=math.sqrt(22.5*eps*bvps)
        changed|=add_method(d,'Graham Number','fundamental',g*.80,g,g*1.20,.60,.55,'Cross-check konservatif berbasis EPS dan BVPS tervalidasi; bobot sengaja rendah.')

    # 3) Historical dividend-yield model for established dividend payers.
    if 'Historical Dividend Yield' not in existing:
        try:
            div=t.dividends
            if div is not None and len(div)>=3:
                cutoff=div.index.max()-pd.DateOffset(years=5); div=div[div.index>=cutoff]
                annual_div=div.groupby(div.index.year).sum(); annual_div=annual_div[annual_div>0]
                try:h=t.history(period='5y',auto_adjust=False)
                except:h=pd.DataFrame()
                yields=[]
                for y,dps in annual_div.items():
                    px=h[h.index.year==y].Close.dropna()
                    if len(px):
                        mid=float(px.median()); yy=float(dps)/mid if mid>0 else 0
                        if .005<=yy<=.20:yields.append(yy)
                if len(yields)>=3:
                    ymed=float(np.median(yields)); ymad=float(np.median(np.abs(np.array(yields)-ymed))); ysig=max(1.4826*ymad,.001)
                    dps=float(annual_div.iloc[-1]); # lower required yield => higher FV
                    bear=dps/min(.25,ymed+ysig); base=dps/ymed; bull=dps/max(.005,ymed-ysig)
                    changed|=add_method(d,'Historical Dividend Yield','income',bear,base,bull,.68,.65,'Dividend per saham terbaru dinilai terhadap median dividend yield historis 5 tahun.',{'mean':ymed,'sd':ysig})
        except Exception as e:d.setdefault('quality',{}).setdefault('guards',[]).append('Dividend model dilewati: '+str(e)[:90])
    if changed:
        rebuild(d); d['engineVersion']='3.5-multimodel'; json.dump(d,open(path,'w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False)
    return changed

changed=0;failed=0
for p in DATA.glob('*.json'):
    if p.name in ('summary.json','errors.json'):continue
    try:changed+=1 if augment(p) else 0
    except Exception as e:failed+=1;print('AUGMENT_ERR',p.stem,e)
print('AUGMENT_DONE changed=',changed,'failed=',failed)
