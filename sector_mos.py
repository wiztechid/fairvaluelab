import json,math
from pathlib import Path
DATA=Path('data'); OUT=DATA/'sector_mos.json'
ELIGIBLE={'SIAP','REVIEW'}
def f(x):
 try:
  x=float(x);return x if math.isfinite(x) else None
 except:return None
def main():
 sectors={}
 for p in DATA.glob('*.json'):
  if p.name in {'summary.json','sector_mos.json','news_raw.json','news_collector_status.json','ticker_aliases.json'}:continue
  try:d=json.load(open(p,encoding='utf-8'))
  except:continue
  t=d.get('ticker');price=f(d.get('price'));fv=d.get('fairValue') or {};base=f(fv.get('base'))
  sec=(d.get('companyProfile') or {}).get('sector') or 'Lainnya'
  if not t or not price or not base or price<=0 or base<=0 or not fv.get('available'):continue
  status=d.get('analysisStatus')
  if status not in ELIGIBLE:continue
  mos=(base-price)/base*100
  q=d.get('quality') or {}
  row={'ticker':t,'name':d.get('name') or t,'sector':sec,'industry':(d.get('companyProfile') or {}).get('industry'),
       'price':price,'fairValueBase':base,'mos':round(mos,2),'analysisStatus':status,
       'confidence':q.get('valuationConfidence'),'dataScore':q.get('dataScore'),
       'reviewFlags':q.get('reviewFlags') or [],'asOf':d.get('asOf')}
  sectors.setdefault(sec,[]).append(row)
 out={}
 for sec,rows in sectors.items():
  rows.sort(key=lambda x:(x['mos'],x.get('confidence') or 0),reverse=True)
  top=rows[:10]
  vals=sorted(x['mos'] for x in rows)
  median=vals[len(vals)//2] if vals else None
  out[sec]={'sector':sec,'eligibleCount':len(rows),'medianMos':round(median,2) if median is not None else None,'top10':top}
 json.dump({'method':'MoS=(FV Base-Price)/FV Base','eligibility':'Full FV only: SIAP or REVIEW. INDIKATIF/REFERENSI/BELUM_DINILAI excluded.',
            'sectors':out},open(OUT,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
 print('SECTOR_MOS',len(out),'sectors',sum(len(v['top10']) for v in out.values()),'ranked rows')
if __name__=='__main__':main()
