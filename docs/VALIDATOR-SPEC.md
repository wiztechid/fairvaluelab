# Governance Validator Spec

Validators should be introduced in report-only mode before blocking deployment.

## Required checks
ENGINE: existing validate_engine remains authoritative for current engine semantics.
DATA: provenance/freshness/schema completeness.
SEO: canonical, title, sitemap, robots, indexability consistency.
TRUST: methodology/disclaimer/source visibility.
CONTENT: ticker identity and canonical JSON parity.
DEPLOYMENT: generated artifacts exist and links resolve.

## Severity
P0 BLOCK — risks wrong financial output or corrupted publication.
P1 BLOCK — material trust/indexation failure.
P2 WARN — quality debt that can ship temporarily.
P3 INFO — optimization.

A governance validator must not silently rewrite production files.
