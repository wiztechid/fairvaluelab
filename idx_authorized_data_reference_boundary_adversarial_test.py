from idx_authorized_data_reference_boundary import normalize
valid={'source':'IDX_DATA_REFERENCE_ENTERPRISE','verification':'AUTHORIZED_IDX_SUBSCRIBER_FEED','recordType':'FINANCIAL_STATEMENT','ticker':'AADI','financialQuarter':'2026Q1','sourceNativeDocumentId':'NATIVE-ID-FROM-AUTHORIZED-SPEC','publishedAt':'2026-04-30T16:51:00+07:00'}
v=normalize(valid);assert v and v['sourceNativeDocumentId']=='NATIVE-ID-FROM-AUTHORIZED-SPEC'
for bad in [None,{},dict(valid,source='IDX_PUBLIC_FINANCIAL_REPORT'),dict(valid,verification='OFFICIAL_IDX_PUBLIC'),dict(valid,recordType='OTHER'),dict(valid,ticker=''),dict(valid,financialQuarter=''),dict(valid,sourceNativeDocumentId=''),dict(valid,publishedAt=None)]:
 assert normalize(bad) is None
# Public filenames/URLs or derived combinations can never substitute for a native authorized-feed identity.
assert normalize({'source':'IDX_DATA_REFERENCE_ENTERPRISE','verification':'AUTHORIZED_IDX_SUBSCRIBER_FEED','recordType':'FINANCIAL_STATEMENT','ticker':'AADI','financialQuarter':'2026Q1','publishedAt':'2026-04-30T16:51:00+07:00','filename':'FinancialStatement-2026-I-AADI.pdf','sourceUrl':'https://idx.id/'}) is None
print('IDX_AUTHORIZED_DATA_REFERENCE_BOUNDARY_V1_PASS')
