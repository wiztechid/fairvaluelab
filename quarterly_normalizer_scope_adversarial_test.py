import ast, pathlib
src=pathlib.Path('quarterly_normalizer.py').read_text(encoding='utf-8')
tree=ast.parse(src)
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='is_valuation_document')
mod=ast.Module(body=[fn],type_ignores=[]);ast.fix_missing_locations(mod);ns={};exec(compile(mod,'<predicate>','exec'),ns);p=ns['is_valuation_document']
health={'contractVersion':'IDX_COLLECTOR_STATUS_V1','state':'SOURCE_BLOCKED','source':'IDX'}
fixture={'contractVersion':'IDX_AUTHENTIC_FINANCIAL_REPORT_FIXTURE_V1','ticker':'AADI','identityStatus':'UNRESOLVED','pointInTimeAdmission':'PROHIBITED'}
cache=[{'ticker':'AADI','title':'announcement'}]
valuation={'ticker':'AADI.JK','raw':{},'methods':[],'fairValue':{}}
assert p(health) is False
assert p(fixture) is False
assert p(cache) is False
assert p(valuation) is True
# The provenance fixture has a ticker by design; ticker alone must never make a sidecar artifact valuation-eligible.
assert 'raw' not in fixture and 'quarterlyNormalization' not in fixture
print('QUARTERLY_NORMALIZER_SCOPE_GATE_V1_PASS')
