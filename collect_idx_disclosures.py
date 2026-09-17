import json,re,hashlib,urllib.request
from html.parser import HTMLParser
from datetime import datetime,timezone,timedelta
from pathlib import Path
from des_universe import TICKERS
OUT=Path('data/idx_disclosures.json');HEALTH=Path('data/idx_collector_status.json');URL='https://www.idx.co.id/id/berita/pengumuman';TICK=set(TICKERS)
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36'
class TextParser(HTMLParser):
 def __init__(self):super().__init__();self.parts=[]
 def handle_data(self,data):
  s=' '.join(data.split())
  if s:self.parts.append(s)
def fetch():
 errors=[]
 # IDX rejects plain datacenter urllib traffic with HTTP 403. curl_cffi is already
 # installed by yfinance and presents a normal browser TLS/client fingerprint.
 try:
  from curl_cffi import requests
  r=requests.get(URL,headers={'Accept-Language':'id-ID,id;q=0.9,en;q=0.7','Referer':'https://www.idx.co.id/id/'},impersonate='chrome',timeout=45)
  if r.status_code==200 and len(r.text)>1000:return r.text,'curl_cffi/chrome'
  errors.append(f'curl_cffi HTTP {r.status_code}')
 except Exception as e:errors.append(f'curl_cffi {type(e).__name__}: {e}')
 try:
  req=urllib.request.Request(URL,headers={'User-Agent':UA,'Accept':'text/html,application/xhtml+xml','Accept-Language':'id-ID,id;q=0.9,en;q=0.7','Referer':'https://www.idx.co.id/id/'})
  with urllib.request.urlopen(req,timeout=45) as r:return r.read().decode('utf-8','replace'),'urllib'
 except Exception as e:errors.append(f'urllib {type(e).__name__}: {e}')
 raise RuntimeError('; '.join(errors))
def parse(doc):
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
  key=f'{ticker}|{dt.isoformat()}|{title}';rows.append({'id':hashlib.sha256(key.encode()).hexdigest()[:20],'ticker':ticker,'title':title,'publishedAt':dt.isoformat(),'source':'IDX','sourceUrl':URL,'verification':'PUBLIC_IDX_PAGE'})
 return rows
def save_health(ok,**kw):
 HEALTH.parent.mkdir(parents=True,exist_ok=True);json.dump({'checkedAt':datetime.now(timezone.utc).isoformat(),'ok':ok,'source':URL,**kw},open(HEALTH,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
def main():
 old=[]
 try:old=json.load(open(OUT,encoding='utf-8'))
 except:pass
 try:doc,transport=fetch();new=parse(doc)
 except Exception as e:
  save_health(False,error=str(e),cachedRecords=len(old));print('IDX_COLLECT_ERROR',repr(e),'cache',len(old));return
 if not new:
  save_health(False,error='IDX page fetched but no DES announcement parsed',transport=transport,cachedRecords=len(old));print('IDX_COLLECT_ERROR no parseable DES announcements; cache',len(old));return
 by={r.get('id') or hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest()[:20]:r for r in old}
 for r in new:by[r['id']]=r
 cutoff=datetime.now(timezone.utc)-timedelta(days=1100);kept=[]
 for r in sorted(by.values(),key=lambda r:r.get('publishedAt',''),reverse=True):
  try:
   if datetime.fromisoformat(r['publishedAt']).astimezone(timezone.utc)>=cutoff:kept.append(r)
  except:kept.append(r)
 OUT.parent.mkdir(parents=True,exist_ok=True);json.dump(kept,open(OUT,'w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False);save_health(True,transport=transport,pageRecords=len(new),cachedRecords=len(kept),tickers=len({r['ticker'] for r in kept}))
 print('IDX_COLLECTED',len(new),'page records; cache',len(kept),'tickers',len({r['ticker'] for r in kept}),'via',transport)
if __name__=='__main__':main()
