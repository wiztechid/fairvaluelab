import json, math
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

def explain_skip(d,name,family,reason,inputs=None,status='NOT_APPLICABLE'):
    d.setdefault('methodDiagnostics',[]).append({'name':name,'family':family,'status':status,'reason':reason,'inputs':inputs or {}})

def add_method(d,name,family,bear,base,bull,confidence,relevance,explanation,bands=None):
    price=num(d.get('price')); vals=[num(bear),num(base),num(bull)]
    if not price or not all(v is not None for v in vals):
        explain_skip(d,name,family,'Input/model tidak menghasilkan nilai numerik yang lengkap.',{'bear':vals[0],'base':vals[1],'bull':vals[2]},'INVALID')
        return False
    if not all(v>0 for v in vals):
        explain_skip(d,name,family,'Hasil valuasi nol/negatif. Nilai dicatat sebagai diagnostik tetapi tidak layak masuk Composite FV.',{'bear':vals[0],'base':vals[1],'bull':vals[2]},'NEGATIVE')
        return False
    if not all(.05*price<=v<=5*price for v in vals):
        explain_skip(d,name,family,'Hasil berada di luar economic sanity guard 0,05x–5x harga pasar; diklasifikasikan extreme/outlier dan tidak masuk Composite FV.',{'bear':vals[0],'base':vals[1],'bull':vals[2],'price':price},'OUTLIER')
        return False
    d.setdefault('methods',[]).append({'name':name,'family':family,'bear':vals[0],'base':vals[1],'bull':vals[2],'confidence':confidence,'relevance':relevance,'rawWeight':confidence*relevance,'bands':bands,'warning':None,'explanation':explanation,'included':False,'normalizedWeight':0,'qcStatus':'CANDIDATE'})
    return True

def robust_bands(vals,floor=.1,cap=40):
    a=np.array([x for x in vals if x is not None and floor<=x<=cap],float)
    if len(a)<3:return None
    med=float(np.median(a)); mad=float(np.median(np.abs(a-med))); sig=1.4826*mad
    if sig<=1e-9:sig=max(.10*med,.1)
    return max(floor,med-sig),med,min(cap,med+sig),sig

def rebuild(d):
    price=num(d.get('price')); methods=d.get('methods') or []; eligible=[]
    for m in methods:
        vals=[num(m.get(k)) for k in ('bear','base','bull')]
        ok=price and all(v is not None and v>0 and .05*price<=v<=5*price for v in vals)
        if ok:eligible.append(m)
        else:
            m['included']=False;m['normalizedWeight']=0;m['qcStatus']='OUTLIER'
            explain_skip(d,m.get('name','Unknown'),m.get('family'),'Metode ditolak saat final QC karena nilai negatif/tidak valid/di luar skala harga.',{'bear':vals[0],'base':vals[1],'bull':vals[2],'price':price},'OUTLIER')
    if not eligible:sufficient=False;use=[]
    else:
        logs=np.log([m['base'] for m in eligible]); med=float(np.median(logs)); mad=float(np.median(np.abs(logs-med))); use=[]
        for m,z in zip(eligible,logs):
            ratio=max(m['base']/price,price/m['base']); robust=True if len(eligible)<3 or mad<1e-9 else abs(z-med)<=3.5*1.4826*mad
            if robust and ratio<=5:use.append(m)
            else:
                m['qcStatus']='OUTLIER';m['included']=False;m['normalizedWeight']=0
                explain_skip(d,m.get('name','Unknown'),m.get('family'),'Nilai berbeda ekstrem dari kelompok metode valid sehingga dikeluarkan dari Composite FV.',{'base':m.get('base'),'price':price},'OUTLIER')
        families={m.get('family') for m in use}; sufficient=len(use)>=2 and len(families)>=2
    if sufficient:
        tw=sum(max(num(m.get('rawWeight')) or 0,.01) for m in use)
        for m in methods:
            m['included']=m in use;m['normalizedWeight']=(max(num(m.get('rawWeight')) or 0,.01)/tw if m in use else 0);m['qcStatus']='INCLUDED' if m in use else m.get('qcStatus','EXCLUDED')
        comp=lambda k:sum(m[k]*m['normalizedWeight'] for m in use); bear,base,bull=comp('bear'),comp('base'),comp('bull'); a=np.array([m['base'] for m in use]); disp=float(np.std(a)/np.mean(a)) if np.mean(a) else None; agreement='HIGH' if disp is not None and disp<.18 else 'MEDIUM' if disp is not None and disp<.32 else 'LOW'
    else:
        bear=base=bull=disp=None;agreement='INSUFFICIENT'
        for m in methods:m['included']=False;m['normalizedWeight']=0
    d['fairValue']={'bear':bear,'base':base,'bull':bull,'dispersion':disp,'agreement':agreement,'available':bool(sufficient)}
    q=d.setdefault('quality',{});q['validMethodCount']=len(use);q['independentFamilies']=len({m.get('family') for m in use});q['diagnosticCount']=len(d.get('methodDiagnostics') or [])
    d['analysisStatus']='SIAP' if sufficient else 'TERBATAS'
    if not sufficient:q.setdefault('guards',[]).append('Composite FV belum diterbitkan: minimal 2 keluarga valuasi independen setelah QC.')

