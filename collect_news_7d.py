import json,re,hashlib,html
from pathlib import Path
from datetime import datetime,timezone,timedelta
from urllib.parse import quote_plus,urlparse,parse_qs
from urllib.request import Request,urlopen
from email.utils import parsedate_to_datetime
from des_universe import TICKERS
try:
    ALIASES=json.load(open('data/ticker_aliases.json',encoding='utf-8'))
except Exception:
    ALIASES={}

OUT=Path('data/news_raw.json'); HEALTH=Path('data/news_collector_status.json')
DAYS=20
UA='Mozilla/5.0 (compatible; WISSFairValue/1.0; +https://wiztechid.github.io/fairvaluelab/)'
# Broad discovery first; the relevance gate in catalyst_7d.py decides what is publishable.
QUERIES=[
    'saham {t} Indonesia',
    '{t} aksi korporasi OR dividen OR buyback OR rights issue OR akuisisi OR ekspansi OR kontrak OR laba',
]
def fetch(url):
    req=Request(url,headers={'User-Agent':UA,'Accept':'application/rss+xml,application/xml,text/xml,*/*'})
    with urlopen(req,timeout=25) as r:return r.read().decode('utf-8','replace')
def clean_text(x):
    return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',x or ''))).strip()
def tag(block,name):
    m=re.search(r'<'+name+r'(?:\s[^>]*)?>(.*?)</'+name+r'>',block,re.I|re.S)
    return clean_text(m.group(1)) if m else ''
def source_name(block):
    m=re.search(r'<source[^>]*>(.*?)</source>',block,re.I|re.S)
    return clean_text(m.group(1)) if m else ''
def unwrap(url):
    # Google News redirect URLs remain auditable source links even when publisher URL
    # cannot be deterministically recovered from RSS.
    return html.unescape(url or '')
def parse_rss(xml,ticker):
    out=[]
    for b in re.findall(r'<item\b.*?</item>',xml,re.I|re.S):
        title=tag(b,'title'); link=unwrap(tag(b,'link')); desc=tag(b,'description'); pub=tag(b,'pubDate')
        if not title or not link:continue
        try:dt=parsedate_to_datetime(pub).astimezone(timezone.utc)
        except:continue
        if dt < datetime.now(timezone.utc)-timedelta(days=DAYS+1):continue
        src=source_name(b) or urlparse(link).netloc or 'Google News'
        key=(ticker+'|'+title.lower()+'|'+dt.date().isoformat()).encode()
        out.append({'id':hashlib.sha256(key).hexdigest()[:20],'ticker':ticker,'title':title,'summary':desc[:800],
                    'publishedAt':dt.isoformat(),'source':src,'sourceUrl':link,'discovery':'GOOGLE_NEWS_RSS'})
    return out
def main():
    rows=[]; failures=[]; now=datetime.now(timezone.utc)
    for t in TICKERS:
        seen={}
        queries=[q.format(t=t) for q in QUERIES]
        # Company/brand aliases catch stories that omit the exchange ticker (e.g. PGN vs PGAS).
        for alias in (ALIASES.get(t) or [])[:3]:
            queries.append('"'+alias+'" aksi korporasi OR dividen OR buyback OR akuisisi OR ekspansi OR kontrak OR laba')
        for query in queries:
            url='https://news.google.com/rss/search?q='+quote_plus(query+' when:20d')+'&hl=id&gl=ID&ceid=ID:id'
            try:
                for x in parse_rss(fetch(url),t):seen[x['id']]=x
            except Exception as e:failures.append({'ticker':t,'error':type(e).__name__+': '+str(e)[:160]})
        rows.extend(seen.values())
    OUT.parent.mkdir(parents=True,exist_ok=True)
    json.dump(rows,open(OUT,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
    json.dump({'checkedAt':now.isoformat(),'windowDays':DAYS,'records':len(rows),'tickers':len(set(x['ticker'] for x in rows)),
               'failures':failures[:100]},open(HEALTH,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
    print('NEWS_20D_COLLECTED',len(rows),'records',len(set(x['ticker'] for x in rows)),'tickers','failures',len(failures))
if __name__=='__main__':main()
