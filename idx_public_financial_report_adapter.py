from datetime import datetime
def _dt(v):
 try:return datetime.fromisoformat(str(v).replace('Z','+00:00'))
 except:return None
def _ticker(v):return str(v or '').replace('.JK','').strip().upper()
def normalize(record):
 """Normalize an already-obtained official IDX Financial Report record.
 No network access, URL guessing, filename-ID inference, or quarter inference."""
 if not isinstance(record,dict):return None
 if record.get('source')!='IDX_PUBLIC_FINANCIAL_REPORT':return None
 if record.get('verification')!='OFFICIAL_IDX_PUBLIC':return None
 ticker=_ticker(record.get('ticker'));published=_dt(record.get('publishedAt'))
 attachment_id=str(record.get('attachmentId') or '').strip()
 document_id=str(record.get('externalDocumentId') or '').strip()
 quarter=str(record.get('financialQuarter') or '').upper().strip()
 if not ticker or not published or not attachment_id or not document_id or not quarter:return None
 # Identity must be supplied by official record/instance metadata, never synthesized here.
 return {'id':attachment_id,'ticker':ticker,'source':'IDX','verification':'OFFICIAL_IDX_API','publishedAt':published.isoformat(),'financialQuarter':quarter,'documentType':'FINANCIAL_STATEMENT','externalDocumentId':document_id,'sourceUrl':record.get('sourceUrl')}
