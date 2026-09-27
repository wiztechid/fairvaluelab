# Versioning and Migration

## Independent versions
Maintain distinct versions for engine semantics, QC policy, data schema, public frontend, and governance.

## Migration rule
A brand/frontend migration must not implicitly change valuation semantics. An engine migration must not silently rewrite historical snapshots.

## Compatibility
Generated public artifacts should declare enough version metadata to diagnose mixed-version states.

## Rollback
Every promoted migration must have a known prior state and a practical rollback path.
