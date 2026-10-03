from datetime import datetime
def _dt(v):
 try:return datetime.fromisoformat(str(v).replace('Z','+00:00'))
 except:return None
def _ticker(v):return str(v or '').replace('.JK','').strip().upper()
def resolve(snapshot,period_evidence,availability_evidence):
 out=dict(snapshot)
 if not isinstance(period_evidence,dict) or not isinstance(availability_evidence,dict):return out
 ticker=_ticker(out.get('ticker'));quarter=str(out.get('financialQuarter') or '').upper()
 # Source A proves report identity/period only.
 if _ticker(period_evidence.get('ticker'))!=ticker:return out
 if period_evidence.get('source')!='IDX_FINANCIAL_DATA_RATIO':return out
 if period_evidence.get('verification')!='OFFICIAL_IDX_PUBLIC':return out
 if str(period_evidence.get('financialQuarter') or '').upper()!=quarter:return out
 pid=str(period_evidence.get('id') or '').strip()
 if not pid:return out
 # Source B proves when the same filing became available.
 if _ticker(availability_evidence.get('ticker'))!=ticker:return out
 if availability_evidence.get('source')!='IDX' or availability_evidence.get('verification')!='OFFICIAL_IDX_API':return out
 if availability_evidence.get('documentType')!='FINANCIAL_STATEMENT':return out
 if str(availability_evidence.get('financialQuarter') or '').upper()!=quarter:return out
 aid=str(availability_evidence.get('id') or '').strip();pub=_dt(availability_evidence.get('publishedAt'))
 if not aid or not pub:return out
 # Cross-source identity must be explicit; never join by ticker+date heuristics.
 if str(period_evidence.get('filingKey') or '')!=str(availability_evidence.get('filingKey') or '') or not period_evidence.get('filingKey'):return out
 out['reportPublishedAt']=pub.isoformat();out['lockedAt']=pub.isoformat();out['lockTimeSource']='dualSourceReportPublishedAt';out['pointInTimeQuality']='VERIFIED'
 out['filingProvenance']={'contractVersion':'IDX_DUAL_SOURCE_FILING_PROVENANCE_V1','filingKey':period_evidence['filingKey'],'periodEvidenceId':pid,'availabilityEvidenceId':aid,'periodSource':period_evidence['source'],'availabilitySource':availability_evidence['source']}
 return out
