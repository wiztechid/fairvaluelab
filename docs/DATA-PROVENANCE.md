# Data Provenance Standard

## Objective
Make every material valuation input traceable by source, timestamp, transformation, and quality.

## Provenance classes
OFFICIAL — regulator, exchange, issuer filing, or authoritative publication.
THIRD_PARTY — external market/fundamental vendor.
DERIVED — deterministic transformation from identified inputs.
ESTIMATED — model assumption, approximation, or inferred value.

## Minimum metadata
For material fields record where technically feasible:
- source/provider
- source class
- source timestamp or reporting period
- retrieved/generated timestamp
- currency and unit
- transformation
- freshness state
- fallback used
- known limitation

## Freshness
Freshness must be assessed separately for price, financial statements, corporate actions, FX, and disclosures. A fresh market price does not make stale fundamentals fresh.

## Fallback policy
Fallbacks must be explicit and must not silently increase confidence. Provider failure must produce a transparent degraded state.

## Point-in-time rule
Historical evaluation must prefer authoritative filing/publication timestamps. Engine-time fallback is PROVISIONAL and must not be represented as verified PIT evidence.

## Public trust
CekValuasi should expose a reader-friendly source/freshness summary without exposing private implementation details.
