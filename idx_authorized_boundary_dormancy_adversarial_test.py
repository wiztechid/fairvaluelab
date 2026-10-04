from pathlib import Path
boundary='idx_authorized_data_reference_boundary'
# The authorized boundary is intentionally dormant until a real IDX subscriber specification
# is obtained, pinned, hashed, and reviewed. No production VERIFIED path may import it.
for p in [Path('dual_source_filing_provenance.py'),Path('snapshot_backtest.py'),Path('filing_provenance.py')]:
 s=p.read_text(encoding='utf-8')
 assert boundary not in s,p
 assert 'IDX_DATA_REFERENCE_ENTERPRISE' not in s,p
print('IDX_AUTHORIZED_BOUNDARY_DORMANT_NO_VERIFIED_WIRING_PASS')
