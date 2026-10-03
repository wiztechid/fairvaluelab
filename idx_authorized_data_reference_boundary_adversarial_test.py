from idx_authorized_data_reference_boundary import normalize
spec={'specReference':'AUTHORIZED-SPEC-REFERENCE','feedRecordIdField':'FIELD-NAME-FROM-SPEC','specSha256':'a'*64}
valid={'source':'IDX_DATA_REFERENCE_ENTERPRISE','verification':'AUTHORIZED_IDX_SUBSCRIBER_FEED','recordType':'FINANCIAL_STATEMENT','ticker':'AADI','financialQuarter':'2026Q1','sourceNativeDocumentId':'NATIVE-ID-FROM-AUTHORIZED-SPEC','publishedAt':'2026-04-30T16:51:00+07:00','specReference':spec['specReference'],'feedRecordIdField':spec['feedRecordIdField']}
v=normalize(valid,spec);assert v and v['sourceNativeDocumentId']=='NATIVE-ID-FROM-AUTHORIZED-SPEC'
assert v['mappingProvenance']['specSha256']=='a'*64
for bad in [None,{},dict(valid,source='IDX_PUBLIC_FINANCIAL_REPORT'),dict(valid,verification='OFFICIAL_IDX_PUBLIC'),dict(valid,recordType='OTHER'),dict(valid,ticker=''),dict(valid,financialQuarter=''),dict(valid,sourceNativeDocumentId=''),dict(valid,publishedAt=None),dict(valid,specReference=''),dict(valid,feedRecordIdField='')]:
 assert normalize(bad,spec) is None
# A record cannot self-assert authorization: a separately pinned specification is mandatory.
assert normalize(valid) is None
assert normalize(valid,{}) is None
assert normalize(valid,dict(spec,specSha256='short')) is None
assert normalize(dict(valid,specReference='OTHER'),spec) is None
assert normalize(dict(valid,feedRecordIdField='OTHER'),spec) is None
# Public filenames/URLs or derived combinations can never substitute for native authorized-feed identity.
derived={'source':'IDX_DATA_REFERENCE_ENTERPRISE','verification':'AUTHORIZED_IDX_SUBSCRIBER_FEED','recordType':'FINANCIAL_STATEMENT','ticker':'AADI','financialQuarter':'2026Q1','publishedAt':'2026-04-30T16:51:00+07:00','filename':'FinancialStatement-2026-I-AADI.pdf','sourceUrl':'https://idx.id/','specReference':spec['specReference'],'feedRecordIdField':spec['feedRecordIdField']}
assert normalize(derived,spec) is None
print('IDX_AUTHORIZED_DATA_REFERENCE_BOUNDARY_V3_PINNED_SPEC_PASS')
