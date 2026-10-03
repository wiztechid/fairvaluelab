"""Fail-closed boundary for already-obtained authorized IDX Data Reference records.
No network access. No undocumented IDX field names are assumed.
The caller must map a real authorized feed/spec into this contract and preserve that mapping provenance.
"""
from datetime import datetime
def _dt(v):
    try:return datetime.fromisoformat(str(v).replace('Z','+00:00'))
    except:return None
def normalize(record, pinned_spec=None):
    if not isinstance(record,dict) or not isinstance(pinned_spec,dict):return None
    expected_ref=str(pinned_spec.get('specReference') or '').strip()
    expected_field=str(pinned_spec.get('feedRecordIdField') or '').strip()
    expected_hash=str(pinned_spec.get('specSha256') or '').strip().lower()
    if not expected_ref or not expected_field or len(expected_hash)!=64:return None
    if record.get('source')!='IDX_DATA_REFERENCE_ENTERPRISE':return None
    if record.get('verification')!='AUTHORIZED_IDX_SUBSCRIBER_FEED':return None
    if record.get('recordType')!='FINANCIAL_STATEMENT':return None
    ticker=str(record.get('ticker') or '').replace('.JK','').strip().upper()
    quarter=str(record.get('financialQuarter') or '').strip().upper()
    native_id=str(record.get('sourceNativeDocumentId') or '').strip()
    published=_dt(record.get('publishedAt'))
    spec_reference=str(record.get('specReference') or '').strip()
    native_id_field=str(record.get('feedRecordIdField') or '').strip()
    if not ticker or not quarter or not native_id or not published or not spec_reference or not native_id_field:return None
    if spec_reference!=expected_ref or native_id_field!=expected_field:return None
    return {'ticker':ticker,'financialQuarter':quarter,'source':'IDX_DATA_REFERENCE_ENTERPRISE',
            'verification':'AUTHORIZED_IDX_SUBSCRIBER_FEED','documentType':'FINANCIAL_STATEMENT',
            'sourceNativeDocumentId':native_id,'publishedAt':published.isoformat(),
            'mappingProvenance':{'specReference':spec_reference,'feedRecordIdField':native_id_field,'specSha256':expected_hash}}
