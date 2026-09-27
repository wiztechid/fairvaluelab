# Model Risk Register

## MR-01 Cross-family disagreement
Risk: independent economic models disagree materially.
Current control: spread >3.0x triggers CROSS_FAMILY_CONFLICT, widens range, reduces confidence, routes to REVIEW.

## MR-02 Market divergence
Risk: model result is extreme relative to current price because of bad inputs or genuine dislocation.
Current control: market is a forensic trigger, not valuation anchor; <0.25x or >3.0x routes to REVIEW.

## MR-03 Family pseudo-diversification
Risk: many methods from one family create false confidence.
Current control: family consensus and minimum independent-family requirement.

## MR-04 Sector mismatch
Risk: generic models are inappropriate for financial/property/asset-heavy businesses.
Current control: sector-aware waterfall and method eligibility. Requires ongoing forensic sampling.

## MR-05 Multiple-band assumption risk
Risk: sector EV/EBIT or revenue bands are judgmental and can become stale.
Control required: version, rationale, regression impact, periodic review.

## MR-06 Growth/terminal sensitivity
Risk: DCF/earnings values react strongly to growth and required-return assumptions.
Control: scenario ranges, growth guards, confidence, cross-family comparison.

## MR-07 Historical reconstruction / look-ahead
Risk: historical multiples or backtests use information not actually known at the date.
Current control: PIT quality distinction; engineAsOfFallback remains PROVISIONAL.

## MR-08 Corporate actions / shares
Risk: splits, rights issues, treasury shares, or vendor share-count errors distort per-share value.
Control required: anomaly checks and forensic review on extreme cases.

## MR-09 Currency normalization
Risk: financial statement currency mismatch.
Current forensic control checks fxNormalized for extreme cases; broader provenance/freshness hardening remains P0.

## MR-10 Vendor/API failure
Risk: third-party rate limits/missing statements reduce model coverage.
Control: explicit degraded status/fallback; never fabricate missing evidence.
