from idx_authorized_data_reference_boundary import normalize
valid={'source':'IDX_DATA_REFERENCE_ENTERPRISE','verification':'AUTHORIZED_IDX_SUBSCRIBER_FEED','recordType':'FINANCIAL_STATEMENT','ticker':'AADI','financialQuarter':'2026Q1','sourceNativeDocumentId':'NATIVE-ID-FROM-AUTHORIZED-SPEC','publishedAt':'2026-04-30T16:51:00+07:00','specReference':'AUTHORIZED-SPEC-REFERENCE','feedRecordIdField':'FIELD-NAME-FROM-SPEC'}
v=normalize(valid);assert v and v['sourceNativeDocumentId']=='NATIVE-ID-FROM-AUTHORIZED-SPEC'
assert v['mappingProvenance']['specReference']=='AUTHORIZED-SPEC-REFERENCE'
for bad in [None,{},dict(valid,source='IDX_PUBLIC_FINANCIAL_REPORT'),dict(valid,verification='OFFICIAL_IDX_PUBLIC'),dict(valid,recordType='OTHER'),dict(valid,ticker=''),dict(valid,financialQuarter=''),dict(valid,sourceNativeDocumentId=''),dict(valid,publishedAt=None),dict(valid,specReference=''),dict(valid,feedRecordIdField='')]:
 assert normalize(bad) is None
# Self-asserted subscriber status alone is insufficient; mapping to an obtained authoritative spec is mandatory.
assert normalize({'source':'IDX_DATA_REFERENCE_ENTERPRISE','verification':'AUTHORIZED_IDX_SUBSCRIBER_FEED','recordType':'FINANCIAL_STATEMENT','ticker':'AADI','financialQuarter':'2026Q1','sourceNativeDocumentId':'CLAIMED','publishedAt':'2026-04-30T16:51:00+07:00'}) is None
# Public filenames/URLs or derived combinations can never substitute for native authorized-feed identity.
assert normalize({'source':'IDX_DATA_REFERENCE_ENTERPRISE','verification':'AUTHORIZED_IDX_SUBSCRIBER_FEED','recordType':'FINANCIAL_STATEMENT','ticker':'AADI','financialQuarter':'2026Q1','publishedAt':'2026-04-30T16:51:00+07:00','filename':'FinancialStatement-2026-I-AADI.pdf','sourceUrl':'https://idx.id/','specReference':'X','feedRecordIdField':'Y'}) is None
print('IDX_AUTHORIZED_DATA_REFERENCE_BOUNDARY_V2_SPEC_PROVENANCE_PASS')
