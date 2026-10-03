from valuation_document import is_valuation_document
health={'contractVersion':'IDX_COLLECTOR_STATUS_V1','state':'SOURCE_BLOCKED','source':'IDX'}
fixture={'contractVersion':'IDX_AUTHENTIC_FINANCIAL_REPORT_FIXTURE_V1','ticker':'AADI','identityStatus':'UNRESOLVED','pointInTimeAdmission':'PROHIBITED'}
cache=[{'ticker':'AADI','title':'announcement'}]
valuation={'ticker':'AADI.JK','raw':{},'methods':[],'fairValue':{}}
assert is_valuation_document(health) is False
assert is_valuation_document(fixture) is False
assert is_valuation_document(cache) is False
assert is_valuation_document(valuation) is True
assert 'raw' not in fixture and 'quarterlyNormalization' not in fixture
print('QUARTERLY_NORMALIZER_SCOPE_GATE_V2_PASS')
