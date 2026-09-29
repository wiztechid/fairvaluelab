# P0 QC Checklist

## Canonicality
- [ ] Frontend canonical source is generated ticker JSON.
- [ ] Canonical engine/QC versions match validator.
- [ ] Legacy live API is explicitly non-canonical.
- [ ] No second component recomputes public FV during canonical stamping.

## Provenance
- [ ] THIRD_PARTY market/fundamental source identified.
- [ ] OFFICIAL DES universe source retained.
- [ ] DERIVED valuation lineage includes engine/QC version.
- [ ] ESTIMATED assumptions are identified.
- [ ] observedAt exists.
- [ ] freshness is FRESH or STALE.

## Non-overlap
- [ ] No valuation formula changed.
- [ ] No frontend changed.
- [ ] No SEO/rebrand changed.
- [ ] Existing semantic validator remains authoritative.
- [ ] New validator checks only canonical/provenance contract.

## Publication
- [ ] Semantic validation runs before canonical stamp.
- [ ] Canonical validation runs before data commit.
- [ ] Atomic universe remains enforced.
- [ ] Failure exits non-zero.
