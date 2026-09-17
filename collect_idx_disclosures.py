import json,re,hashlib,urllib.request
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

class TextParser(HTMLParser):
 def __init__(self):super().__init__();self.parts=[]
 def handle_data(self,data):
  s=' '.join(data.split())
  if s:self.parts.append(s)

def browser_get(url):
 from curl_cffi import requests
 headers={'Accept':'application/json,text/plain,*/*','Accept-Language':'id-ID,id;q=0.9,en;q=0.7','Referer':'https://www.idx.co.id/id/perusahaan-tercatat/keterbukaan-informasi/','User-Agent':UA}
 r=requests.get(url,headers=headers,impersonate='chrome',timeout=45)
 if r.status_code!=200:raise RuntimeError(f'HTTP {r.status_code}')
 return r.text

def fetch_api():
 # Official IDX JSON endpoint used by the public disclosure interface. Keep the
 # request small/current so Actions does not hammer IDX and cached history can
 # accumulate across runs.
 now=datetime.now(timezone(timedelta(hours=7)))
 start=now-timedelta(days=14)
 params=(f'?kodeEmiten=&emitenType=*&indexFrom=0&pageSize=100'
         f'&dateFrom={start:%Y%m%d}&dateTo={now:%Y%m%d}&lang=id&keyword=')
 text=browser_get(API_URL+params)
 obj=json.loads(text)
 raw=obj.get('Results') or obj.get('results') or obj.get('data') or obj.get('Data') or []
 rows=[]
 for item in raw:
  a=item.get('pengumuman') if isinstance(item,dict) and isinstance(item.get('pengumuman'),dict) else item
  if not isinstance(a,dict):continue
  ticker=str(a.get('Kode_Emiten') or a.get('KodeEmiten') or a.get('kodeEmiten') or a.get('code') or '').strip().upper()
  if ticker not in TICK:continue
  title=str(a.get('JudulPengumuman') or a.get('Judul') or a.get('title') or a.get('Perihal') or '').strip()
  if not title:continue
  rawdt=a.get('TglPengumuman') or a.get('TanggalPengumuman') or a.get('publishedAt') or a.get('CreatedDate') or a.get('File_Modified')
  dt=None
  if rawdt:
   s=str(rawdt).replace('Z','+00:00')
   try:dt=datetime.fromisoformat(s)
   except:
    m=re.search(r'(20\d\d)[-/](\d\d)[-/](\d\d)(?:[ T](\d\d):(\d\d)(?::(\d\d))?)?',s)
    if m:
     y,mo,d,hh,mi,ss=m.groups();dt=datetime(int(y),int(mo),int(d),int(hh or 0),int(mi or 0),int(ss or 0),tzinfo=timezone(timedelta(hours=7)))
  if dt is None:continue
  if dt.tzinfo is None:dt=dt.replace(tzinfo=timezone(timedelta(hours=7)))
  attachments=item.get('attachments') if isinstance(item,dict) else None
  source_url=PAGE_URL
  if isinstance(attachments,list) and attachments:
   x=attachments[0]
   if isinstance(x,dict):source_url=x.get('url') or x.get('File_Path') or source_url
  if isinstance(source_url,str) and source_url.startswith('/'):
   source_url='https://www.idx.co.id'+source_url
  key=f'{ticker}|{dt.isoformat()}|{title}'
  rows.append({'id':hashlib.sha256(key.encode()).hexdigest()[:20],'ticker':ticker,'title':title,'publishedAt':dt.isoformat(),'source':'IDX','sourceUrl':source_url,'verification':'OFFICIAL_IDX_API'})
 return rows,'official-api'

def fetch_page():
 doc=browser_get(PAGE_URL)
 p=TextParser();p.feed(doc);text=' '.join(p.parts)
 months={'jan':1,'feb':2,'mar':3,'apr':4,'mei':5,'jun':6,'jul':7,'agu':8,'agt':8,'sep':9,'okt':10,'nov':11,'des':12}
 date=r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|Mei|Jun|Jul|Agu|Agt|Sep|Okt|Nov|Des)\s+(20\d{2})\s+(\d{1,2}):(\d{2}):(\d{2})'
 starts=list(re.finditer(date,text,re.I));rows=[]
 for i,m in enumerate(starts):
  chunk=text[m.end():starts[i+1].start() if i+1<len(starts) else min(len(text),m.end()+3000)]
  tm=re.search(r'\[\s*([A-Z0-9]{4})\s*\]',chunk)
  if not tm:continue
  ticker=tm.group(1).upper()
  if ticker not in TICK:continue
  title=' '.join(chunk[:tm.start()].strip(' -–—|:').split())
  if not title or len(title)>500:continue
  day,mon,yr,hh,mm,ss=m.groups();dt=datetime(int(yr),months[mon.lower()],int(day),int(hh),int(mm),int(ss),tzinfo=timezone(timedelta(hours=7)))
  key=f'{ticker}|{dt.isoformat()}|{title}'
  rows.append({'id':hashlib.sha256(key.encode()).hexdigest()[:20],'ticker':ticker,'title':title,'publishedAt':dt.isoformat(),'source':'IDX','sourceUrl':PAGE_URL,'verification':'PUBLIC_IDX_PAGE'})
 return rows,'public-page'

def fetch():
 errors=[]
 for fn in (fetch_api,fetch_page):
  try:
   rows,transport=fn()
   if rows:return rows,transport
   errors.append(f'{transport}: no DES records')
  except Exception as e:errors.append(f'{fn.__name__}: {type(e).__name__}: {e}')
 raise RuntimeError('; '.join(errors))

def save_health(ok,**kw):
 HEALTH.parent.mkdir(parents=True,exist_ok=True)
 json.dump({'checkedAt':datetime.now(timezone.utc).isoformat(),'ok':ok,'source':API_URL,**kw},open(HEALTH,'w',encoding='utf-8'),ensure_ascii=False,indent=2)

def main():
 old=[]
 try:old=json.load(open(OUT,encoding='utf-8'))
 except:pass
 try:new,transport=fetch()
 except Exception as e:
  save_health(False,error=str(e),cachedRecords=len(old));print('IDX_COLLECT_ERROR',repr(e),'cache',len(old));return
 by={r.get('id') or hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest()[:20]:r for r in old}
 for r in new:by[r['id']]=r
 cutoff=datetime.now(timezone.utc)-timedelta(days=1100);kept=[]
 for r in sorted(by.values(),key=lambda r:r.get('publishedAt',''),reverse=True):
  try:
   if datetime.fromisoformat(r['publishedAt']).astimezone(timezone.utc)>=cutoff:kept.append(r)
  except:kept.append(r)
 OUT.parent.mkdir(parents=True,exist_ok=True)
 json.dump(kept,open(OUT,'w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False)
 save_health(True,transport=transport,pageRecords=len(new),cachedRecords=len(kept),tickers=len({r['ticker'] for r in kept}))
 print('IDX_COLLECTED',len(new),'records; cache',len(kept),'tickers',len({r['ticker'] for r in kept}),'via',transport)

if __name__=='__main__':main()
