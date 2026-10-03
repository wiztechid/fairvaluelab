from filing_provenance import resolve
def base():
 return {'ticker':'AADI','financialQuarter':'2026Q2','lockedAt':'2026-09-17T00:00:00+00:00','lockTimeSource':'engineAsOfFallback','pointInTimeQuality':'PROVISIONAL'}
def filing(**kw):
 x={'id':'idx-1','ticker':'AADI','source':'IDX','verification':'OFFICIAL_IDX_API','publishedAt':'2026-08-01T10:00:00+07:00','financialQuarter':'2026Q2','documentType':'FINANCIAL_STATEMENT','sourceUrl':'https://www.idx.co.id/'}
 x.update(kw);return x
def unchanged(d):
 assert d['pointInTimeQuality']=='PROVISIONAL' and d['lockTimeSource']=='engineAsOfFallback'
unchanged(resolve(base(),filing()))
v=resolve(base(),filing(),allow_legacy_promotion=True);assert v['pointInTimeQuality']=='VERIFIED';assert v['lockTimeSource']=='reportPublishedAt';assert v['filingProvenance']['disclosureId']=='idx-1'
for bad in [filing(ticker='ADRO'),filing(financialQuarter='2026Q1'),filing(source='OTHER'),filing(verification='UNVERIFIED'),filing(publishedAt=None),filing(documentType='OTHER'),filing(id='')]:unchanged(resolve(base(),bad,allow_legacy_promotion=True))
unchanged(resolve(base(),None,allow_legacy_promotion=True))
print('FILING_PROVENANCE_ADVERSARIAL_V1_PASS')
