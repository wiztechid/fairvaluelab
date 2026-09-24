import json,math,statistics,re
from pathlib import Path
DATA=Path('data'); OUT=DATA/'sector_mos.json'
ELIGIBLE={'SIAP','REVIEW'}
MIN_MOS=10.0

def f(x):
 try:
  x=float(x);return x if math.isfinite(x) else None
 except:return None

def canon(t):
 return re.sub(r'\.JK$','',str(t or '').upper())

def peer_group(profile):
 p=profile or {}; vp=str(p.get('valuationProfile') or '').strip(); ind=str(p.get('industry') or '').strip(); src=str(p.get('sourceSector') or '').strip(); sec=str(p.get('sector') or '').strip()
 # Valuation economics first. Financials must not be grouped by DES administrative label.
 if vp.lower() in {'keuangan','financials','financial services'} or 'bank' in ind.lower() or 'financial' in src.lower():
  if 'bank' in ind.lower(): return 'Keuangan · Bank'
  return 'Keuangan'
 # Prefer industry when it is informative; fall back to valuation profile, then economic/DES sector.
 generic={'','n/a','unknown','other'}
 if ind.lower() not in generic:return (vp+' · '+ind) if vp and vp.lower()!=ind.lower() else ind
 if vp.lower() not in generic:return vp
 return src or sec or 'Lainnya'

def main():
 groups={}
 for p in DATA.glob('*.json'):
  if p.name in {'summary.json','sector_mos.json','news_raw.json','news_collector_status.json','ticker_aliases.json'}:continue
  try:d=json.load(open(p,encoding='utf-8'))
  except:continue
  if not isinstance(d,dict):continue
  t=canon(d.get('ticker'));price=f(d.get('price'));fv=d.get('fairValue') or {};base=f(fv.get('base'));prof=d.get('companyProfile') or {}
  if not t or not price or not base or price<=0 or base<=0 or not fv.get('available'):continue
  status=d.get('analysisStatus')
  if status not in ELIGIBLE:continue
  group=peer_group(prof);mos=(base-price)/base*100
  # Leaderboard is an opportunity shortlist: hide negative/thin discounts.
  if mos < MIN_MOS:continue
  q=d.get('quality') or {}
  row={'ticker':t,'name':d.get('name') or t,'peerGroup':group,'desSector':prof.get('sector'),'valuationProfile':prof.get('valuationProfile'),
       'sourceSector':prof.get('sourceSector'),'industry':prof.get('industry'),'price':price,'fairValueBase':base,'mos':round(mos,2),
       'analysisStatus':status,'confidence':q.get('valuationConfidence'),'dataScore':q.get('dataScore'),
       'reviewFlags':q.get('reviewFlags') or [],'asOf':d.get('asOf')}
  groups.setdefault(group,[]).append(row)
 out={}
 for group,rows in groups.items():
  rows.sort(key=lambda x:(x['mos'],x.get('confidence') or 0),reverse=True);top=rows[:10];vals=[x['mos'] for x in rows]
  out[group]={'peerGroup':group,'eligibleCount':len(rows),'medianMos':round(statistics.median(vals),2) if vals else None,'top10':top}
 json.dump({'method':'MoS=(FV Base-Price)/FV Base','grouping':'Valuation Peer Group: valuation profile / industry / economic sector; DES sector retained only as metadata/fallback.',
            'tickerPolicy':'Canonical IDX ticker without .JK suffix','eligibility':f'Full FV only: SIAP or REVIEW, MoS >= {MIN_MOS:.0f}%. INDIKATIF/REFERENSI/BELUM_DINILAI excluded.',
            'peerGroups':out},open(OUT,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
 print('PEER_MOS',len(out),'groups',sum(len(v['top10']) for v in out.values()),'ranked rows')
if __name__=='__main__':main()
