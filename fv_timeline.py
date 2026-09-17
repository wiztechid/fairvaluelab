import json, math
from pathlib import Path
from datetime import datetime, timezone
DATA=Path('data'); BT=DATA/'backtest'; OUT=DATA/'timeline'; OUT.mkdir(parents=True,exist_ok=True)
def n(x):
 try:v=float(x);return v if math.isfinite(v) else None
 except:return None
def pct(a,b): return (b/a-1) if a and b is not None else None
def method_map(s): return {m.get('name'):m for m in (s.get('methods') or []) if m.get('name')}
def attribution(prev,cur):
 pm,cm=method_map(prev),method_map(cur); names=sorted(set(pm)|set(cm)); rows=[]
 for name in names:
  a=n((pm.get(name) or {}).get('base'));b=n((cm.get(name) or {}).get('base'))
  wa=n((pm.get(name) or {}).get('weight'));wb=n((cm.get(name) or {}).get('weight'))
  rows.append({'method':name,'previousBase':a,'currentBase':b,'changePct':pct(a,b),'previousWeight':wa,'currentWeight':wb,'state':'ADDED' if name not in pm else 'REMOVED' if name not in cm else 'CONTINUED'})
 q0=prev.get('quarterlyNormalization') or {};q1=cur.get('quarterlyNormalization') or {}
 return {'fairValueChangePct':pct(n((prev.get('fairValue') or {}).get('base')),n((cur.get('fairValue') or {}).get('base'))),'sustainableGrowthPrevious':n(q0.get('sustainableGrowth')),'sustainableGrowthCurrent':n(q1.get('sustainableGrowth')),'methodChanges':rows}
def main():
 summary=[]
 for td in BT.iterdir() if BT.exists() else []:
  if not td.is_dir():continue
  snaps=[]
  for p in sorted(td.glob('*.json')):
   try:s=json.load(open(p,encoding='utf-8'))
   except:continue
   if (s.get('fairValue') or {}).get('base') is not None:snaps.append(s)
  if not snaps:continue
  points=[]
  for i,s in enumerate(snaps):
   point={'quarter':s.get('quarter'),'lockedAt':s.get('lockedAt'),'informationStatus':s.get('informationStatus'),'priceAtLock':s.get('price'),'fairValue':s.get('fairValue'),'entryZone':s.get('entryZone'),'progress':s.get('progress',{}),'quarterlyNormalization':s.get('quarterlyNormalization')}
   if i:point['changeAttribution']=attribution(snaps[i-1],s)
   points.append(point)
  payload={'ticker':td.name,'updatedAt':datetime.now(timezone.utc).isoformat(),'points':points,'policy':'Timeline preserves quarter snapshots; attribution compares only information stored at each lock.'}
  json.dump(payload,open(OUT/f'{td.name}.json','w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False)
  latest=points[-1];chg=(latest.get('changeAttribution') or {}).get('fairValueChangePct')
  summary.append({'ticker':td.name,'quarters':len(points),'latestQuarter':latest['quarter'],'latestBase':(latest.get('fairValue') or {}).get('base'),'latestFVChangePct':chg})
 json.dump({'updatedAt':datetime.now(timezone.utc).isoformat(),'count':len(summary),'stocks':summary},open(OUT/'summary.json','w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False)
 print('FV_TIMELINES',len(summary))
if __name__=='__main__':main()