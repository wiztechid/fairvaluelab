import json,re,math,hashlib,unicodedata
from pathlib import Path
from datetime import datetime,timezone,timedelta

DATA=Path('data'); SRC=DATA/'news_raw.json'; OUT=DATA/'catalysts'; OUT.mkdir(parents=True,exist_ok=True); DAYS=7
CATEGORIES={
 'EARNINGS':['laporan keuangan','kinerja','laba','rugi bersih','pendapatan','revenue','ebitda'],
 'DIVIDEND':['dividen','dividend'],
 'BUYBACK':['buyback','pembelian kembali saham'],
 'RIGHTS':['rights issue','hmetd','hak memesan efek terlebih dahulu','private placement','penambahan modal tanpa hak memesan'],
 'MNA':['akuisisi','merger','pengambilalihan','divestasi','spin off'],
 'CAPEX_EXPANSION':['ekspansi','capex','belanja modal','pabrik','smelter','kapasitas produksi','gerai baru','proyek baru'],
 'CONTRACT':['kontrak','tender','order baru','pesanan','kerja sama','kerjasama'],
 'DEBT_FINANCING':['obligasi','sukuk','pinjaman','utang','refinancing','pendanaan'],
 'OWNERSHIP':['kepemilikan saham','pemegang saham','pengendali','insider','direksi membeli','direksi menjual'],
 'REGULATORY_LEGAL':['regulasi','izin','sanksi','gugatan','perkara','suspensi','suspension'],
 'RUPS':['rups','rapat umum pemegang saham'],
}
CAUSAL={
 'EARNINGS':'Kinerja → revenue/margin → EPS & FCF → earnings power / DCF',
 'DIVIDEND':'Distribusi kas → dividend yield; tidak otomatis mengubah enterprise value',
 'BUYBACK':'Saham beredar ↓ → EPS per saham/ownership → nilai per saham bila material',
 'RIGHTS':'Modal baru → kas/debt capacity + potensi dilusi → nilai per saham',
 'MNA':'Perubahan aset/bisnis → revenue/margin/debt → FV setelah dampak terukur',
 'CAPEX_EXPANSION':'Capex → kapasitas/revenue potensial; FCF jangka pendek dapat tertekan → DCF',
 'CONTRACT':'Kontrak/order → revenue visibility → margin/EPS/FCF',
 'DEBT_FINANCING':'Utang/pendanaan → interest expense & WACC → EPS/DCF',
 'OWNERSHIP':'Perubahan ownership/control → governance/capital allocation; bukan input FV langsung tanpa dampak terukur',
 'REGULATORY_LEGAL':'Regulasi/legal → operating/cash-flow risk bila material',
 'RUPS':'Keputusan RUPS → FV hanya berubah jika keputusan berdampak pada cash flow, modal, aset, atau saham beredar',
}
NOISE=['rekomendasi saham','saham pilihan','target harga','analisis teknikal','support resistance','resistance','foreign flow',
       'top gainers','top losers','saham cuan','saham hari ini','ihsg','broker summary','ramalan','prediksi harga']
STOP={'pt','tbk','persero','indonesia','saham','dan','yang','untuk','dari','dengan','akan','telah','di','ke','pada','rp','persen'}
def norm(s):
 s=unicodedata.normalize('NFKD',(s or '').lower());s=''.join(c for c in s if not unicodedata.combining(c))
 return re.sub(r'[^a-z0-9]+',' ',s).strip()
def classify(text):
 s=norm(text);return [k for k,terms in CATEGORIES.items() if any(norm(x) in s for x in terms)]
