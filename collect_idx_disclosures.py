import json,re,hashlib,urllib.request
from html.parser import HTMLParser
from datetime import datetime,timezone,timedelta
from pathlib import Path
from des_universe import TICKERS

OUT=Path('data/idx_disclosures.json')
URL='https://www.idx.co.id/id/berita/pengumuman'
TICK=set(TICKERS)
UA='WISS-FairValueLab/1.0 public-disclosure-collector'

class TextParser(HTMLParser):
 def __init__(self):super().__init__();self.parts=[];self.href=None
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='a':self.href=a.get('href')
 def handle_data(self,data):
  s=' '.join(data.split())
  if s:self.parts.append((s,self.href))

def fetch():
 req=urllib.request.Request(URL,headers={'User-Agent':UA,'Accept-Language':'id-ID,id;q=0.9'})
 with urllib.request.urlopen(req,timeout=45) as r:return r.read().decode('utf-8','ignore')

def parse(html):
 # IDX public announcement page exposes announcement text in rendered/public HTML.
 # We only retain rows that explicitly name a DES ticker in [XXXX].
 p=TextParser();p.feed(html);text='\n'.join(x[0] for x in p.parts)
 lines=[x.strip() for x in text.splitlines() if x.strip()]
 date_re=re.compile(r'^(\d{1,2})\s+(Jan|Feb|Mar|Apr|Mei|Jun|Jul|Agt|Sep|Okt|Nov|Des)\s+(\d{4})\s+(\d{1,2}):(\d{2}):(\d{2})\s+(.+?)\s*\[\s*([A-Z0-9]{4})\s*\]$',re.I)
 months={'jan':1,'feb':2,'mar':3,'apr':4,'mei':5,'jun':6,'jul':7,'agt':8,'sep':9,'okt':10,'nov':11,'des':12}
 rows=[]
 for line in lines:
  m=date_re.match(line)
  if not m:continue
  day,mon,yr,hh,mm,ss,title,ticker=m.groups();ticker=ticker.upper()
  if ticker not in TICK:continue
  dt=datetime(int(yr),months[mon.lower()],int(day),int(hh),int(mm),int(ss),tzinfo=timezone(timedelta(hours=7)))
  key=f'{ticker}|{dt.isoformat()}|{title.strip()}'
  rows.append({'id':hashlib.sha1(key.encode()).hexdigest()[:16],'ticker':ticker,'title':title.strip(),'publishedAt':dt.isoformat(),'source':'IDX','sourceUrl':URL,'verification':'PUBLIC_IDX_PAGE'})
 return rows

def main():
 old=[]
 try:old=json.load(open(OUT,encoding='utf-8'))
 except:pass
 try:new=parse(fetch())
 except Exception as e:
  print('IDX_COLLECT_WARNING',repr(e),'keeping',len(old),'existing records');return
 by={r.get('id') or hashlib.sha1(json.dumps(r,sort_keys=True).encode()).hexdigest()[:16]:r for r in old}
 for r in new:by[r['id']]=r
 rows=sorted(by.values(),key=lambda r:r.get('publishedAt',''),reverse=True)
 # Public IDX page is the authoritative discovery source. Keep a rolling 3-year-compatible cache.
 cutoff=datetime.now(timezone.utc)-timedelta(days=1100)
 kept=[]
 for r in rows:
  try:
   dt=datetime.fromisoformat(r['publishedAt']);dt=dt.astimezone(timezone.utc)
   if dt>=cutoff:kept.append(r)
  except:kept.append(r)
 OUT.parent.mkdir(parents=True,exist_ok=True)
 json.dump(kept,open(OUT,'w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False)
 print('IDX_COLLECTED',len(new),'page records; cache',len(kept))
if __name__=='__main__':main()
