from valuation_document import is_valuation_document
health={'contractVersion':'IDX_COLLECTOR_STATUS_V1','state':'SOURCE_BLOCKED','source':'IDX'}
disclosures=[{'ticker':'AADI','title':'financial statement'}]
fixture={'contractVersion':'IDX_AUTHENTIC_FINANCIAL_REPORT_FIXTURE_V1','ticker':'AADI','identityStatus':'PUBLIC_ROUTE_IDENTITY_BLOCKED','pointInTimeAdmission':'PROHIBITED'}
ticker_only={'ticker':'AADI','publishedAt':'2026-04-30T16:51:00+07:00'}
valuation={'ticker':'AADI.JK','raw':{},'methods':[],'fairValue':{}}
for x in (health,disclosures,fixture,ticker_only): assert is_valuation_document(x) is False
assert is_valuation_document(valuation) is True
# Guard against regression to filename blacklists: every root-data writer must import and use canonical scope.
from pathlib import Path
writers=['quarterly_normalizer.py','adaptive_pe.py','augment_models.py','family_consensus.py','indicative_fv.py','sector_models.py','sector_waterfall.py','postprocess_qc.py']
for p in writers:
 s=Path(p).read_text(encoding='utf-8')
 assert 'from valuation_document import is_valuation_document' in s,p
 assert 'is_valuation_document(' in s,p
# Discovery guard: fail closed if a new top-level Python root-data glob writer appears without canonical scope.
# This supplements the explicit writer inventory so future pipelines cannot silently escape it.
for p in Path('.').glob('*.py'):
 s=p.read_text(encoding='utf-8')
 root_scan=("DATA.glob('*.json')" in s or "glob.glob(os.path.join(OUT,'*.json'))" in s or "glob('data/*.json')" in s or 'glob("data/*.json")' in s)
 mutates=('json.dump(' in s or '.write_text(' in s)
 if root_scan and mutates:
  assert 'from valuation_document import is_valuation_document' in s,p
  assert 'is_valuation_document(' in s,p
print('VALUATION_ARTIFACT_ISOLATION_V3_DISCOVERY_GUARD_PASS')
