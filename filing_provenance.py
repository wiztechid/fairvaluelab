import re
from datetime import datetime
def _dt(v):
    try:return datetime.fromisoformat(str(v).replace('Z','+00:00'))
    except:return None
def resolve(snapshot, disclosure):
    out=dict(snapshot)
    # Fail closed: no authoritative evidence means no promotion.
    if not isinstance(disclosure,dict):return out
    ticker=str(out.get('ticker','')).replace('.JK','').upper()
    if str(disclosure.get('ticker','')).replace('.JK','').upper()!=ticker:return out
    if disclosure.get('source')!='IDX' or disclosure.get('verification')!='OFFICIAL_IDX_API':return out
    pub=_dt(disclosure.get('publishedAt'))
    if not pub:return out
    q=str(out.get('financialQuarter',''))
    title=str(disclosure.get('title','')).upper()
    # Quarter must be explicitly present in normalized metadata or title; never infer from publication date.
    dq=str(disclosure.get('financialQuarter') or '').upper()
    if dq!=q.upper() and q.upper() not in title:return out
    if not re.search(r'LAPORAN\s+KEUANGAN|FINANCIAL\s+STATEMENT',title):return out
    out['reportPublishedAt']=pub.isoformat()
    out['lockedAt']=pub.isoformat()
    out['lockTimeSource']='reportPublishedAt'
    out['pointInTimeQuality']='VERIFIED'
    out['filingProvenance']={'source':'IDX','verification':'OFFICIAL_IDX_API','disclosureId':disclosure.get('id'),'sourceUrl':disclosure.get('sourceUrl')}
    return out
