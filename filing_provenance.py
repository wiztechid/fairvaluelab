from datetime import datetime
def _dt(v):
    try:return datetime.fromisoformat(str(v).replace('Z','+00:00'))
    except:return None
def resolve(snapshot, disclosure, allow_legacy_promotion=False):
    out=dict(snapshot)
    if not isinstance(disclosure,dict):return out
    ticker=str(out.get('ticker','')).replace('.JK','').upper()
    if str(disclosure.get('ticker','')).replace('.JK','').upper()!=ticker:return out
    if disclosure.get('source')!='IDX' or disclosure.get('verification')!='OFFICIAL_IDX_API':return out
    pub=_dt(disclosure.get('publishedAt'))
    if not pub:return out
    q=str(out.get('financialQuarter','')).upper()
    # VERIFIED promotion requires collector-normalized quarter identity.
    # Publication date/title alone are never sufficient to infer the financial quarter.
    if str(disclosure.get('financialQuarter') or '').upper()!=q:return out
    if disclosure.get('documentType')!='FINANCIAL_STATEMENT':return out
    did=str(disclosure.get('id') or '').strip()
    if not did:return out
    out['reportPublishedAt']=pub.isoformat()
    out['lockedAt']=pub.isoformat()
    out['lockTimeSource']='reportPublishedAt'
    out['pointInTimeQuality']='VERIFIED'
    out['filingProvenance']={'source':'IDX','verification':'OFFICIAL_IDX_API','disclosureId':did,'sourceUrl':disclosure.get('sourceUrl')}
    return out