def augment(path):
    d=json.load(open(path,encoding='utf-8')); d['methodDiagnostics']=[]
    ticker=d.get('ticker') or (path.stem+'.JK'); price=num(d.get('price')); raw=d.get('raw') or {}; shares=num(raw.get('shares'))
    if not price or not shares:
        explain_skip(d,'All fallback models','data','Harga atau jumlah saham tidak tersedia.','', 'INVALID'); d['analysisStatus']='TERBATAS'; json.dump(d,open(path,'w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False); return True
    t=yf.Ticker(ticker); inc=t.income_stmt; bs=t.balance_sheet; sector=(d.get('companyProfile') or {}).get('sector') or ''; changed=False; existing={m.get('name') for m in d.get('methods') or []}
    eps=num(raw.get('epsTTM')); bvps=num(raw.get('bvps')); fcf=num(raw.get('fcf'))
    if eps is None:explain_skip(d,'P/E & Graham','earnings','EPS tidak tersedia/tervalidasi.')
    elif eps<=0:explain_skip(d,'P/E & Graham','earnings','EPS/laba bersih negatif; metode berbasis P/E dan Graham tidak bermakna.',{'eps':eps},'NEGATIVE')
    if bvps is None:explain_skip(d,'PBV & Graham','book','BVPS tidak tersedia/tervalidasi.')
    elif bvps<=0:explain_skip(d,'PBV & Graham','book','Ekuitas/BVPS negatif; metode berbasis book value tidak digunakan.',{'bvps':bvps},'NEGATIVE')
    if fcf is None:explain_skip(d,'DCF & FCF Yield','cashflow','FCF tidak tersedia/tervalidasi.')
    elif fcf<=0:explain_skip(d,'DCF & FCF Yield','cashflow','Free cash flow negatif; DCF berbasis FCF dan FCF Yield dilewati, metode lain tetap dihitung.',{'fcf':fcf},'NEGATIVE')
    if 'Historical EV/EBITDA' not in existing and 'Keuangan' not in sector:
        debt=row(bs,['Total Debt']); cash=row(bs,['Cash Cash Equivalents And Short Term Investments','Cash And Cash Equivalents','Cash Financial']); netdebt=(debt or 0)-(cash or 0); ebitdas=annual(inc,['EBITDA','Normalized EBITDA']); eb=row(inc,['EBITDA','Normalized EBITDA'])
        if eb is None:explain_skip(d,'Historical EV/EBITDA','enterprise','EBITDA tidak tersedia.')
        elif eb<=0:explain_skip(d,'Historical EV/EBITDA','enterprise','EBITDA negatif/nol; EV/EBITDA tidak digunakan.',{'ebitda':eb},'NEGATIVE')
        else:
            try:h=t.history(period='5y',auto_adjust=False)
            except:h=pd.DataFrame()
            mult=[]
            if not h.empty:
                for dt,e in ebitdas:
                    if e<=0:continue
                    px=h[h.index.year==dt.year].Close.dropna()
                    if len(px):mult.extend([((float(p)*shares+netdebt)/e) for p in px.iloc[::max(1,len(px)//24)] if .5<=((float(p)*shares+netdebt)/e)<=30])
            b=robust_bands(mult,.5,30)
            if b:
                lo,med,hi,sig=b; fv=lambda x:(x*eb-netdebt)/shares; changed|=add_method(d,'Historical EV/EBITDA','enterprise',fv(lo),fv(med),fv(hi),.82,1.0,'Enterprise value berbasis median EV/EBITDA historis; net debt dikembalikan ke equity value.',{'mean':med,'sd':sig,'minus1':lo,'base':med,'plus1':hi})
            else:explain_skip(d,'Historical EV/EBITDA','enterprise','Riwayat EV/EBITDA valid belum cukup untuk membentuk rentang valuasi.')
    if 'Graham Number' not in existing:
        if eps and eps>0 and bvps and bvps>0:
            g=math.sqrt(22.5*eps*bvps); changed|=add_method(d,'Graham Number','fundamental',g*.80,g,g*1.20,.60,.55,'Cross-check konservatif berbasis EPS dan BVPS tervalidasi; bobot sengaja rendah.')
    if 'Historical Dividend Yield' not in existing:
        try:
            div=t.dividends
            if div is None or len(div)<3:explain_skip(d,'Historical Dividend Yield','income','Riwayat pembayaran dividen belum cukup.')
            else:
                cutoff=div.index.max()-pd.DateOffset(years=5); div=div[div.index>=cutoff]; annual_div=div.groupby(div.index.year).sum(); annual_div=annual_div[annual_div>0]; h=t.history(period='5y',auto_adjust=False); yields=[]
                for y,dps in annual_div.items():
                    px=h[h.index.year==y].Close.dropna()
                    if len(px):
                        yy=float(dps)/float(px.median())
                        if .005<=yy<=.20:yields.append(yy)
                if len(yields)>=3:
                    ymed=float(np.median(yields)); ymad=float(np.median(np.abs(np.array(yields)-ymed))); ysig=max(1.4826*ymad,.001); dps=float(annual_div.iloc[-1]); changed|=add_method(d,'Historical Dividend Yield','income',dps/min(.25,ymed+ysig),dps/ymed,dps/max(.005,ymed-ysig),.68,.65,'Dividend per saham terbaru dinilai terhadap median dividend yield historis 5 tahun.',{'mean':ymed,'sd':ysig})
                else:explain_skip(d,'Historical Dividend Yield','income','Riwayat dividend yield valid kurang dari 3 periode.')
        except Exception as e:explain_skip(d,'Historical Dividend Yield','income','Model dividen gagal diproses: '+str(e)[:90],status='INVALID')
    rebuild(d); d['engineVersion']='3.6-transparent-negative-qc'; json.dump(d,open(path,'w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False); return True

changed=0;failed=0
for p in DATA.glob('*.json'):
    if p.name in ('summary.json','errors.json'):continue
    try:changed+=1 if augment(p) else 0
    except Exception as e:failed+=1;print('AUGMENT_ERR',p.stem,e)
print('AUGMENT_DONE changed=',changed,'failed=',failed)
