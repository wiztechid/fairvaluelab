import json
from pathlib import Path
from datetime import datetime, timezone
DATA=Path('data'); BT=DATA/'backtest'; CAT=DATA/'catalysts'
def dt(x):
 try:return datetime.fromisoformat(str(x).replace('Z','+00:00'))
 except:return None
def main():
 changed=0
 if not BT.exists():return
 for td in BT.iterdir():
  if not td.is_dir():continue
  cp=CAT/f'{td.name}.json'; events=[]
  if cp.exists():
   try:events=json.load(open(cp,encoding='utf-8')).get('events',[])
   except:events=[]
  for sp in td.glob('*.json'):
   try:s=json.load(open(sp,encoding='utf-8'))
   except:continue
   lock=dt(s.get('lockedAt'))
   if not lock:continue
   known=[]
   for e in events:
    pub=dt(e.get('publishedAt'))
    if pub and pub<=lock:known.append(e)
   insider=[e for e in known if 'INSIDER' in e.get('categories',[])]
   buy=sum(1 for e in insider if (e.get('insiderSignal') or {}).get('direction')=='BUY');sell=sum(1 for e in insider if (e.get('insiderSignal') or {}).get('direction')=='SELL')
   s['catalystAtLock']={'knownEventCount':len(known),'insiderBuyCount':buy,'insiderSellCount':sell,'insiderNetScore':sum((e.get('insiderSignal') or {}).get('score',0) for e in insider),'corporateActions':sorted({c for e in known for c in e.get('categories',[]) if c not in ('INSIDER','OTHER')}),'events':[{'publishedAt':e.get('publishedAt'),'title':e.get('title'),'categories':e.get('categories'),'insiderSignal':e.get('insiderSignal')} for e in known[-30:]],'pointInTime':True,'policy':'Only disclosures published on or before snapshot lock are included; later events cannot leak backward.'}
   json.dump(s,open(sp,'w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False);changed+=1
 print('CATALYST_SNAPSHOTS',changed)
if __name__=='__main__':main()