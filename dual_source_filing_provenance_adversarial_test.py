from dual_source_filing_provenance import resolve
def base():return {'ticker':'AADI','financialQuarter':'2026Q2','lockedAt':'2026-09-17T00:00:00+00:00','lockTimeSource':'engineAsOfFallback','pointInTimeQuality':'PROVISIONAL'}
def p(**kw):
 x={'id':'period-1','ticker':'AADI','source':'IDX_FINANCIAL_DATA_RATIO','verification':'OFFICIAL_IDX_PUBLIC','financialQuarter':'2026Q2','externalDocumentId':'IDX-DOC-123'};x.update(kw);return x
def a(**kw):
 x={'id':'avail-1','ticker':'AADI','source':'IDX','verification':'OFFICIAL_IDX_API','documentType':'FINANCIAL_STATEMENT','financialQuarter':'2026Q2','externalDocumentId':'IDX-DOC-123','publishedAt':'2026-08-01T10:00:00+07:00'};x.update(kw);return x
def provisional(x):assert x['pointInTimeQuality']=='PROVISIONAL' and x['lockTimeSource']=='engineAsOfFallback'
v=resolve(base(),p(),a());assert v['pointInTimeQuality']=='VERIFIED';assert v['lockTimeSource']=='dualSourceReportPublishedAt'
for pe,ae in [(None,a()),(p(),None),(p(ticker='ADRO'),a()),(p(financialQuarter='2026Q1'),a()),(p(source='OTHER'),a()),(p(verification='UNVERIFIED'),a()),(p(id=''),a()),(p(externalDocumentId=''),a()),(p(externalDocumentId='X'),a()),(p(),a(ticker='ADRO')),(p(),a(financialQuarter='2026Q1')),(p(),a(source='OTHER')),(p(),a(verification='UNVERIFIED')),(p(),a(documentType='OTHER')),(p(),a(id='')),(p(),a(externalDocumentId='')),(p(),a(publishedAt=None)),(p(),a(externalDocumentId='X'))]:provisional(resolve(base(),pe,ae))
print('DUAL_SOURCE_FILING_PROVENANCE_V1_PASS')

# Public Financial Report evidence must never satisfy the API availability leg merely because it is official IDX evidence.
public_leg=a(source='IDX_PUBLIC_FINANCIAL_REPORT',verification='OFFICIAL_IDX_PUBLIC')
provisional(resolve(base(),p(),public_leg))
print('DUAL_SOURCE_PUBLIC_CANNOT_MASQUERADE_AS_API_PASS')
