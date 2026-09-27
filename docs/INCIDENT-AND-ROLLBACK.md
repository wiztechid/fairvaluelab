# Incident and Rollback

## Incident classes
DATA: stale/wrong/missing source data.
MODEL: erroneous valuation logic or abnormal distribution shift.
PUBLICATION: invalid artifact published.
SEO: canonical/indexation/sitemap regression.
DEPLOYMENT: site unavailable or broken.
TRUST: misleading financial presentation.

## Immediate response
1. Stop further publication if propagation could continue.
2. Preserve evidence and identify last known-good artifact.
3. Classify affected tickers/pages/time window.
4. Roll back public artifact or mark unavailable/stale.
5. Fix in isolation and rerun relevant gates.
6. Document cause and prevention.

## Financial safety rule
When correctness is uncertain, prefer unavailable/stale/review over a confident but unverified valuation.
