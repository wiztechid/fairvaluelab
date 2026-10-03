from idx_public_financial_report_adapter import normalize
def good(**kw):
 x={'source':'IDX_PUBLIC_FINANCIAL_REPORT','verification':'OFFICIAL_IDX_PUBLIC','ticker':'AADI','publishedAt':'2026-08-01T10:00:00+07:00','attachmentId':'ATT-123','externalDocumentId':'DOC-123','financialQuarter':'2026Q2','sourceUrl':'https://www.idx.co.id/'}
 x.update(kw);return x
v=normalize(good());assert v and v['externalDocumentId']=='DOC-123' and v['publishedAt'].startswith('2026-08-01')
for x in [None,{},good(source='OTHER'),good(verification='UNVERIFIED'),good(ticker=''),good(publishedAt=None),good(attachmentId=''),good(externalDocumentId=''),good(financialQuarter='')]:assert normalize(x) is None
# Filename-like values alone never create identity.
assert normalize({'source':'IDX_PUBLIC_FINANCIAL_REPORT','verification':'OFFICIAL_IDX_PUBLIC','ticker':'AADI','publishedAt':'2026-08-01T10:00:00+07:00','filename':'20260801_AADI_report_123.pdf','financialQuarter':'2026Q2'}) is None
print('IDX_PUBLIC_FINANCIAL_REPORT_ADAPTER_V1_PASS')