def relevant(r):
 text=norm((r.get('title') or '')+' '+(r.get('summary') or ''));t=norm(r.get('ticker'))
 cats=classify(text)
 if not cats:return False,cats,'NO_MATERIAL_CATEGORY'
 if any(norm(x) in text for x in NOISE) and not any(c in cats for c in ('DIVIDEND','BUYBACK','RIGHTS','MNA','EARNINGS')):return False,cats,'MARKET_COMMENTARY'
 # ticker must appear as a token, or the story must still contain a material category.
 tokens=set(text.split())
 if t not in tokens:return False,cats,'TICKER_NOT_EXPLICIT'
 return True,cats,'MATERIAL_TICKER_EVENT'
def fingerprint(r,cats):
 words=[w for w in norm(r.get('title')).split() if len(w)>2 and w not in STOP and w!=norm(r.get('ticker'))]
 # event signature intentionally ignores publisher and headline word order.
 core=' '.join(sorted(set(words))[:18])
 return hashlib.sha256((r.get('ticker','')+'|'+'|'.join(sorted(cats))+'|'+core).encode()).hexdigest()[:20]
def similar(a,b):
 A=set(norm(a).split())-STOP;B=set(norm(b).split())-STOP
 return len(A&B)/max(1,len(A|B))
def main():
 try:rows=json.load(open(SRC,encoding='utf-8'))
 except:rows=[]
 cutoff=datetime.now(timezone.utc)-timedelta(days=DAYS);by={}
 for r in rows:
  if not isinstance(r,dict):continue
  try:dt=datetime.fromisoformat(r.get('publishedAt','')).astimezone(timezone.utc)
  except:continue
  if dt<cutoff:continue
  ok,cats,reason=relevant(r)
  if not ok:continue
  x=dict(r);x['categories']=cats;x['causalLinks']=[CAUSAL[c] for c in cats if c in CAUSAL];x['relevanceGate']=reason;x['eventKey']=fingerprint(r,cats)
  by.setdefault(str(r.get('ticker') or '').upper(),[]).append(x)
 summary=[];published=set()
 for t,events in by.items():
  events.sort(key=lambda x:x.get('publishedAt',''),reverse=True);groups=[]
  for e in events:
   hit=None
   for g in groups:
    samecat=bool(set(e['categories'])&set(g[0]['categories']))
    close=abs((datetime.fromisoformat(e['publishedAt'])-datetime.fromisoformat(g[0]['publishedAt'])).total_seconds())<=3*86400
    if samecat and close and similar(e['title'],g[0]['title'])>=.42:hit=g;break
   if hit is None:groups.append([e])
   else:hit.append(e)
  out=[]
  for g in groups:
   primary=g[0];primary['corroboration']=[{'source':x.get('source'),'sourceUrl':x.get('sourceUrl'),'title':x.get('title')} for x in g[1:4]]
   primary['duplicateCount']=len(g)-1;out.append(primary)
  out=out[:12];published.add(t)
  payload={'ticker':t,'historyWindow':'ROLLING_7D','windowDays':DAYS,'updatedAt':datetime.now(timezone.utc).isoformat(),
           'sourcePolicy':'Public news discovery; material ticker events only; duplicate coverage collapsed into one event.',
           'events':out,'signals':{'eventCount':len(out),'catalystTypes':sorted({c for e in out for c in e['categories']})},
           'policy':'News is context, not an automatic fair-value input. FV changes only after measurable fundamental impact is verified.'}
  json.dump(payload,open(OUT/f'{t}.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
  summary.append({'ticker':t,'events7D':len(out),'catalystTypes':payload['signals']['catalystTypes']})
 # Remove stale per-ticker catalyst files so an old 3Y cache cannot masquerade as a current 7D result.
 for p in OUT.glob('*.json'):
  if p.name!='summary.json' and p.stem not in published:
   p.unlink()
 json.dump({'updatedAt':datetime.now(timezone.utc).isoformat(),'historyWindow':'ROLLING_7D','windowDays':DAYS,'count':len(summary),'stocks':summary},
           open(OUT/'summary.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
 print('CATALYST_7D',len(summary),'tickers',sum(x['events7D'] for x in summary),'deduped events')
if __name__=='__main__':main()
