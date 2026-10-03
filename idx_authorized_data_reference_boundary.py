"""Fail-closed boundary for already-obtained authorized IDX Data Reference records.
This module performs no network access and assumes no undocumented field names.
A caller must explicitly map an authorized feed/spec into this minimal contract.
"""
from datetime import datetime

def _dt(v):
    try:return datetime.fromisoformat(str(v).replace('Z','+00:00'))
    except:return None

def normalize(record):
    if not isinstance(record,dict):return None
    if record.get('source')!='IDX_DATA_REFERENCE_ENTERPRISE':return None
    if record.get('verification')!='AUTHORIZED_IDX_SUBSCRIBER_FEED':return None
    if record.get('recordType')!='FINANCIAL_STATEMENT':return None
    ticker=str(record.get('ticker') or '').replace('.JK','').strip().upper()
    quarter=str(record.get('financialQuarter') or '').strip().upper()
    native_id=str(record.get('sourceNativeDocumentId') or '').strip()
    published=_dt(record.get('publishedAt'))
    if not ticker or not quarter or not native_id or not published:return None
    # Never derive identity from ticker/quarter/date/title/filename/url.
    return {'ticker':ticker,'financialQuarter':quarter,'source':'IDX_DATA_REFERENCE_ENTERPRISE',
            'verification':'AUTHORIZED_IDX_SUBSCRIBER_FEED','documentType':'FINANCIAL_STATEMENT',
            'sourceNativeDocumentId':native_id,'publishedAt':published.isoformat()}
