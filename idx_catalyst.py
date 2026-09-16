import json, re, math
from pathlib import Path
from datetime import datetime, timezone

DATA=Path('data'); CAT=DATA/'catalysts'; CAT.mkdir(parents=True,exist_ok=True)
# This module intentionally consumes normalized IDX disclosure records supplied by a collector/API.
# It does not scrape undocumented IDX endpoints. Raw records live in data/idx_disclosures.json.
SRC=DATA/'idx_disclosures.json'
CATEGORIES={
 'INSIDER':['kepemilikan saham','perubahan kepemilikan','direksi','komisaris'],
 'BUYBACK':['pembelian kembali','buyback','penarikan kembali saham'],
 'RIGHTS':['hak memesan efek terlebih dahulu','hmetd','rights issue'],
 'DIVIDEND':['dividen','dividend'],
 'MNA':['akuisisi','merger','penggabungan usaha','pengambilalihan'],
 'AFFILIATE':['transaksi afiliasi','benturan kepentingan'],
 'MATERIAL':['informasi dan fakta material','fakta material'],
 'RUPS':['rups','rapat umum pemegang saham'],
 'PUBLIC_EXPOSE':['public expose','paparan publik'],
 'DEBT_CAPITAL':['obligasi','sukuk','utang','pinjaman'],
 'SUSPENSION':['suspensi','penghentian sementara','uma','unusual market activity'],
 'FINANCIAL_REPORT':['laporan keuangan','financial statement'],
}
def classify(title):
 s=(title or '').lower()
 return [k for k,terms in CATEGORIES.items() if any(x in s for x in terms)] or ['OTHER']
def num(x):
 try:v=float(x);return v if math.isfinite(v) else None
 except:return None
def insider_signal(r):
 # Direction comes only from explicit normalized transaction fields, never inferred from title.
 side=str(r.get('side') or '').upper();shares=num(r.get('sharesChanged'));pct=num(r.get('ownershipChangePct'))
 if side not in ('BUY','SELL'):return {'direction':'UNKNOWN','score':0,'reason':'Arah transaksi belum terstruktur dari dokumen sumber.'}
 mag=0
 if pct is not None:mag=min(3,max(1,1+int(abs(pct)>=.1)+int(abs(pct)>=.5)))
 elif shares is not None:mag=1
 return {'direction':side,'score':mag if side=='BUY' else -mag,'reason':'Berdasarkan field transaksi terstruktur dari keterbukaan, bukan inferensi judul.'}
def main():
 try:rows=json.load(open(SRC,encoding='utf-8'))
 except:rows=[]
 by={}
 for r in rows:
  ticker=str(r.get('ticker') or '').replace('.JK','').upper().strip()
  if not ticker:continue
  cats=classify(r.get('title'));x=dict(r);x['categories']=cats
  if 'INSIDER' in cats:x['insiderSignal']=insider_signal(r)
  by.setdefault(ticker,[]).append(x)
 summary=[]
 for ticker,events in by.items():
  events=sorted(events,key=lambda x:x.get('publishedAt') or '',reverse=True)
  insider=sum((e.get('insiderSignal') or {}).get('score',0) for e in events)
  payload={'ticker':ticker,'updatedAt':datetime.now(timezone.utc).isoformat(),'source':'IDX normalized disclosures','events':events,'signals':{'insiderNetScore':insider,'insiderBuyingConfirmed':any((e.get('insiderSignal') or {}).get('direction')=='BUY' for e in events),'corporateActions':sorted({c for e in events for c in e['categories'] if c not in ('INSIDER','OTHER')})},'policy':'Catalyst metadata is separate from fair-value calculation. Insider/corporate-action events may alter catalyst/confidence only after document fields are verified.'}
  json.dump(payload,open(CAT/f'{ticker}.json','w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False)
  summary.append({'ticker':ticker,'events':len(events),'insiderNetScore':insider,'corporateActions':payload['signals']['corporateActions']})
 json.dump({'updatedAt':datetime.now(timezone.utc).isoformat(),'count':len(summary),'stocks':summary},open(CAT/'summary.json','w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False)
 print('IDX_CATALYSTS',len(summary),'from',len(rows),'records')
if __name__=='__main__':main()
