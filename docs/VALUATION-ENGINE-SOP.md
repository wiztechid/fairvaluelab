# Valuation Engine SOP

## Purpose
Govern changes to the valuation engine independently from public presentation.

## Canonical principle
The public product must consume one canonical, validated valuation output. Parallel implementations must never silently publish conflicting fair values.

## Evidence hierarchy
Inputs must be classified as OFFICIAL, THIRD_PARTY, DERIVED, or ESTIMATED. Unknown provenance is a quality penalty.

## Model rules
- Each model must declare family, inputs, assumptions, scenario logic, and independence eligibility.
- Bear/base/bull must be finite, positive where applicable, and ordered.
- Full composite requires at least two independent valuation families.
- One family must not dominate the composite beyond the approved cap.
- Cross-family disagreement is uncertainty, not a reason to hide minority evidence.
- Extreme divergence from market routes to forensic review; market price does not pull fair value toward itself.
- Insufficient evidence must degrade to indicative/reference/unvalued state.

## Change classes
PATCH: implementation correction with no intended model semantics change.
MINOR: assumption/model addition or quality-rule change.
MAJOR: composite philosophy, evidence hierarchy, or canonical output change.

## Required before promotion
1. Explain the economic rationale.
2. Identify affected sectors/tickers.
3. Run engine validation.
4. Run regression benchmark set.
5. Compare distribution shifts.
6. Review extreme changes.
7. Record the model change.
8. Preserve rollback point.

## Forbidden
- Tuning formulas to make output closer to market.
- Suppressing inconvenient valid model disagreement.
- Publishing stale or failed runs as current.
- Using future-known filing data in a historical snapshot without explicit non-PIT labeling.
