import json, math
from pathlib import Path
import numpy as np
DATA=Path('data')
def n(x):
    try:v=float(x);return v if math.isfinite(v) else None
    except:return None
def clamp(x,a,b):return max(a,min(b,x))
def add(d,name,family,bear,base,bull,confidence,relevance,explanation,warning=None,meta=None,independent=True):
    p=n(d.get('price'));vals=[n(bear),n(base),n(bull)]
    if not p or not all(v is not None and v>0 and .05*p<=v<=5*p for v in vals):
        d.setdefault('methodDiagnostics',[]).append({'name':name,'family':family,'status':'OUTLIER','reason':'Hasil sector model tidak lolos economic sanity guard 0.05x–5x harga.','inputs':meta or {}});return False
    d.setdefault('methods',[]).append({'name':name,'family':family,'bear':vals[0],'base':vals[1],'bull':vals[2],'confidence':confidence,'relevance':relevance,'rawWeight':confidence*relevance,'warning':warning,'explanation':explanation,'bands':meta,'included':False,'normalizedWeight':0,'qcStatus':'CANDIDATE','countsForIndependence':independent});return True
def sector_weights(sector,industry):
    s=(sector or '').lower();i=(industry or '').lower()
    if 'keuangan' in s or any(x in i for x in ['bank','insurance','financial']):return {'forward_pe':.85,'justified_pbv':1.35,'graham':.15,'ev':0,'dividend':1.15,'dcf':.15}
    if 'properti' in s or 'real estat' in s:return {'forward_pe':.55,'justified_pbv':1.35,'graham':.2,'ev':.65,'dividend':.7,'dcf':.55}
    if 'energi' in s or 'barang baku' in s or any(x in i for x in ['mining','coal','gold','metal','oil','gas']):return {'forward_pe':1.05,'justified_pbv':.65,'graham':.15,'ev':1.25,'dividend':.55,'dcf':.85}
    if 'teknologi' in s:return {'forward_pe':1.25,'justified_pbv':.25,'graham':.1,'ev':.85,'dividend':.25,'dcf':1.15}
    if 'konsumen' in s:return {'forward_pe':1.25,'justified_pbv':.55,'graham':.2,'ev':.9,'dividend':.85,'dcf':1.0}
    return {'forward_pe':1.05,'justified_pbv':.7,'graham':.2,'ev':1.0,'dividend':.65,'dcf':1.0}
def process(path):
    d=json.load(open(path,encoding='utf-8'));raw=d.get('raw') or {};p=n(d.get('price'));eps=n(raw.get('epsTTM'));bvps=n(raw.get('bvps'));roe=n(raw.get('roe'));ke=n(raw.get('costOfEquity'));g0=n(raw.get('growthNormalized'));cp=d.get('companyProfile') or {};sector=cp.get('sector');industry=cp.get('industry');w=sector_weights(sector,industry)
    if not p:return d
    generated=('Forward Earnings Power','Mid-Cycle Earnings','Justified PBV / ROE');d['methods']=[m for m in (d.get('methods') or []) if m.get('name') not in generated]
    for m in d['methods']:
        name=str(m.get('name',''))
        if name=='Graham Number':m['relevance']=w['graham'];m['rawWeight']=(n(m.get('confidence')) or .6)*w['graham'];m['countsForIndependence']=False;m['warning']='Cross-check konservatif; tidak dihitung sebagai keluarga independen.'
        elif name=='Historical EV/EBITDA':m['relevance']=w['ev'];m['rawWeight']=(n(m.get('confidence')) or .82)*w['ev']
        elif name=='Historical Dividend Yield':m['relevance']=w['dividend'];m['rawWeight']=(n(m.get('confidence')) or .68)*w['dividend']
        elif name=='DCF':m['relevance']=w['dcf'];m['rawWeight']=(n(m.get('confidence')) or .85)*w['dcf']
    pe_methods=[m for m in d['methods'] if str(m.get('name','')).startswith('Historical P/E') and n((m.get('bands') or {}).get('mean'))]
    if eps and eps>0 and pe_methods:
        g=clamp(g0 if g0 is not None else 0,-.10,.25);forward_eps=eps*(1+g*.65);pes=[n(m['bands']['mean']) for m in pe_methods];pe=float(np.median(pes));spread=max(pe*.12,float(np.std(pes)) if len(pes)>1 else 0);lo=max(.5,pe-spread);hi=min(500,pe+spread);high=pe>60
        add(d,'Forward Earnings Power','forward_earnings',forward_eps*lo,forward_eps*pe,forward_eps*hi,.76 if high else .86,w['forward_pe'],'Forward EPS memakai normalized sustainable growth dan adaptive historical P/E.','HIGH MULTIPLE · confidence diturunkan.' if high else None,{'forwardEPS':forward_eps,'growthUsed':g*.65,'historicalPE':pe},True)
    # Cyclical/short-history fallback: normalized earnings capitalized with a conservative mid-cycle P/E.
    # This is independent from book value/Graham and does not use current market price as the target.
    cyc=('energi' in (sector or '').lower() or 'barang baku' in (sector or '').lower() or any(x in (industry or '').lower() for x in ['coal','mining','gold','metal','oil','gas']))
    if eps and eps>0 and cyc and not pe_methods:
        g=clamp(g0 if g0 is not None else 0,-.15,.15);norm_eps=eps*(1+g*.35)
        # Commodity businesses get a deliberately broad 5x-9x through-cycle earnings band.
        lo,mid,hi=5.0,7.0,9.0
        add(d,'Mid-Cycle Earnings','earnings_midcycle',norm_eps*lo,norm_eps*mid,norm_eps*hi,.66,w['forward_pe'],'Fallback untuk emiten siklikal/riwayat listing pendek: EPS tervalidasi dinormalisasi secara konservatif lalu dikapitalisasi dengan rentang P/E through-cycle 5x–9x. Harga pasar hanya menjadi sanity guard, bukan anchor.', 'SHORT HISTORY · confidence moderat; validasi bertambah seiring histori laporan.',{'normalizedEPS':norm_eps,'growthAdjustment':g*.35,'peBand':[lo,mid,hi]},True)
    if bvps and bvps>0 and roe is not None and ke and ke>0:
        g=clamp(g0 if g0 is not None else 0,-.02,min(.08,ke-.035));den=ke-g
        if den>=.03 and roe>g:
            j=(roe-g)/den
            if .2<=j<=12:add(d,'Justified PBV / ROE','book_profitability',bvps*max(.2,j*.8),bvps*j,bvps*min(12,j*1.2),.78,w['justified_pbv'],'PBV wajar diturunkan dari ROE, normalized growth dan cost of equity.',None,{'justifiedPBV':j,'roe':roe,'growth':g,'costOfEquity':ke},True)
    d.setdefault('valuationPolicy',{})['sectorWeights']=w;d['valuationPolicy']['principle']='Sector-aware evidence weighting; market price is QC guard only, never valuation target.';d['engineVersion']='3.13-sector-midcycle';return d
for p in DATA.glob('*.json'):
    if p.name in ('summary.json','errors.json'):continue
    try:d=process(p);json.dump(d,open(p,'w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False)
    except Exception as e:print('SECTOR_MODEL_ERR',p.stem,e)
print('SECTOR_MODELS_DONE')