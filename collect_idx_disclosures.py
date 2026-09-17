import json,re,hashlib,urllib.request
from html.parser import HTMLParser
from datetime import datetime,timezone,timedelta
from pathlib import Path
from des_universe import TICKERS
OUT=Path('data/idx_disclosures.json');URL='https://www.idx.co.id/id/berita/pengumuman';TICK=set(TICKERS)
UA='Mozilla/5.0 WISS-FairValueLab/1.1 public-disclosure-collector'
class TextParser(HTMLParser):
 def __init__(self):super().__init__();self.parts=[];self.href=None
 def handle_starttag(self,tag,attrs):
  if tag=='a':self.href=dict(attrs).get('href')
 def handle_endtag(self,tag):
  if tag=='a':self.href=None
 def handle_data(self,data):
  s=' '.join(data.split())
  if s:self.parts.append((s,self.href))
def fetch():
 req=urllib.request.Request(URL,headers={'User-Agent':UA,'Accept-Language':'id-ID,id;q=0.9,en;q=0.7'})
 with urllib.request.urlopen(req,timeout=45) as r:return r.read().decode('utf-8','replace')
def parse(doc):
 p=TextParser();p.feed(doc)
 # IDX separates timestamp/title/ticker into different DOM text nodes. Parse a continuous
 # public-text stream rather than requiring all fields to occur in one HTML node.
 text=' '.join(s for s,_ in p.parts)
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
def main():
 old=[]
 try:old=json.load(open(OUT,encoding='utf-8'))
 except:pass
 try:new=parse(fetch())
 except Exception as e:print('IDX_COLLECT_WARNING',repr(e),'keeping',len(old),'existing records');return
 if not new:
  print('IDX_COLLECT_WARNING no parseable DES announcements; keeping',len(old),'existing records');return
 by={r.get('id') or hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest()[:20]:r for r in old}
 for r in new:by[r['id']]=r
 cutoff=datetime.now(timezone.utc)-timedelta(days=1100);kept=[]
 for r in sorted(by.values(),key=lambda r:r.get('publishedAt',''),reverse=True):
  try:
   if datetime.fromisoformat(r['publishedAt']).astimezone(timezone.utc)>=cutoff:kept.append(r)
  except:kept.append(r)
 OUT.parent.mkdir(parents=True,exist_ok=True);json.dump(kept,open(OUT,'w',encoding='utf-8'),ensure_ascii=False,indent=2,allow_nan=False)
 print('IDX_COLLECTED',len(new),'page records; cache',len(kept),'tickers',len({r['ticker'] for r in kept}))
if __name__=='__main__':main()
