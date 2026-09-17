import json,re,hashlib
from html.parser import HTMLParser
from datetime import datetime,timezone,timedelta
from pathlib import Path
from des_universe import TICKERS

OUT=Path('data/idx_disclosures.json')
HEALTH=Path('data/idx_collector_status.json')
PAGE_URL='https://www.idx.co.id/id/berita/pengumuman'
API_URL='https://www.idx.co.id/primary/ListedCompany/GetAnnouncement'
TICK=set(TICKERS)
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36'
HISTORY_DAYS=1096

def browser_get(url):
 from curl_cffi import requests
 h={'Accept':'application/json,text/plain,*/*','Accept-Language':'id-ID,id;q=0.9,en;q=0.7','Referer':'https://www.idx.co.id/id/perusahaan-tercatat/keterbukaan-informasi/','User-Agent':UA}
 r=requests.get(url,headers=h,impersonate='chrome',timeout=45)
 if r.status_code!=200:raise RuntimeError(f'HTTP {r.status_code}')
 return r.text

def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)

def first(d,*keys):
 for k in keys:
  v=d.get(k)
  if v not in (None,''):return v
 return None

def parse_dt(v):
 if not v:return None
 s=str(v).replace('Z','+00:00')
 try:return datetime.fromisoformat(s)
 except:pass
 m=re.search(r'(20\d\d)[-/](\d\d)[-/](\d\d)(?:[ T](\d\d):(\d\d)(?::(\d\d))?)?',s)
 if m:
  y,mo,d,hh,mi,ss=m.groups();return datetime(int(y),int(mo),int(d),int(hh or 0),int(mi or 0),int(ss or 0),tzinfo=timezone(timedelta(hours=7)))
 return None

def normalize_obj(obj):
 rows=[]
 for a in walk(obj):
  ticker=str(first(a,'Kode_Emiten','KodeEmiten','kodeEmiten','Kode_Emiten1','EmitenCode','code','Code') or '').replace('.JK','').strip().upper()
  if ticker not in TICK:continue
  title=str(first(a,'JudulPengumuman','Judul','judul','title','Title','Perihal','NamaPengumuman') or '').strip()
  dt=parse_dt(first(a,'TglPengumuman','TanggalPengumuman','publishedAt','CreatedDate','File_Modified','Tanggal','Date'))
  if not title or not dt:continue
  if dt.tzinfo is None:dt=dt.replace(tzinfo=timezone(timedelta(hours=7)))
  url=first(a,'url','Url','URL','File_Path','FilePath','Attachment','Link') or PAGE_URL
  if isinstance(url,str) and url.startswith('/'):url='https://www.idx.co.id'+url
  key=f'{ticker}|{dt.isoformat()}|{title}'
  rows.append({'id':hashlib.sha256(key.encode()).hexdigest()[:20],'ticker':ticker,'title':title,'publishedAt':dt.isoformat(),'source':'IDX','sourceUrl':url,'verification':'OFFICIAL_IDX_API'})
 return rows

def fetch_api():
 # Query month-by-month for the rolling 3Y history. Small windows are friendlier
 # to IDX and let us retain a durable local cache per ticker.
 now=datetime.now(timezone(timedelta(hours=7)));cut=now-timedelta(days=HISTORY_DAYS)
 cursor=now;allrows={};windows=0
 while cursor>cut:
  start=max(cut,cursor-timedelta(days=31));index=0
  while index<1000:
   url=(API_URL+f'?kodeEmiten=&emitenType=*&indexFrom={index}&pageSize=100'
        f'&dateFrom={start:%Y%m%d}&dateTo={cursor:%Y%m%d}&lang=id&keyword=')
   obj=json.loads(browser_get(url));batch=normalize_obj(obj)
   for r in batch:allrows[r['id']]=r
   # Stop paging when the raw response is clearly small or no new normalized rows.
   raw_count=sum(1 for d in walk(obj) if isinstance(d,dict) and any(k in d for k in ('Kode_Emiten','KodeEmiten','kodeEmiten')))
   if raw_count<100:break
   index+=100
  windows+=1;cursor=start-timedelta(seconds=1)
 return list(allrows.values()),f'official-api-3y/{windows}w'

def fetch():
 try:
  rows,transport=fetch_api()
  if rows:return rows,transport
  raise RuntimeError('official IDX API returned no identifiable DES disclosure records')
 except Exception as e:raise RuntimeError(f'official-api: {type(e).__name__}: {e}')

def save_health(ok,**kw):
 HEALTH.parent.mkdir(parents=True,exist_ok=True)
 json.dump({'checkedAt':datetime.now(timezone.utc).isoformat(),'ok':ok,'source':API_URL,'historyDays':HISTORY_DAYS,**kw},open(HEALTH,'w',encoding='utf-8'),ensure_ascii=False,indent=2)

def main():
 old=[]
 try:old=json.load(open(OUT,encoding='utf-8'))
 except:pass
 try:new,transport=fetch()
 except Exception as e:
  save_health(False,error=str(e),cachedRecords=len(old));print('IDX_COLLECT_ERROR',repr(e),'cache',len(old));return
 by={r.get('id') or hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest()[:20]:r for r in old if isinstance(r,dict)}
 for r in new:by[r['id']]=r
 cutoff=datetime.now(timezone.utc)-timedelta(days=HISTORY_DAYS);kept=[]
 for r in sorted(by.values(),key=lambda r:r.get('publishedAt',''),reverse=True):
  try:
   if datetime.fromisoformat(r['publishedAt']).astimezone(timezone.utc)>=cutoff:kept.append(r)
  except:pass
 OUT.parent.mkdir(parents=True,exist_ok=True)
 json.dump(kept,open(OUT,'w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False)
 save_health(True,transport=transport,newRecords=len(new),cachedRecords=len(kept),tickers=len({r['ticker'] for r in kept}))
 print('IDX_COLLECTED',len(new),'records; cache',len(kept),'tickers',len({r['ticker'] for r in kept}),'via',transport)
if __name__=='__main__':main()
