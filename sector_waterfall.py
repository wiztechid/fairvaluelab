# v3.19 sector valuation waterfall: add defensible fallback families without anchoring values to market price.
import json, math
from pathlib import Path
import yfinance as yf
DATA=Path('data')
def n(x):
    try:
        v=float(x); return v if math.isfinite(v) else None
    except: return None
def row(df,names):
    if df is None or df.empty:return None
    for name in names:
        if name in df.index:
            try:return n(df.loc[name].iloc[0])
            except:pass
    return None
def add(d,name,family,bear,base,bull,confidence,relevance,explanation,meta=None,independent=True):
    vals=[n(bear),n(base),n(bull)]
    if not all(v is not None and v>0 for v in vals):
        d.setdefault('methodDiagnostics',[]).append({'name':name,'family':family,'status':'INVALID','reason':'Input fundamental tidak menghasilkan nilai positif lengkap.','inputs':meta or {}});return False
    d.setdefault('methods',[]).append({'name':name,'family':family,'bear':vals[0],'base':vals[1],'bull':vals[2],'confidence':confidence,'relevance':relevance,'rawWeight':confidence*relevance,'warning':None,'explanation':explanation,'bands':meta,'included':False,'normalizedWeight':0,'qcStatus':'CANDIDATE','countsForIndependence':independent})
    return True
def process(path):
    d=json.load(open(path,encoding='utf-8'))
    if not isinstance(d,dict) or not d.get('ticker') or not n(d.get('price')):return d
    raw=d.get('raw') or {}; cp=d.get('companyProfile') or {}; sector=(cp.get('sector') or '').lower(); industry=(cp.get('industry') or '').lower()
    eps=n(raw.get('epsTTM')); bvps=n(raw.get('bvps')); roe=n(raw.get('roe')); ke=n(raw.get('costOfEquity')); growth=n(raw.get('growthNormalized')); shares=n(raw.get('shares')); factor=n(raw.get('fxFactor')) or 1
    existing={m.get('name') for m in d.get('methods') or []}
    t=yf.Ticker(d['ticker']); inc=t.income_stmt; bs=t.balance_sheet
    revenue=row(inc,['Total Revenue','Operating Revenue']); ebit=row(inc,['EBIT','Operating Income']); debt=row(bs,['Total Debt']); cash=row(bs,['Cash Cash Equivalents And Short Term Investments','Cash And Cash Equivalents'])
    revenue=revenue*factor if revenue is not None else None; ebit=ebit*factor if ebit is not None else None; debt=debt*factor if debt is not None else 0; cash=cash*factor if cash is not None else 0
    netdebt=(debt or 0)-(cash or 0)
    financial=('keuangan' in sector or any(x in industry for x in ['bank','insurance','financial']))
    property=('properti' in sector or 'real estat' in sector or any(x in industry for x in ['real estate','property']))
    asset_heavy=property or any(x in sector for x in ['energi','barang baku','infrastruktur','transportasi']) or any(x in industry for x in ['mining','coal','metal','oil','gas','shipping'])
    # Earnings Power Value: conservative no-growth capitalization of sustainable positive earnings.
    if eps and eps>0 and ke and ke>0 and not financial and 'Earnings Power Value' not in existing:
        req=max(.10,min(.22,ke)); base=eps/req
        add(d,'Earnings Power Value','earnings_power',base*.78,base,base*1.22,.72,1.0,'No-growth earnings power: EPS tervalidasi dikapitalisasi dengan required return. Growth tidak dipakai sebagai pengerek nilai.',{'eps':eps,'requiredReturn':req})
    # EV/EBIT: useful for capital-intensive companies where depreciation matters.
    if ebit and ebit>0 and shares and shares>0 and not financial and 'EV / EBIT' not in existing:
        mult=(7,10,13) if asset_heavy else (9,12,15)
        vals=[(ebit*m-netdebt)/shares for m in mult]
        add(d,'EV / EBIT','enterprise_earnings',*vals,.70,1.0,'Operating earnings dikapitalisasi pada rentang EV/EBIT sektor lalu dikurangi net debt.',{'ebit':ebit,'netDebt':netdebt,'multipleBand':list(mult)})
    # EV/Sales is reference-grade for real operating revenue when earnings are absent/unstable.
    if revenue and revenue>0 and shares and shares>0 and not financial and (not eps or eps<=0) and 'EV / Sales' not in existing:
        mult=(.45,.75,1.10) if asset_heavy else (.70,1.10,1.60)
        vals=[(revenue*m-netdebt)/shares for m in mult]
        add(d,'EV / Sales','revenue',*vals,.52,.65,'Fallback revenue valuation untuk bisnis dengan laba belum defensible; confidence sengaja dibatasi.',{'revenue':revenue,'netDebt':netdebt,'multipleBand':list(mult)})
    # Residual income: particularly suitable for financials/book-value businesses.
    if financial and bvps and bvps>0 and roe is not None and ke and ke>0 and 'Residual Income' not in existing:
        g=max(-.01,min(.05,growth if growth is not None else .02)); den=max(.04,ke-g); excess=roe-ke
        base=bvps + bvps*excess/den
        if base>0:add(d,'Residual Income','residual_income',max(bvps*.55,base*.78),base,base*1.22,.80,1.25,'Book value ditambah present value excess return (ROE di atas/bawah cost of equity).',{'bvps':bvps,'roe':roe,'costOfEquity':ke,'growth':g})
    # Adjusted book-value floor: reference only, never an independent full-FV family.
    if asset_heavy and bvps and bvps>0 and 'Adjusted Asset Floor' not in existing:
        add(d,'Adjusted Asset Floor','asset_floor',bvps*.55,bvps*.75,bvps*.95,.45,.45,'Konservatif: haircut terhadap book value sebagai asset floor; bukan RNAV dan tidak dihitung sebagai bukti independen.',{'bvps':bvps,'haircut':[.55,.75,.95]},False)
    d.setdefault('valuationPolicy',{})['waterfallVersion']='3.19-sector-waterfall'
    d['valuationPolicy']['marketAnchorPolicy']='Market price is not a valuation target. Distance to market is reviewed only after fundamental model construction.'
    d['engineVersion']='3.19-sector-waterfall'
    return d
for p in DATA.glob('*.json'):
    if p.name in ('summary.json','errors.json','idx_disclosures.json','idx_collector_status.json'):continue
    try:
        d=process(p);json.dump(d,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False)
    except Exception as e:print('WATERFALL_ERR',p.stem,e)
print('SECTOR_WATERFALL_DONE')
