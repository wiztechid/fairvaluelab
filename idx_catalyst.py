import json,math
from pathlib import Path
from datetime import datetime,timezone,timedelta
DATA=Path('data');CAT=DATA/'catalysts';CAT.mkdir(parents=True,exist_ok=True);SRC=DATA/'idx_disclosures.json';DAYS=1096
CATEGORIES={
 'EARNINGS':['laporan keuangan','kinerja keuangan','laba bersih','pendapatan'],
 'INSIDER':['kepemilikan saham','perubahan kepemilikan','direksi','komisaris'],
 'CONTROLLER':['pengendali','pemegang saham utama','beneficial owner','pemilik manfaat'],
 'BUYBACK':['pembelian kembali','buyback'], 'RIGHTS':['hmetd','rights issue','hak memesan efek terlebih dahulu'],
 'DIVIDEND':['dividen','dividend'], 'MNA':['akuisisi','merger','penggabungan usaha','pengambilalihan'],
 'CAPEX_EXPANSION':['belanja modal','capex','ekspansi','pabrik baru','gerai baru'],
 'CONTRACT':['kontrak baru','perolehan kontrak','tender','pesanan baru'],
 'AFFILIATE':['transaksi afiliasi','benturan kepentingan'], 'MATERIAL':['informasi dan fakta material','fakta material'],
 'RUPS':['rups','rapat umum pemegang saham'], 'PUBLIC_EXPOSE':['public expose','paparan publik'],
 'DEBT_FINANCING':['obligasi','sukuk','utang','pinjaman','refinancing'],
 'SUSPENSION':['suspensi','penghentian sementara','uma','unusual market activity'],
 'LEGAL_REGULATORY':['gugatan','perkara','sanksi','regulasi','izin usaha'],
}
CAUSAL={
 'EARNINGS':'Revenue/margin → EPS & FCF → earnings power / DCF', 'CAPEX_EXPANSION':'Capex → kapasitas/revenue potensial → FCF & DCF',
 'CONTRACT':'Order/kontrak → revenue visibility → margin/EPS/FCF', 'DIVIDEND':'Distribusi kas → dividend yield; tidak otomatis mengubah enterprise value',
 'BUYBACK':'Shares outstanding ↓ → EPS/share & ownership concentration', 'RIGHTS':'Equity baru → cash/debt capacity + dilution → per-share value',
 'MNA':'Asset/business mix → revenue/margin/debt → FV setelah dampak terukur', 'DEBT_FINANCING':'Debt/cost of capital → interest expense/WACC → EPS/DCF',
 'CONTROLLER':'Control/ownership change → governance/capital allocation; FV hanya bila dampak fundamental terukur',
 'INSIDER':'Ownership behavior → confidence/flow context; bukan input FV langsung', 'AFFILIATE':'Related-party transaction → asset/cashflow/governance review',
 'LEGAL_REGULATORY':'Legal/regulatory event → operating/cash-flow risk if material','SUSPENSION':'Market-status/flow risk; bukan FV input langsung'
}
def classify(title):
 s=(title or '').lower();return [k for k,v in CATEGORIES.items() if any(x in s for x in v)] or ['OTHER']
def num(x):
 try:v=float(x);return v if math.isfinite(v) else None
 except:return None
def insider(r):
 side=str(r.get('side') or '').upper();pct=num(r.get('ownershipChangePct'));shares=num(r.get('sharesChanged'))
 if side not in ('BUY','SELL'):return {'direction':'UNKNOWN','score':0,'verified':False}
 mag=min(3,max(1,1+int(abs(pct or 0)>=.1)+int(abs(pct or 0)>=.5))) if pct is not None else (1 if shares is not None else 0)
 return {'direction':side,'score':mag if side=='BUY' else -mag,'verified':True}
def controller_profile(events):
 # Never infer a controller from largest-holder names or news prose. Only structured,
 # source-verified fields are accepted.
 candidates=[]
 for e in events:
  c=e.get('controller') or e.get('controllingShareholder');ubo=e.get('ultimateController') or e.get('beneficialOwner')
  if c and str(e.get('controllerVerification') or e.get('verification') or '').upper().startswith(('OFFICIAL','VERIFIED')):
   candidates.append({'controller':c,'ultimateController':ubo,'ownershipPct':num(e.get('controllerOwnershipPct')),'asOf':e.get('publishedAt'),'sourceUrl':e.get('sourceUrl'),'verification':'VERIFIED_SOURCE'})
 if not candidates:return {'status':'UNVERIFIED','controller':None,'ultimateController':None,'note':'Pengendali belum terverifikasi dari field sumber resmi; tidak diinferensikan dari pemegang saham terbesar.'}
 candidates.sort(key=lambda x:x.get('asOf') or '',reverse=True);x=candidates[0];x['status']='VERIFIED';return x
def main():
 try:rows=json.load(open(SRC,encoding='utf-8'))
 except:rows=[]
 cutoff=datetime.now(timezone.utc)-timedelta(days=DAYS);by={}
 for r in rows:
  if not isinstance(r,dict):continue
  try:
   if datetime.fromisoformat(r.get('publishedAt','')).astimezone(timezone.utc)<cutoff:continue
  except:continue
  t=str(r.get('ticker') or '').replace('.JK','').upper().strip()
  if not t:continue
  x=dict(r);x['categories']=classify(r.get('title'));x['causalLinks']=[CAUSAL[c] for c in x['categories'] if c in CAUSAL]
  if 'INSIDER' in x['categories']:x['insiderSignal']=insider(r)
  by.setdefault(t,[]).append(x)
 summary=[]
 for t,events in by.items():
  events.sort(key=lambda x:x.get('publishedAt') or '',reverse=True);ins=sum((e.get('insiderSignal') or {}).get('score',0) for e in events)
  ctrl=controller_profile(events);actions=sorted({c for e in events for c in e['categories'] if c!='OTHER'})
  payload={'ticker':t,'historyWindow':'ROLLING_3Y','updatedAt':datetime.now(timezone.utc).isoformat(),'source':'IDX verified disclosures','controllerProfile':ctrl,'events':events,'signals':{'insiderNetScore':ins,'insiderBuyingConfirmed':any((e.get('insiderSignal') or {}).get('direction')=='BUY' and (e.get('insiderSignal') or {}).get('verified') for e in events),'catalystTypes':actions},'policy':'Catalyst and controller context are separate from fair value. Controller identity is never inferred. Events affect FV only after measurable financial impact is verified.'}
  json.dump(payload,open(CAT/f'{t}.json','w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False)
  summary.append({'ticker':t,'events3Y':len(events),'controllerStatus':ctrl['status'],'controller':ctrl.get('controller'),'catalystTypes':actions})
 json.dump({'updatedAt':datetime.now(timezone.utc).isoformat(),'historyWindow':'ROLLING_3Y','count':len(summary),'stocks':summary},open(CAT/'summary.json','w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False)
 print('IDX_CATALYSTS_3Y',len(summary),'stocks from',len(rows),'records')
if __name__=='__main__':main()
