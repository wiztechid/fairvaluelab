from filing_provenance import resolve
def base():
 return {'ticker':'AADI','financialQuarter':'2026Q2','lockedAt':'2026-09-17T00:00:00+00:00','lockTimeSource':'engineAsOfFallback','pointInTimeQuality':'PROVISIONAL'}
def filing(**kw):
 x={'id':'idx-1','ticker':'AADI','source':'IDX','verification':'OFFICIAL_IDX_API','publishedAt':'2026-08-01T10:00:00+07:00','financialQuarter':'2026Q2','documentType':'FINANCIAL_STATEMENT'}
 x.update(kw);return x
def unchanged(d):
 assert d['pointInTimeQuality']=='PROVISIONAL' and d['lockTimeSource']=='engineAsOfFallback'
for evidence in [filing(),filing(ticker='ADRO'),filing(financialQuarter='2026Q1'),filing(source='OTHER'),filing(publishedAt=None),None]:
 unchanged(resolve(base(),evidence))
 # Old compatibility flag must be inert; no hidden escape hatch remains.
 unchanged(resolve(base(),evidence,allow_legacy_promotion=True))
print('FILING_PROVENANCE_NO_SINGLE_SOURCE_PROMOTION_V2_PASS')
